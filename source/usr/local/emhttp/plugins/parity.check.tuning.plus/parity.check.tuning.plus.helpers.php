<?PHP
/*
 * Helper routines used by the parity.check.tuning.plus plugin
 *
 * Copyright 2019-2026, Dave Walker (itimpi).
 * Modified 2026-11-04 by alexphillips-dev for Parity Check Tuning Plus.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License version 2,
 * as published by the Free Software Foundation.
 *
 * Limetech is given explicit permission to use this code in any way they like.
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * Useful site for checking php sytax: https://phphub.net/linter/
 */

// useful for testing outside Gui
$docroot = $docroot ?? $_SERVER['DOCUMENT_ROOT'] ?: '/usr/local/emhttp';

require_once __DIR__ . "/parity.check.tuning.plus.assistant.php";
require_once "$docroot/webGui/include/Helpers.php";
require_once "$docroot/plugins/dynamix/include/Wrappers.php";

// Set up some useful constants used in multiple files
define('EMHTTP_DIR' ,               '/usr/local/emhttp');
define('CONFIG_DIR' ,               '/boot/config');
define('PLUGINS_DIR' ,              CONFIG_DIR . '/plugins');
define('PARITY_TUNING_PLUS_PLUGIN',      'parity.check.tuning.plus');
$plugin = PARITY_TUNING_PLUS_PLUGIN;		// required by security guidelines
define('PARITY_TUNING_PLUS_EMHTTP_DIR',  EMHTTP_DIR . '/plugins/' . $plugin);
define('PARITY_TUNING_PLUS_VERSION_FILE',PARITY_TUNING_PLUS_EMHTTP_DIR . "/$plugin.version");
define('PARITY_TUNING_PLUS_PHP_FILE',    PARITY_TUNING_PLUS_EMHTTP_DIR . '/' . PARITY_TUNING_PLUS_PLUGIN . '.php');  
define('PARITY_TUNING_PLUS_BOOT_DIR',    PLUGINS_DIR . '/' . PARITY_TUNING_PLUS_PLUGIN);
define('PARITY_TUNING_PLUS_FILE_PREFIX', PARITY_TUNING_PLUS_BOOT_DIR . '/' . PARITY_TUNING_PLUS_PLUGIN . '.');

define('PARITY_TUNING_PLUS_DEFAULTS_FILE', PARITY_TUNING_PLUS_EMHTTP_DIR . '/default.cfg');
define('PARITY_TUNING_PLUS_CFG_FILE',    PARITY_TUNING_PLUS_FILE_PREFIX . 'cfg');
define('PARITY_TUNING_PLUS_LOG_FILE',    PARITY_TUNING_PLUS_FILE_PREFIX . 'log');
define('PARITY_TUNING_PLUS_PARTIAL_FILE',PARITY_TUNING_PLUS_FILE_PREFIX . 'partial');  // Create when partial check in progress (contains end sector value)
define('EMHTTP_VAR_DIR' ,           '/var/local/emhttp/');
define('PARITY_TUNING_PLUS_EMHTTP_VAR_FILE',  EMHTTP_VAR_DIR . 'var.ini');
define('PARITY_TUNING_PLUS_EMHTTP_DISKS_FILE',EMHTTP_VAR_DIR . 'disks.ini');
define('PARITY_TUNING_PLUS_CABACKUP2_FILE',   PLUGINS_DIR . '/ca.backup2.plg'); 
define('PARITY_TUNING_PLUS_APPBACKUP_FILE',   PLUGINS_DIR . '/appdata.backup.plg'); 
define('PARITY_TUNING_PLUS_RESTART_FILE',   PARITY_TUNING_PLUS_FILE_PREFIX . 'restart');  // Created if array stopped with array operation active to hold restart info
define('PARITY_TUNING_PLUS_SCHEDULED_FILE', PARITY_TUNING_PLUS_FILE_PREFIX . 'scheduled');// Created when we detect an array operation started by cron
define('PARITY_TUNING_PLUS_MANUAL_FILE',    PARITY_TUNING_PLUS_FILE_PREFIX . 'manual');   // Created when we detect an array operation started manually
define('PARITY_TUNING_PLUS_AUTOMATIC_FILE', PARITY_TUNING_PLUS_FILE_PREFIX . 'automatic');// Created when we detect an array operation started automatically after unclean shutdown
define('PARITY_TUNING_PLUS_DATE_FORMAT', 'Y M d H:i:s');
// Logging modes supported
define('PARITY_TUNING_PLUS_LOGGING_BASIC' , '0');
define('PARITY_TUNING_PLUS_LOGGING_DEBUG' , '1');
define('PARITY_TUNING_PLUS_LOGGING_TESTING' ,'2');
// Targets for testing mode
define('PARITY_TUNING_PLUS_LOGGING_SYSLOG' ,'0');
define('PARITY_TUNING_PLUS_LOGGING_BOTH' ,'1');
define('PARITY_TUNING_PLUS_LOGGING_FLASH' ,'2');

// Configuration information
// (automatically merge defauls with current settings)
$parityTuningPlusCfg = parse_plugin_cfg($plugin);
// Hand-edited or damaged offsets must not stop the monitor with PHP arithmetic errors.
$offsetDefaults = ['parityTuningPlusHeatHigh'=>'3','parityTuningPlusHeatLow'=>'8',
                   'parityTuningPlusHeatCritical'=>'2','parityTuningPlusHeatTooLong'=>'30'];
foreach ($offsetDefaults as $key => $fallback) {
    $value = $parityTuningPlusCfg[$key] ?? null;
    if (!is_numeric($value) || !is_finite((float)$value) || $value < 0 || $value > PHP_INT_MAX) $parityTuningPlusCfg[$key] = $fallback;
}

// Only want this line active while debugging to help clear up all PHP errors.
if ($parityTuningPlusCfg['parityTuningPlusLogging'] > 1) {
	error_reporting(E_ERROR | E_WARNING | E_PARSE | E_NOTICE);
}

$dynamixCfg = @parse_ini_file('/boot/config/plugins/dynamix/dynamix.cfg', true);
$parityTuningPlusTempUnit      = @$dynamixCfg['display']['unit'] ?? 'C'; // Use Celsius if not set
	
// Multi-Language support code enabler for non-GUI usage

$plugin = PARITY_TUNING_PLUS_PLUGIN;
if (!array_key_exists('locale', $_SESSION ?? [])) {
    $_SESSION['locale'] = $dynamixCfg['display']['locale'] ?? '';
}
$login_locale = $_SESSION['locale'];
require_once __DIR__ . '/parity.check.tuning.plus.i18n.php';
if (file_exists(EMHTTP_DIR . '/webGui/include/Translations.php')) {
    require_once "$docroot/webGui/include/Translations.php";
    parse_plugin('paritychecktuningplus');
} else {
    require_once __DIR__ . '/Legacy.php';
}

// Unraid version dependencies

$parityTuningPlusVersion = pctT('Version') . ': ' . pctVersion(PARITY_TUNING_PLUS_VERSION_FILE);
// Handle Unraid version dependencies
$parityTuningPlusUnraidVersion = parse_ini_file("/etc/unraid-version")['version'];
$parityTuningPlusStartStop = version_compare($parityTuningPlusUnraidVersion,'6.10.3','>=');
$parityTuningPlusSizeInHistory = version_compare($parityTuningPlusUnraidVersion,'6.11.0','>=');

// Determine if parity drive installed

$disks = is_file(PARITY_TUNING_PLUS_EMHTTP_DISKS_FILE) ? parse_ini_file(PARITY_TUNING_PLUS_EMHTTP_DISKS_FILE, true) : [];
$parityTuningPlusParity1 = isset($disks['parity']['status']) && !startsWith($disks['parity']['status'], 'DISK_NP');
$parityTuningPlusParity2 = isset($disks['parity2']['status']) && !startsWith($disks['parity2']['status'], 'DISK_NP');
$parityTuningPlusNoParity = !($parityTuningPlusParity1 || $parityTuningPlusParity2);

// Plugin cannot handle increments if standard Unbraid setting set to cumulative
$parityTuningPlusCumulative = $dynamixCfg['parity']['cumulative'] ?? '0';  // Assume 0 if not set
if ($parityTuningPlusCumulative) {
	parityTuningPlusLoggerTesting ("Cumulative option set at Unraid level");
}

// Decide if backup plugin installed

$parityTuningPlusNoBackup = !(file_exists(PARITY_TUNING_PLUS_CABACKUP2_FILE)||file_exists(PARITY_TUNING_PLUS_APPBACKUP_FILE));
if ($parityTuningPlusNoBackup) {
	parityTuningPlusLoggerTesting ("No appdata backupo plugin installed");
}

// load some state information into global variables for directly referencing elsewhere.
// (written as a function to facilitate reloads)
function loadVars($delay = 0) {
    global $var, $parityTuningPlusStateValid, $parityTuningPlusDescription;
    global $parityTuningPlusServer, $parityTuningPlusStarted, $parityTuningPlusPos, $parityTuningPlusSize;
    global $parityTuningPlusAction, $parityTuningPlusActive, $parityTuningPlusPaused;
    global $parityTuningPlusCorrecting, $parityTuningPlusErrors;
    if ($delay > 0) sleep($delay);
    $read = @parse_ini_file(PARITY_TUNING_PLUS_EMHTTP_VAR_FILE, false, INI_SCANNER_RAW);
    $defaults = ['NAME'=>'', 'mdState'=>'STOPPED', 'mdResyncPos'=>'0', 'mdResyncSize'=>'0',
                 'mdResyncAction'=>'', 'mdResync'=>'0', 'mdResyncCorr'=>'0',
                 'sbSyncErrs'=>'0', 'sbSynced'=>'0', 'sbSynced2'=>'0', 'sbSyncExit'=>'0'];
    $parityTuningPlusStateValid = is_array($read) && !array_diff_key($defaults, $read);
    $var = array_replace($defaults, is_array($read) ? $read : []);
    foreach (array_keys($defaults) as $key) {
        if (!is_scalar($var[$key])) { $var[$key] = $defaults[$key]; $parityTuningPlusStateValid = false; }
    }
    foreach (['mdResyncPos','mdResyncSize','mdResync','mdResyncCorr','sbSyncErrs','sbSynced','sbSynced2','sbSyncExit'] as $key) {
        $value = (string)$var[$key];
        $valid = $key === 'sbSyncExit' ? preg_match('/^-?[0-9]+$/D', $value) : ctype_digit($value);
        $canonical = ltrim($value, '0');
        if (substr($value, 0, 1) === '-') $canonical = '-'.ltrim(substr($value, 1), '0');
        if (!$valid || (string)(int)$value !== ($canonical === '' || $canonical === '-' ? '0' : $canonical)) {
            $var[$key] = $defaults[$key]; $parityTuningPlusStateValid = false;
        }
    }
    $parityTuningPlusServer = strtoupper((string)$var['NAME']);
    $parityTuningPlusStarted = $parityTuningPlusStateValid && $var['mdState'] === 'STARTED' ? 1 : 0;
    $parityTuningPlusPos = (int)$var['mdResyncPos'];
    $parityTuningPlusSize = (int)$var['mdResyncSize'];
    $parityTuningPlusAction = (string)$var['mdResyncAction'];
    $parityTuningPlusActive = $parityTuningPlusStarted && $parityTuningPlusPos > 0 ? 1 : 0;
    $parityTuningPlusPaused = $parityTuningPlusActive && (int)$var['mdResync'] === 0 ? 1 : 0;
    $parityTuningPlusCorrecting = (int)$var['mdResyncCorr'];
    $parityTuningPlusErrors = (int)$var['sbSyncErrs'];
    $trigger = '';
    foreach (['SCHEDULED'=>PARITY_TUNING_PLUS_SCHEDULED_FILE,'AUTOMATIC'=>PARITY_TUNING_PLUS_AUTOMATIC_FILE,'MANUAL'=>PARITY_TUNING_PLUS_MANUAL_FILE] as $type=>$path) {
        if (is_file($path)) { $trigger = $type; break; }
    }
    if (defined('PARITY_TUNING_PLUS_PARTIAL_FILE') && is_file(PARITY_TUNING_PLUS_PARTIAL_FILE)) $trigger = 'PARTIAL';
    $parityTuningPlusDescription = $parityTuningPlusActive
        ? actionDescription($parityTuningPlusAction, $parityTuningPlusCorrecting, $trigger, true)
        : pctT('No array operation in progress');
}

loadVars();


// Establish fallback trigger markers for an operation detected during initial loading.
if ($parityTuningPlusActive) {
	$parityTuningPlusDescription = actionDescription($parityTuningPlusAction, $parityTuningPlusCorrecting);
	parityTuningPlusLoggerDebug($parityTuningPlusDescription.' '.($parityTuningPlusPaused ? pctT('paused') : pctT('running')));
}

// ----------------------- Support/Utility  Functions ----------------------------

// Tidy up the name of a marker file for logging purposes
//       ~~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusMarkerTidy($name) {
//       ~~~~~~~~~~~~~~~~~~~~~~
	if (startsWith($name, PARITY_TUNING_PLUS_FILE_PREFIX)) {
		$name = str_replace(PARITY_TUNING_PLUS_FILE_PREFIX, '', $name) . ' marker file';
	}
	return $name;
}

// Set marker file to remember some state information we have detected
// (put date/time into file so can tie it back to syslog if needed)
//       ~~~~~~~~~~~~~~~~
function pctSetOperationTrigger($trigger) {
    $markers = ['SCHEDULED'=>PARITY_TUNING_PLUS_SCHEDULED_FILE, 'MANUAL'=>PARITY_TUNING_PLUS_MANUAL_FILE,
                'AUTOMATIC'=>PARITY_TUNING_PLUS_AUTOMATIC_FILE, 'PARTIAL'=>null];
    if (!array_key_exists($trigger, $markers)) return false;
    foreach ($markers as $type => $path) if ($path !== null && $type !== $trigger) parityTuningPlusDeleteFile($path);
    if ($markers[$trigger] !== null) createMarkerFile($markers[$trigger]);
    return true;
}

/** Return a normalized five-field cron expression, or false without accepting commands. */
function pctCronExpression($expression) {
    if (!is_string($expression) || preg_match('/[\r\n\x00]/', $expression)) return false;
    $fields = preg_split('/[ \t]+/', trim($expression));
    if (count($fields) !== 5) return false;
    $bounds = [[0,59],[0,23],[1,31],[1,12],[0,7]];
    foreach ($fields as $index => &$field) {
        $field = strtolower($field);
        $names = $index === 3 ? ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']
               : ($index === 4 ? ['sun','mon','tue','wed','thu','fri','sat'] : []);
        foreach ($names as $number => $name) $field = str_replace($name, (string)($number + ($index === 3 ? 1 : 0)), $field);
        foreach (explode(',', $field) as $part) {
            if (!preg_match('/^(\*|[0-9]+(?:-[0-9]+)?)(?:\/([0-9]+))?$/D', $part, $match)) return false;
            if (isset($match[2]) && ((int)$match[2] < 1 || (int)$match[2] > $bounds[$index][1])) return false;
            if (isset($match[2]) && $match[1] !== '*' && strpos($match[1], '-') === false) return false;
            if ($match[1] === '*') continue;
            $range = explode('-', $match[1]);
            foreach ($range as $value) if ((float)$value < $bounds[$index][0] || (float)$value > $bounds[$index][1]) return false;
            if (count($range) === 2 && (int)$range[0] > (int)$range[1]) return false;
        }
    }
    unset($field);
    return implode(' ', $fields);
}

function pctRestartRange($state) {
    if (!is_array($state)) return false;
    $numbers = [];
    foreach (['mdResyncPos', 'mdResyncSize', 'mdResync', 'mdResyncCorr'] as $key) {
        $value = (string)($state[$key] ?? '');
        $canonical = ltrim($value, '0');
        if (!ctype_digit($value) || (string)(int)$value !== ($canonical === '' ? '0' : $canonical)) return false;
        $numbers[$key] = (int)$value;
    }
    if ($numbers['mdResyncPos'] <= 0 || $numbers['mdResyncPos'] >= $numbers['mdResyncSize']
        || $numbers['mdResyncPos'] > intdiv(PHP_INT_MAX, 2) || $numbers['mdResyncCorr'] > 1) return false;
    $action = trim((string)($state['mdResyncAction'] ?? ''));
    if (!preg_match('/^(check|recon|clear)(?: [A-Za-z0-9]+)*$/D', $action)) return false;
    $sector = $numbers['mdResyncPos'] * 2;
    return ['sector'=>$sector - $sector % 8, 'correct'=>$numbers['mdResyncCorr'], 'action'=>$action];
}

function createMarkerFile ($filename) {
//       ~~~~~~~~~~~~~~~~
	if (!file_exists($filename)) {
        file_put_contents($filename, date(PARITY_TUNING_PLUS_DATE_FORMAT), LOCK_EX);
		parityTuningPlusLoggerTesting(parityTuningPlusMarkerTidy($filename) ." created"); 
	}
}

// Remove a file and if TESTING logging active then log it has happened
// For marker files sanitize the name to a friendlier form.
// Return true if file was deleted, and false if did not exist.

//       ~~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusDeleteFile($name) {
//       ~~~~~~~~~~~~~~~~~~~~~~
 	if (file_exists($name)) {
		@unlink($name);
		parityTuningPlusLoggerTesting('Deleted ' . parityTuningPlusMarkerTidy($name));
		return true;
	}
	return false;
}


// get the type of a check according to which marker files exist
// (plus apply some consistency checks against scenarios that should not happen)
//		 ~~~~~~~~~~~~~~~~~~~~
function operationTriggerType($action = null, $active=null) {
//		 ~~~~~~~~~~~~~~~~~~~~
	global $parityTuningPlusAction, $parityTuningPlusActive;
	

	if (is_null($action)) $action = $parityTuningPlusAction;
	if (is_null($active)) $active = $parityTuningPlusActive;
	if (! file_exists(PARITY_TUNING_PLUS_RESTART_FILE) ) {
		if (!($active)) {
			return '';
		}
	}
	if (! startsWith($action, 'check')) {
		parityTuningPlusLoggerTesting ('... ' . pctT('not a parity check so always treat it as an automatic operation'));
		createMarkerFile (PARITY_TUNING_PLUS_AUTOMATIC_FILE);
		if (file_exists(PARITY_TUNING_PLUS_SCHEDULED_FILE)) {
			parityTuningPlusLogger("WARNING: scheduled marker file found for $parityTuningPlusAction");
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_SCHEDULED_FILE);
		}
		if (file_exists(PARITY_TUNING_PLUS_MANUAL_FILE))	{
			parityTuningPlusLogger("WARNING: manual marker file found for $parityTuningPlusAction");
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MANUAL_FILE);
		}
		return 'AUTOMATIC';
	} else {
		// If we have not caught the start then assume an automatic parity check
		if (file_exists(PARITY_TUNING_PLUS_SCHEDULED_FILE)) {
			parityTuningPlusLoggerTesting ('... ' . pctT('appears to be marked as scheduled parity check'));
			if (file_exists(PARITY_TUNING_PLUS_MANUAL_FILE))	{
				parityTuningPlusLogger("WARNING: marker file found for both scheduled and manual $parityTuningPlusAction");
				parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_SCHEDULED_FILE);
			}
			if (file_exists(PARITY_TUNING_PLUS_AUTOMATIC_FILE)) {
				parityTuningPlusLogger("WARNING: marker file found for both scheduled and automatic $parityTuningPlusAction");
				parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_SCHEDULED_FILE);
			}
			return 'SCHEDULED';
		} else if (file_exists(PARITY_TUNING_PLUS_AUTOMATIC_FILE)) {
			parityTuningPlusLoggerTesting ('... ' . pctT('appears to be marked as automatic parity check'));
			if (file_exists(PARITY_TUNING_PLUS_MANUAL_FILE))	{
				parityTuningPlusLogger("WARNING: marker file found for both automatic and manual $parityTuningPlusAction");
				parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MANUAL_FILE);
			}
			return 'AUTOMATIC';
		} else if (file_exists(PARITY_TUNING_PLUS_MANUAL_FILE)) {
			parityTuningPlusLoggerTesting ('... ' . pctT('appears to be manual parity check'));
			return 'MANUAL';
		} else if (file_exists(PARITY_TUNING_PLUS_PARTIAL_FILE)) {
			parityTuningPlusLoggerTesting ('... ' . pctT('appears to be partial parity check'));
			return 'PARTIAL';			
		} else {
	
			parityTuningPlusLoggerTesting ('... ' . pctT('trigger unknown - assume manual'));
			createMarkerFile (PARITY_TUNING_PLUS_MANUAL_FILE);
			return 'MANUAL';
		}
	}
}

// Get the long text description of an active array operation
// if $correcting is omitted, then the mdstat values will be assumed
// if $trigger is omitted, then the presenced of marked files will be used
// if $active is omitted or false, then the mdstat active state will be used

//       ~~~~~~~~~~~~~~~~
function actionDescription($action = null, $correcting = null, $trigger = null, $active = null, $translate = true) {
    global $parityTuningPlusAction, $parityTuningPlusActive, $parityTuningPlusCorrecting;
    $action = $action ?? $parityTuningPlusAction;
    $correcting = $correcting ?? $parityTuningPlusCorrecting;
    $active = $active ?? $parityTuningPlusActive;
    $trigger = $trigger ?? operationTriggerType($action, $active);
    $act = preg_split('/\s+/', trim((string)$action));
    switch (strtolower($act[0])) {
        case 'recon': $parts = ['Parity Sync / Data Rebuild']; break;
        case 'clear': $parts = ['Disk Clear']; break;
        case 'check':
            $prefixes = ['MANUAL'=>'Manual', 'SCHEDULED'=>'Scheduled', 'AUTOMATIC'=>'Automatic', 'PARTIAL'=>'Partial'];
            $parts = isset($prefixes[strtoupper($trigger)]) ? [$prefixes[strtoupper($trigger)]] : [];
            if (count($act) === 1) $parts[] = 'Read-Check';
            else {
                $parts[] = $correcting ? 'Correcting' : 'Non-Correcting';
                $parts[] = 'Parity-Check';
            }
            break;
        default:
            return sprintf($translate ? pctT('Unknown action: %s') : 'Unknown action: %s', $action);
    }
    return implode(' ', $translate ? array_map('pctT', $parts) : $parts);
}


//	test if partial parity check in progress
//       ~~~~~~~~~~~~~~~~~~~
function parityTuningPlusPartial() {
//       ~~~~~~~~~~~~~~~~~~~
	return ( file_exists(PARITY_TUNING_PLUS_PARTIAL_FILE));
}

// Logging functions

// Write message to syslog and also to console if in CLI mode
// Change source according to whether doing partial check or not

//       ~~~~~~~~~~~~~~~~
function parityTuningPlusLogger($string) {  
//       ~~~~~~~~~~~~~~~~
  global $parityTuningPlusCfg, $parityTuningPlusServer;	
  $logTarget = $parityTuningPlusCfg['parityTuningPlusLogTarget'];
  $logName = parityTuningPlusPartial() ? "Parity Check Tuning Plus Assistant" : "Parity Check Tuning Plus";
  if ($logTarget > 0) {
	 $line = date(PARITY_TUNING_PLUS_DATE_FORMAT) . ' ' . $parityTuningPlusServer . " $logName: $string\n";
	 file_put_contents(PARITY_TUNING_PLUS_LOG_FILE, $line, FILE_APPEND | LOCK_EX);
  }
  if ($logTarget < 2)  {
	$cmd = 'logger -t ' . escapeshellarg($logName) . ' -- ' . escapeshellarg($string);
	shell_exec($cmd);
  }
}

// Write message to syslog if debug or testing logging active

//       ~~~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusLoggerDebug($string) {
//       ~~~~~~~~~~~~~~~~~~~~~~~
  global $parityTuningPlusCfg;
  if ($parityTuningPlusCfg['parityTuningPlusLogging'] > 0) parityTuningPlusLogger('DEBUG:   ' . $string);
}

// Write message to syslog if testing logging active

//       ~~~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusLoggerTesting($string) {
//       ~~~~~~~~~~~~~~~~~~~~~~~
  global $parityTuningPlusCfg, $command;
  if ($parityTuningPlusCfg['parityTuningPlusLogging'] > 1) {
	parityTuningPlusLogger('TESTING:'.(is_null($command)?'':strtoupper($command))." $string");
  }
}



// Useful matching functions

//       ~~~~~~~~~~
function startsWith($haystack, $beginning){
//       ~~~~~~~~~~
	if (is_null($haystack)) {
		parityTuningPlusLoggerTesting("haystack=null on call to startsWith()");
		return false;
	}
	if (is_null($beginning)) {
		parityTuningPlusLoggerTesting("beginning=null on call to startsWith()");
		return false;
	}
    return strncmp($haystack, $beginning, strlen($beginning)) === 0;
}

?>
