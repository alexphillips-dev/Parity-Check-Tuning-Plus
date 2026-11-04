const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');

async function main() {
  const root = path.resolve(__dirname, '..');
  const dir = path.join(root, 'build/ui-cases');
  const cases = JSON.parse(fs.readFileSync(path.join(dir, 'cases.json'), 'utf8'));
  const jquery = fs.readFileSync(require.resolve('jquery/dist/jquery.min.js'), 'utf8');
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({viewport:{width:1280,height:900}});
  const failures = [];
  page.on('pageerror', error => failures.push(error.message));
  let checked = 0;
  try {
    for (const item of cases) {
      failures.length = 0;
      const html = fs.readFileSync(path.join(dir,item.file),'utf8').replace('<head>', '<head><script>'+jquery+'</script><script>window.swal=(options)=>{window.pctLastDialog=options;};window.done=()=>{};window.caPluginUpdateCheck=()=>{};window.openChanges=()=>{};window.openBox=()=>{};</script>');
      await page.setContent(html,{waitUntil:'domcontentloaded'});
      await page.evaluate(() => new Promise(resolve => $(resolve)));
      assert.deepEqual(failures, [], `${item.locale}/${item.kind}: initial JS errors`);
      if (item.kind==='settings' || item.kind==='plugins') {
        assert.equal(await page.locator('#parityTuningPlusPage').getAttribute('dir'),item.rtl?'rtl':'ltr');
        assert.ok((await page.locator('body').innerText()).includes(item.expected['Increment frequency']));
        assert.ok(await page.locator('[data-pct-help]').count() >= 20);
        await page.locator('select[name="parityTuningPlusLogging"]').selectOption('1');
        assert.equal(await page.evaluate(()=>pctLastDialog.title),item.expected['Do you really want Debug logging mode?']);
        assert.equal(await page.locator('select[name="parityTuningPlusBackground"]').inputValue(),'0');
        assert.equal(await page.locator('[name="parityTuningPlusDocker"],[name="parityTuningPlusContainers"]').count(),0,'Retired Docker controls must not be rendered');
        assert.equal(await page.locator('[data-pct-help="parity_tuning_plus_docker_plug"],[data-pct-help="parity_tuning_plus_dockerlist_plug"]').count(),0,'Retired Docker help must not be rendered');
        assert.equal(await page.evaluate(()=>typeof DockerListSet),'undefined');
        if (item.locale==='en_US' && item.kind==='settings') {
          const historyCalls=await page.evaluate(()=>{
            const calls=[];
            window.openChanges=(...args)=>calls.push(['changes',...args]);
            parityTuningPlusHistory();
            delete window.openChanges;
            window.openBox=(...args)=>calls.push(['box',...args]);
            parityTuningPlusHistory();
            return calls;
          });
          assert.equal(historyCalls[0][0],'changes');
          assert.equal(historyCalls[0][1],'parity_history');
          assert.equal(historyCalls[1][0],'box');
          assert.equal(historyCalls[1][1],'/webGui/include/ParityHistory.php');
          const submissions=await page.evaluate(()=>{
            const form=document.getElementById('parityTuningPlusPage');
            const attempts=[];
            const capture=event=>{
              attempts.push({blocked:event.defaultPrevented,command:form.elements['#arg[1]'].value});
              // Observe actual browser submit ordering without posting to a host.
              event.preventDefault();
            };
            form.addEventListener('submit',capture);
            form.parityTuningPlusFrequency.value='1';
            form.parityTuningPlusResumeCustom.value='60 * * * *';
            form.querySelector('#Defaults').click();
            form.elements['#apply'].disabled=false;
            form.elements['#apply'].click();
            form.parityTuningPlusResumeCustom.value='0 1 * * *';
            form.parityTuningPlusPauseCustom.value='0 2 * * *';
            checkCustomOptions(form);
            // Canceling a Defaults submission must not turn the next Apply into a reset.
            form.querySelector('#Defaults').click();
            form.elements['#apply'].click();
            form.removeEventListener('submit',capture);
            return attempts;
          });
          assert.deepEqual(submissions,[
            {blocked:false,command:'defaults'},
            {blocked:true,command:'config'},
            {blocked:false,command:'defaults'},
            {blocked:false,command:'config'},
          ],'Defaults must recover invalid settings and canceled resets must not change Apply');
        }
        await page.evaluate(()=>{form=document.getElementById('parityTuningPlusPage');form.parityTuningPlusFrequency.value='1';form.parityTuningPlusPauseCustom.value='0 1 * * *';form.parityTuningPlusResumeCustom.value='0 1 * * *';window.pctCustomResult=checkCustomOptions(form);});
        assert.equal(await page.evaluate(()=>pctCustomResult),false,`${item.locale}: identical custom schedules must block Apply`);
        assert.equal(await page.locator('#native-scheduler input').isDisabled(),true,'Plugin validation must preserve native Scheduler controls');
        await page.evaluate(()=>{
          const form=document.getElementById('parityTuningPlusPage');
          for (const bad of ['60 * * * *','*/0 * * * *','* * * * *\n* * * * * echo bad']) {
            form.parityTuningPlusResumeCustom.value=bad;
            if (checkCustomOptions(form)!==false) throw Error('Invalid cron accepted: '+bad);
          }
          if (normalizedCron('*/5 2-5 * JAN mon-fri')!=='*/5 2-5 * 1 1-5') throw Error('Valid cron rejected');
          form.parityTuningPlusFrequency.value='0';
          form.parityTuningPlusResumeHour.value=form.parityTuningPlusPauseHour.value='1';
          form.parityTuningPlusResumeMinute.value=form.parityTuningPlusPauseMinute.value='0';
          if (checkCustomOptions(form)!==false) throw Error('Identical daily times accepted');
          form.parityTuningPlusFrequency.value='2';
          form.parityTuningPlusResumeDay.value='0';form.parityTuningPlusPauseDay.value='1';
          if (checkCustomOptions(form)!==true || form.elements['#apply'].disabled) throw Error('Valid weekly window blocked');
        });
        assert.equal(await page.locator('#native-scheduler input').isDisabled(),true);
      } else if (item.kind==='assistant') {
        assert.equal(await page.locator('form').getAttribute('dir'),item.rtl?'rtl':'ltr');
        assert.equal(await page.locator('[data-pct-help]').count(),7);
        assert.equal(await page.locator('select[name="parityProblemPlusType"]').inputValue(),'sector');
        assert.equal(await page.locator('#Apply').isEnabled(),true);
        await page.locator('select[name="parityProblemPlusType"]').selectOption('percent');
        assert.equal(await page.locator('#parityProblemPlusPercentStart').isVisible(),true);
        assert.equal(await page.locator('#parityProblemPlusSectorStart').isVisible(),false);
        await page.locator('[name="parityProblemPlusStartPercent"]').fill('10');
        await page.locator('[name="parityProblemPlusEndPercent"]').fill('20');
        await page.locator('[name="parityProblemPlusEndPercent"]').dispatchEvent('change');
        assert.equal(await page.locator('#Apply').isEnabled(),true);
        await page.locator('[name="parityProblemPlusEndPercent"]').fill('101');
        assert.equal(await page.evaluate(()=>checkStartEnd(document.getElementById('parityProblemPlusPage'),true)),false);
        assert.equal(await page.locator('#Apply').isDisabled(),true);
        if (item.locale==='en_US') {
          const activeHtml=html.replace('var pctProblemActive = false;', 'var pctProblemActive = true;')
            .replace('<head>','<head><script>window.pctRefreshTimers=[];window.pctNativeTimeout=window.setTimeout.bind(window);window.setTimeout=(callback,delay,...args)=>{if(delay===30000){window.pctRefreshTimers.push({name:callback.name,delay});return 0;}return window.pctNativeTimeout(callback,delay,...args);};</script>');
          await page.setContent(activeHtml,{waitUntil:'domcontentloaded'});
          await page.evaluate(() => new Promise(resolve => $(resolve)));
          assert.equal(await page.evaluate(()=>pctProblemActive),true);
          for (const name of ['Type','StartSector','StartPercent','EndSector','EndPercent','Correct']) {
            assert.equal(await page.locator(`[name="parityProblemPlus${name}"]`).isDisabled(),true,'Active assistant must disable '+name);
          }
          assert.equal(await page.locator('#Apply').isDisabled(),true,'Active assistant cannot start another check');
          assert.deepEqual(await page.evaluate(()=>pctRefreshTimers),[{name:'refreshPage',delay:30000}]);
          const popupCalls=await page.evaluate(()=>{
            const calls=[];
            myWin=null;
            positionPopup();
            myWin={moveBy:(left,top)=>calls.push(['move',left,top]),focus:()=>calls.push(['focus'])};
            positionPopup();
            return calls;
          });
          assert.equal(popupCalls[0][0],'move');
          assert.deepEqual(popupCalls[1],['focus']);
          await page.evaluate(()=>{window.setTimeout=window.pctNativeTimeout;delete window.pctNativeTimeout;});
        }
      } else if (item.kind==='popup') {
        assert.equal(await page.locator('html').getAttribute('dir'),item.rtl?'rtl':'ltr');
        assert.ok((await page.locator('body').innerText()).includes('<script>bad()</script>'));
        assert.equal(await page.evaluate(()=>typeof bad),'undefined');
      } else if (item.kind==='history') {
        const body=await page.locator('body').innerText();
        assert.ok(body.includes(item.expected.Action));
        assert.ok(body.includes(item.expected.Scheduled));
        assert.ok(body.includes(item.expected['Non-Correcting']));
      }
      assert.deepEqual(failures, [], `${item.locale}/${item.kind}: interaction JS errors`);
      if (['settings','assistant'].includes(item.kind)) {
        await page.setViewportSize({width:390,height:844});
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= window.innerWidth+2),`${item.locale}/${item.kind}: mobile horizontal overflow`);
        await page.setViewportSize({width:1280,height:900});
      }
      checked++;
    }
    console.log(`PASS: ${checked} real-browser page/route cases, dialogs, help, controls, validation, aliases, RTL, and mobile layout.`);
  } finally {await browser.close();}
}
main().catch(error=>{console.error(error);process.exitCode=1;});
