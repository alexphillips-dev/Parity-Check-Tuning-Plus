const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');

// Exercise the actual host grid, rather than the simplified translation fixture CSS.
async function inspect(page, desktop) {
  return page.locator('#parityTuningPlusPage,#parityProblemPlusPage').evaluate((form, desktop) => {
    const errors = [];
    const visible = el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
    let column;
    for (const dl of form.querySelectorAll('dl')) {
      const children = [...dl.children];
      if (children.some((el, i) => el.tagName !== (i % 2 ? 'DD' : 'DT')) || children.length % 2) {
        errors.push('Unpaired setting label/control: ' + dl.textContent.trim().slice(0, 70));
      }
      if (dl.querySelector('[data-pct-help]')) errors.push('Help was parsed into a setting row');
      for (const dd of dl.querySelectorAll(':scope > dd')) {
        const control = [...dd.querySelectorAll('input:not([type="hidden"]),select')].find(visible);
        if (!control || !visible(dd)) continue;
        const dt = dd.previousElementSibling;
        if (!dt || dt.tagName !== 'DT') continue;
        const field = dd.getBoundingClientRect();
        const label = dt.getBoundingClientRect();
        if (desktop) {
          column ??= field.left;
          if (Math.abs(field.left - column) > 1.5) errors.push(control.name + ': inconsistent control column');
          if (Math.abs(field.top - label.top) > Math.max(16, label.height)) errors.push(control.name + ': label/control on different rows');
        } else if (field.top + 1 < label.bottom) {
          errors.push(control.name + ': mobile label/control overlap');
        }
      }
    }
    if (document.documentElement.scrollWidth > innerWidth + 2) errors.push('Horizontal overflow');
    return errors;
  }, desktop);
}

async function main() {
  const root = path.resolve(__dirname, '..');
  const dir = path.join(root, 'build/ui-cases');
  const cases = JSON.parse(fs.readFileSync(path.join(dir, 'cases.json'), 'utf8'))
    .filter(item => ['settings', 'plugins', 'assistant'].includes(item.kind));
  const jquery = fs.readFileSync(require.resolve('jquery/dist/jquery.min.js'), 'utf8');
  const css = fs.readFileSync(path.join(__dirname, 'fixtures/unraid/default-base.css'), 'utf8');
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage();
  let checked = 0;
  try {
    for (const item of cases) {
      const html = fs.readFileSync(path.join(dir, item.file), 'utf8').replace('<head>',
        '<head><script>' + jquery + '</script><script>window.swal=()=>{};window.done=()=>{};window.caPluginUpdateCheck=()=>{};window.openChanges=()=>{};window.openBox=()=>{};</script>');
      await page.setContent(html, {waitUntil:'domcontentloaded'});
      await page.evaluate(() => new Promise(resolve => $(resolve)));
      await page.locator('head > style').first().evaluate(el => el.remove());
      await page.addStyleTag({content:css});
      if (item.kind === 'assistant') {
        for (const width of [1920,1280,390]) {
          await page.setViewportSize({width,height:900});
          assert.deepEqual(await inspect(page,width>768),[],`${item.locale}/assistant/${width}`);
          checked++;
        }
        continue;
      }
      assert.equal(await page.locator('[name="parityTuningPlusDocker"],[name="parityTuningPlusContainers"]').count(), 0, 'Retired Docker controls must not be rendered');
      for (const width of [1920, 1280, 390]) {
        await page.setViewportSize({width, height:900});
        for (const frequency of ['0', '2', '1']) {
          await page.evaluate(frequency => {
            const form = document.getElementById('parityTuningPlusPage');
            form.parityTuningPlusScheduled.value = '1';
            form.parityTuningPlusFrequency.value = frequency;
            form.parityTuningPlusMover.value = '1';
            form.parityTuningPlusBackup.value = '1';
            form.parityTuningPlusHeat.value = '1';
            form.parityTuningPlusHeatShutdown.value = '1';
            form.parityTuningPlusLogging.value = '2';
            presetParityTuningPlus(form);
          }, frequency);
          assert.deepEqual(await inspect(page, width > 768), [], `${item.locale}/${item.kind}/${width}/${frequency}`);
          checked++;
        }
      }
      assert.equal(await page.locator('#native-scheduler input').isDisabled(), true, 'Native Scheduler remains untouched');
      await page.evaluate(() => {
        const form = document.getElementById('parityTuningPlusPage');
        for (const field of ['Scheduled','Manual','Automatic','Recon','Clear','Mover','Backup','Heat','HeatShutdown']) form['parityTuningPlus' + field].value = '0';
        presetParityTuningPlus(form);
      });
      for (const id of ['IncrementDisplay','BackgroundDisplay','HeatDisplay','CriticalDisplay']) {
        assert.equal(await page.locator('#parityTuningPlus' + id).isVisible(), false, 'Disabled conditional group: ' + id);
      }
      assert.deepEqual(await inspect(page, false), [], 'Disabled optional groups retain layout');
      if (item.locale === 'en_US' && item.kind === 'settings') {
        await page.setViewportSize({width:1920, height:900});
        await page.evaluate(() => {
          const form = document.getElementById('parityTuningPlusPage');
          form.parityTuningPlusScheduled.value = '1';
          presetParityTuningPlus(form);
        });
        await page.addStyleTag({content:'.inline_help{display:block}'});
        assert.deepEqual(await inspect(page, true), [], 'Expanded help must not disrupt setting columns');
        // Recreate the original extra help DT and require the same checks to reject it.
        await page.evaluate(() => {
          const dd = document.querySelector('[name="parityTuningPlusNotify"]').closest('dd');
          const extra = document.createElement('dt');
          extra.innerHTML = '<div data-pct-help="negative-control"><blockquote class="inline_help">Help</blockquote></div>';
          dd.previousElementSibling.before(extra);
        });
        assert.ok((await inspect(page, true)).length > 0, 'Negative control must detect the original displaced row');
      }
    }
    console.log(`PASS: ${checked} native-grid layouts across Scheduler/Plugins/Assistant, all locales, daily/weekly/custom, conditional fields, desktop/mobile, expanded help and malformed-row negative control.`);
  } finally {await browser.close();}
}
main().catch(error => {console.error(error);process.exitCode = 1;});
