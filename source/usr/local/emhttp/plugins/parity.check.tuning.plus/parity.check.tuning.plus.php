#!/usr/bin/php
<?PHP
/*
 * Script parity.check.tuning.plus.php that is run to carry out support tasks for the parity.check.tuning.plus plugin.
 *
 * It can be triggered in a variety of ways such as an Unraid event; a cron job;
 * a page file command; or from another script.
 *
 * It takes a parameter describing the action required.
 *
 * It can also be called via CLI as the command 'parity.check.plus' to expose functionality
 * that relates to parity checking.
 *
 * Copyright 2019-2026, Dave Walker (itimpi).
 * Modified 2026-11-04 by alexphillips-dev for Parity Check Tuning Plus.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License version 2,
 * as published by the Free Software Foundation.
 *
 * Limetech is given explicit permission to use thfis code in any way they like.
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * Useful site for checking php sytax: https://phphub.net/linter/
 */

require_once '/usr/local/emhttp/plugins/parity.check.tuning.plus/parity.check.tuning.plus.helpers.php';
require_once __DIR__ . '/parity.check.tuning.plus.background.php';
require_once __DIR__ . '/parity.check.tuning.plus.completion.php';
require_once __DIR__ . '/parity.check.tuning.plus.temperature.php';

// Work out what type of action triggered calling this script
if (empty($argv)) {
  parityTuningPlusLoggerDebug(pctT("ERROR") . ": " . pctT("No action specified"));
  exit(0);
}

$command = (count($argv) > 1) ? trim($argv[1]) : '?';
spacerDebugLine(true, $command);

// Normally cron triggers actions on minute boundaries and this can lead to two different
// invocations of this script running in parallel.  Adding a random delay to the monitor 
// tasks which are not time critical is an attempt to stop simultaneous calls interleaving
// although if they do things should still operate OK, but the logs look a lot tidier 
// and are easier to interpret.

$parityTuningPlusCLI = isset($argv)?(basename($argv[0]) == 'parity.check.plus'):false;
if (!$parityTuningPlusCLI && !in_array(strtolower($command), ['mdcmd', 'mdcmd_prepare'], true)) {
	$sleepTime = rand(5,10);
	parityTuningPlusLoggerTesting (sprintf('waiting %d seconds to minimnise chance of race conditions', $sleepTime));
	sleep ($sleepTime);		// Desynchonize calls via cron
	loadVars();					// Allow for fact these might have changed while sleeping.
}

// Show the start of the action in the logs requested via the command line argument(s)
// Effectively each command line option is like an event type1

if ($parityTuningPlusCLI) parityTuningPlusLoggerTesting("CLI Mode active");

// Some useful constants local to this file
// Marker files are used to try and inicate state type information
define('UNRAID_PARITY_SYNC_FILE',      '/boot/config/forcesync');		        // Presence of file used by Unraid to detect unclean Shutdown (we currently ignore)
define('UNRAID_PARITY_HISTORY_FILE',   '/boot/config/parity-checks.log');		// File that holds history of array operations  
define('PARITY_TUNING_PLUS_CRON_FILE',      PARITY_TUNING_PLUS_FILE_PREFIX . 'cron');	    // File created to hold current cron settings for this plugin
define('PARITY_TUNING_PLUS_PROGRESS_FILE',  PARITY_TUNING_PLUS_FILE_PREFIX . 'progress'); // Created when array operation active to hold increment info
define('PARITY_TUNING_PLUS_PROGRESS_SAVE',  PARITY_TUNING_PLUS_FILE_PREFIX . 'progress.save');// Created when analysis completed
define('PARITY_TUNING_PLUS_INCREMENT_FILE',  PARITY_TUNING_PLUS_FILE_PREFIX . 'increment');// Present when within increment times
define('PARITY_TUNING_PLUS_MOVER_FILE',     PARITY_TUNING_PLUS_FILE_PREFIX . 'mover');	 // Present when paused because mover is running
define('PARITY_TUNING_PLUS_BACKUP_FILE',    PARITY_TUNING_PLUS_FILE_PREFIX . 'backup');	// Present when paused because CA Backup is running
define('PARITY_TUNING_PLUS_HOT_FILE',       PARITY_TUNING_PLUS_FILE_PREFIX . 'hot');	    // Present when paused because at least one drive found to have reached 'hot' temperature
define('PARITY_TUNING_PLUS_CRITICAL_FILE',  PARITY_TUNING_PLUS_FILE_PREFIX . 'critical'); // Created when parused besause at least one drive found to reach critical temperature
define('PARITY_TUNING_PLUS_DISKS_FILE',     PARITY_TUNING_PLUS_FILE_PREFIX . 'disks');    // Copy of disks.ini  info saved to allow check if disk configuration changed
define('PARITY_TUNING_PLUS_TIDY_FILE',      PARITY_TUNING_PLUS_FILE_PREFIX . 'tidy');	    // Create when we think there was a tidy shutdown
define('PARITY_TUNING_PLUS_SHUTDOWN_FILE',  PARITY_TUNING_PLUS_FILE_PREFIX . 'shutdown');	// Create when shutdown required after array operation
define('PARITY_TUNING_PLUS_STOPPING_FILE',  PARITY_TUNING_PLUS_FILE_PREFIX . 'stopping');	// Create when array stop is initiated
define('PARITY_TUNING_PLUS_HISTORY_FILE',    PARITY_TUNING_PLUS_FILE_PREFIX . 'history');


// check for presence of any plugin marker files that can
// (optionally) exist on flash drive indicating status (useful 
// to know when testing the plugin

$filesToCheck = array(UNRAID_PARITY_SYNC_FILE,
   					  PARITY_TUNING_PLUS_TIDY_FILE,
					  PARITY_TUNING_PLUS_PROGRESS_FILE,
					  PARITY_TUNING_PLUS_AUTOMATIC_FILE,
					  PARITY_TUNING_PLUS_MANUAL_FILE,
					  PARITY_TUNING_PLUS_SCHEDULED_FILE,
					  PARITY_TUNING_PLUS_INCREMENT_FILE,
					  PARITY_TUNING_PLUS_RESTART_FILE,
		  			  PARITY_TUNING_PLUS_BACKUP_FILE,
					  PARITY_TUNING_PLUS_PARTIAL_FILE, 	
					  PARITY_TUNING_PLUS_DISKS_FILE,
					  PARITY_TUNING_PLUS_HOT_FILE,
					  PARITY_TUNING_PLUS_CRITICAL_FILE,
					  PARITY_TUNING_PLUS_STOPPING_FILE,
					  PARITY_TUNING_PLUS_SHUTDOWN_FILE, 
					  PARITY_TUNING_PLUS_MOVER_FILE);
foreach ($filesToCheck as $filename) {
	if ($parityTuningPlusCfg['parityTuningPlusLogging'] > 1) {
		// For effeciency only do these checks in Testing logging mode
		if (file_exists($filename)) {
			$tidyname=str_replace(PARITY_TUNING_PLUS_FILE_PREFIX,'',$filename);
			parityTuningPlusLoggerTesting("$tidyname marker file present");
		}
	}
}


switch (strtolower($command)) {

	//--------------------------------- PHP triggered ----------------------------
	//						Options triggered by PHP of shell scripts
	
	case 'defaults':
		// reset user configuration to the defaults issued with plugin
		copy(PARITY_TUNING_PLUS_DEFAULTS_FILE, PARITY_TUNING_PLUS_CFG_FILE);
		$parityTuningPlusCfg = parse_plugin_cfg(PARITY_TUNING_PLUS_PLUGIN);
		parityTuningPlusLogger(pctT('Settings reset to default values'));
		// FALLTHRU
	case 'config':
		parityTuningPlusLogger (sprintf( pctT('Versions: Unraid %s, Plugin %s'),$parityTuningPlusUnraidVersion,pctVersion(PARITY_TUNING_PLUS_VERSION_FILE)));
		parityTuningPlusLogger(pctT('Configuration'));
		parityTuningPlusLogger(print_r($parityTuningPlusCfg,true));
		// FALLTHRU
	case 'updatecron':
		// set up cron entries based on current configuration values
		updateCronEntries();
        break;

    case 'mdcmd_prepare':
        if (strtolower($argv[3] ?? '') === 'check' && strtolower($argv[4] ?? '') !== 'resume'
            && !$parityTuningPlusActive && file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
            parityTuningPlusProgressAnalyze();
        }
        break;

    case 'mdcmd':
        // This case is aimed at telling when a scheduled call to
		// 'mdcmd' was made so that we can detect if a parity check
		// was started on a schedule or whether it was manually
		// started.
        $cmd = 'mdcmd '; for ($i = 3; $i < count($argv) ; $i++)  $cmd .= $argv[$i] . ' ';
        parityTuningPlusLoggerDebug(sprintf(pctT('detected that mdcmd had been called from %s with command %s'), $argv[2], $cmd));
        switch (strtolower($argv[2])) {
			case 'crond':
			case 'sh':
			case 'bash':
				switch (strtolower($argv[3])) {
					case 'check':
						loadVars(5);         // give time for start/resume
                        if (!$parityTuningPlusActive) {
                            parityTuningPlusLoggerTesting('Native check command did not leave an active operation');
                            break;
                        }
						if (strtolower($argv[4] ?? '') === 'resume') {
                            if ($parityTuningPlusPaused) break;
							parityTuningPlusLoggerDebug ('... ' . sprintf(pctT('Resume %s'), $parityTuningPlusDescription));
							parityTuningPlusProgressWrite('RESUME');		// We want state after resume has started
						} else {
							if (file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
								parityTuningPlusLoggerTesting('analyze previous progress before starting new one');
								parityTuningPlusProgressAnalyze();
							}
							// Work out what type of trigger
							if (strtolower($argv[2]) === 'crond') {
								parityTuningPlusLoggerTesting ('... ' . pctT('appears to be a regular scheduled check'));
                                pctSetOperationTrigger('SCHEDULED');
								parityTuningPlusProgressWrite ('SCHEDULED');
							} else {
								$triggerType = operationTriggerType();
								parityTuningPlusLoggerTesting ('... ' . sprintf(pctT('Appears to be a %s array operation'), $triggerType));
								parityTuningPlusProgressWrite ($triggerType);
							}
						}
						break;
					case 'nocheck':
						loadVars(5);         // give time for pause/cancel
                        if (!$parityTuningPlusStateValid || parityTuningPlusPartial()) break;
                        $requestedPause = strtolower($argv[4] ?? '') === 'pause';
                        if ($requestedPause ? !$parityTuningPlusPaused : $parityTuningPlusActive) {
                            parityTuningPlusLoggerTesting('Native stop command did not reach its requested state');
                            break;
                        }
						if (!isset($argv[4])) {
							parityTuningPlusProgressWrite ('CANCELLED');
							parityTuningPlusProgressAnalyze();
							parityTuningPlusInactiveCleanup();
						} else {
							switch (strtolower($argv[4])) {
								case 'pause':                     
									parityTuningPlusLoggerDebug ('...' . sprintf(pctT('Pause %s'), $parityTuningPlusDescription));
									parityTuningPlusProgressWrite ("PAUSE");
									break;
								case 'cancel':
								default:
									parityTuningPlusProgressWrite ('CANCELLED');
									parityTuningPlusProgressAnalyze();
									parityTuningPlusInactiveCleanup();
									break;
							}
						}
						updateCronEntries();
						suppressMonitorNotification();
						break;
					}  // end of 'crond/sh' 
					break;
				
			// Compatibility with observations from event-named native callers.
			case 'array_started':
					if ($argv[4] === 'pause') {
						parityTuningPlusProgressWrite ('PAUSE');
					}
					break;
					
			case 'started':
					updateCronEntries();
					parityTuningPlusLoggerTesting('Must be part of restart operation so nothing further to do!');
					break;
					
					
			case 'mover':
					parityTuningPlusLoggerTesting('... ignore as generated by mover');
					break; 	
					
			default:
					parityTuningPlusLoggerDebug(pctT('Option not currently recognized').': '.$argv[2]);
					break;
		}  // end of operation type switch
		break;

	//-------------------------------- cron options ------------------------------
	//				Options set up to be run via cron at specified intervals
	
    case 'monitor':
        // This is invoked at regular intervals to try and detect
		// some sort of relevant status change that we need to take
		// some action on.  In particular disks overheating 
		// (or cooling back down).
        //
        // This is also the place where we can detect manual checks
		// have been started.
        //
        // The monitor frequency varies according to whether
		// temperatures are being checked or partial parity checks
		// are active as then we do it more often.

		if (! file_exists(PARITY_TUNING_PLUS_EMHTTP_DISKS_FILE)) {
			parityTuningPlusLoggerTesting('System appears to still be initializing - disk information not available');
			break;
		}	
        if ($parityTuningPlusCfg['parityTuningPlusHeat'] || $parityTuningPlusCfg['parityTuningPlusHeatShutdown']) {
            require_once "$docroot/webGui/include/CustomMerge.php";
        }
        // Critical protection applies to all available disks, even while idle,
        // stopped, restarting, or running an assistant check.
        if ($parityTuningPlusCfg['parityTuningPlusHeatShutdown']) {
            $criticalDrives = pctCriticalTemperatureDrives($disks, $dynamixCfg['display'] ?? [], $parityTuningPlusCfg['parityTuningPlusHeatCritical']);
            if ($criticalDrives) {
                $drives = listDrives($criticalDrives);
                file_put_contents(PARITY_TUNING_PLUS_CRITICAL_FILE, "$drives\n", LOCK_EX);
                $msg = pctT('Following drives overheated') . ': ' . $drives;
                parityTuningPlusShutdown($msg, true);
                break;
            }
        }
        if (!$parityTuningPlusStarted) {
			parityTuningPlusLoggerTesting('Array not yet started so nothing to monitor');
			break;
		}
		// See if array operation is being restarted
		// Apply some consistency checks here as well for safety reasons
		if (file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
			if (file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
				if ($parityTuningPlusActive) {
					parityTuningPlusLoggerTesting (pctT('no action taken as appears restart outstanding'));
				} else {
					loadVars(30);
					if (!$parityTuningPlusActive) {
						parityTuningPlusLoggerTesting (pctT('Restart requested - but appears to not be happening'));
						parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_RESTART_FILE);	// Tidy up
					}
				}
				break;
			} else {
				// This condition should never happen if things are working as expected
				parityTuningPlusLogger (pctT('Inconsisten state information - Restart requested but no progress file'));
				loadVars(30);			// Just in case STARTING is still running
				parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_RESTART_FILE);	// Tidy up
			}
		}

		// Handle monitoring of partial checks

		if (parityTuningPlusPartial()) {
            $range = pctPartialOwner($var);
            if ($range === false) {
                parityTuningPlusLoggerTesting('Partial ownership is missing or stale; leaving native operation untouched');
                parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_PARTIAL_FILE);
                updateCronEntries();
                break;
            }
			$endpointReached = false;
			if (isArrayOperationActive()) {
				$parityTuningPlusSector = $parityTuningPlusPos * 2;
				if ($parityTuningPlusSector < pctPartialEndSector()) {
					parityTuningPlusLoggerTesting ("Partial check: sector reached:$parityTuningPlusSector, end sector:".$parityTuningPlusCfg['parityProblemPlusEndSector']);
					break;
				}
				parityTuningPlusLoggerTesting('Stop partial check');

				exec('/usr/local/sbin/mdcmd nocheck', $partialOutput, $partialStatus);
				loadVars(3);			// Need to confirm this is long enough!
                if ($partialStatus !== 0 || $parityTuningPlusActive) break;
                $endpointReached = true;
			}
			parityTuningPlusProgressWrite('PARTIAL STOP');
			parityTuningPlusProgressSave();
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_PROGRESS_FILE);
			suppressMonitorNotification();
			$runType = $range['correct'] ? pctT('Correcting') : pctT('Non-Correcting');
			sendNotification($endpointReached || (int)$var['sbSyncExit'] === 0 ? sprintf(pctT('Completed partial check (%s)'), $runType) : pctT('canceled'),
			parityTuningPlusPartialRange() . ' ' . pctT('Errors') . ' ' . $var['sbSyncErrs'] );
			parityTuningPlusDeleteFile (PARITY_TUNING_PLUS_PARTIAL_FILE);
			updateCronEntries();
			break;
		}

		$backgroundBlocked = backGroundTaskRunning();

		// See if no array operation in progress so that we no longer need to consider pause/resume
		if (!isArrayOperationActive()) {
			parityTuningPlusLoggerTesting (pctT('no array operation in progress'));
			parityTuningPlusProgressAnalyze();
			parityTuningPlusInactiveCleanup();
			break;
		}

		// Consistency checks
		$trigger = operationTriggerType();
		if (! file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
			parityTuningPlusLoggerTesting (pctT('appears there is a running array operation but no Progress file yet created'));
			parityTuningPlusLogger ($parityTuningPlusDescription.' '.pctT('detected'));
			parityTuningPlusProgressWrite ($trigger);
			updateCronEntries();    // ensure reasonably frequent monitor checks
		}
		// Record manual transitions not already captured by the verified native-command hooks.
		if (file_exists(PARITY_TUNING_PLUS_MANUAL_FILE)) {
			if (parityTuningPlusProgressWrite($parityTuningPlusPaused?'PAUSE (MANUAL)':'RESUME (MANUAL)')) {				
				ParityTuningPlusLogger($parityTuningPlusDescription.': '.($parityTuningPlusPaused?pctT('Manually paused'):pctT('Manually resumed')));
			}
		}

		// Added Shutdown marker file if required
		if ($parityTuningPlusCfg['parityTuningPlusShutdown'] ) {
			if (! file_exists(PARITY_TUNING_PLUS_SHUTDOWN_FILE)) {
				$msg=pctT('Server will be shutdown when array operation completes');
				parityTuningPlusLogger ($msg);
				sendNotificationWithCompletion($msg);
				createMarkerFile (PARITY_TUNING_PLUS_SHUTDOWN_FILE);
			}
		}

        // Check for disk temperature changes we are monitoring

        if ((!$parityTuningPlusCfg['parityTuningPlusHeat']) && (! $parityTuningPlusCfg['parityTuningPlusHeatShutdown'])) {
            parityTuningPlusLoggerTesting (pctT('Temperature monitoring switched off'));
            parityTuningPlusDeleteFile (PARITY_TUNING_PLUS_CRITICAL_FILE);
            break;
        }

        // Get disk temperature information
		//
		// It is slightly complicated by the fact that the
		// temperature of spundown disks cannot be read.
		// We also need to allow for fact that indivdual disks
		// can override the global settings

        $dynamixCfg = parse_ini_file('/boot/config/plugins/dynamix/dynamix.cfg', true);
        $hotDrives = array();       // drives that exceed pause threshold
        $warmDrives = array();      // drives that are between pause and resume thresholds
        $coolDrives = array();      // drives that are cooler than resume threshold
		$spinDrives = array();  	// drives that ase spundown so need spinning up to read temperatures
		$idleDrives = array();		// drives no longes being used
        $arrayCount = 0;
        $status = '';
		$globalWarning = ($dynamixCfg['display']['hot']??45);
		$globalCritical = ($dynamixCfg['display']['max']??55);
		parityTuningPlusLoggerTesting (pctT('global temperature limits')
									. ': ' . pctT('Warning') . ': ' . 
									($globalWarning == 0?pctT('disabled'):$globalWarning)
									. ', ' . pctT('Critical') . ': ' . 
									($globalCritical == 0?pctT('disabled'):$globalCritical));
        parityTuningPlusLoggerTesting (pctT('plugin temperature settings') 
									. ': ' . pctT('Pause') . ' ' .  $parityTuningPlusCfg['parityTuningPlusHeatHigh'] 
									. ', ' . pctT('Resume') . ' ' . $parityTuningPlusCfg['parityTuningPlusHeatLow']
                				   . ($parityTuningPlusCfg['parityTuningPlusHeatShutdown'] ? (', ' . pctT('Shutdown') . ' ' . $parityTuningPlusCfg['parityTuningPlusHeatCritical']) . ')' : ''));
		// Get configuration settings
		$parityTuningPlusHeatCritical = $parityTuningPlusCfg['parityTuningPlusHeatCritical'];
		$parityTuningPlusHeatHigh     = $parityTuningPlusCfg['parityTuningPlusHeatHigh'];
		$parityTuningPlusHeatLow      = $parityTuningPlusCfg['parityTuningPlusHeatLow'];	
		// gather temperature information from all drives
        foreach ($disks as $drive) {
            $name=$drive['name'];
            $temp = $drive['temp'];
			// The flash drive is ignored
			// All other drives are potentially checked even if not part of the array
			if ((!startsWith($drive['status'],'DISK_NP')) && (!($name === 'flash'))) {
                $driveWarning = pctDiskTemperatureLimit($drive, $dynamixCfg['display'] ?? [], 'hotTemp');
                $driveCritical = pctDiskTemperatureLimit($drive, $dynamixCfg['display'] ?? [], 'maxTemp');
				if (($driveWarning != $globalWarning)
				||  ($driveCritical != $globalCritical)) {
					parityTuningPlusLoggerTesting (pctT('drive temperature limits')
									. ': ' . pctT('Warning') . ': ' . 
									($driveWarning== 0?pctT('disabled'):$driveWarning)
									. ', ' . pctT('Critical') . ': ' . 
									($driveCritical== 0?pctT('disabled'):$driveCritical));
				}
                $critical  = $driveCritical - $parityTuningPlusHeatCritical;
                $hot  = $driveWarning - $parityTuningPlusHeatHigh;
                $cool = $driveWarning - $parityTuningPlusHeatLow;
				
				// Only array disks control operation pausing; critical protection above covers pools too.
				if ((startsWith($name, 'parity')) || (startsWith($name,'disk'))) {
					$arrayCount++;
					if ($temp == "*" ) { 	// spun down
						if ($drive['size'] > $parityTuningPlusPos) {
							$spinDrives[] = $name;
						} else {
							$idleDrives[$name] = $temp;
							$status = pctT('past size');
						}
					} else {
						if ($driveWarning == 0) {
							$status = pctT('disabled');
						} else {
							if ($temp <= $cool) {
							  $coolDrives[$name] = $temp;
							  $status = pctT('cool');
							} elseif ($temp >= $hot) {
							  $hotDrives[$name] = $temp;
							  $status = pctT('hot');
							} else {
								$warmDrives[$name] = $temp;
								$status = pctT('warm');
							}
						}
					}
					//  Check drives for critical temperatures
					if ($driveCritical == 0) {
						if ($driveWarning == 0) $status = pctT('disabled');
					} else {
						if ((($temp != "*" )) && ($temp >= $critical)) {
							parityTuningPlusLoggerTesting(sprintf('Drive %s: %s%s appears to be critical (%s%s)', $name, tempInDisplayUnit($temp), $parityTuningPlusTempUnit,
							$critical, $parityTuningPlusTempUnit));
							$status = pctT('critical');
						}
					}
					parityTuningPlusLoggerTesting (sprintf('%s temp=%s%s, status=%s (drive settings: hot=%s%s, cool=%s%s',$name,
												($temp=='*')?'*':tempInDisplayUnit($temp),
												($temp=='*')?'':$parityTuningPlusTempUnit, $status,
												tempInDisplayUnit($hot), $parityTuningPlusTempUnit,
												tempInDisplayUnit($cool), $parityTuningPlusTempUnit)
											   . ($parityTuningPlusCfg['parityTuningPlusHeatShutdown'] ? sprintf(', critical=%s%s',tempInDisplayUnit($critical), $parityTuningPlusTempUnit) : ''). ')');
				}
			}
        }  // end of for loop gathering temperature information


		// Handle drives being paused/resumed due to temperature
        if (!$parityTuningPlusCfg['parityTuningPlusHeat']) break;

        parityTuningPlusLoggerDebug (sprintf('%s=%d, %s=%d, %s=%d, %s=%d, %s=%d, %s=%d', pctT('array drives'), $arrayCount, pctT('hot'), count($hotDrives), pctT('warm'), count($warmDrives), pctT('cool'), count($coolDrives),pctT('spundown'),count($spinDrives),pctT('idle'),count($idleDrives)));
        if (!$parityTuningPlusPaused) {
			// PAUSE?
        	// Check if we need to pause because at least one drive too hot
            if (count($hotDrives) == 0) {
                parityTuningPlusLoggerDebug (sprintf('%s',pctT('All array drives below temperature threshold for a Pause')));
            } else {
                $drives = listDrives($hotDrives);
                $msg = (sprintf('%s: ',pctT('Following drives overheated')) . $drives);
                if (parityTuningPlusPause($msg, false)) {
                    file_put_contents(PARITY_TUNING_PLUS_HOT_FILE, "$drives\n", LOCK_EX);
                    parityTuningPlusLogger(sprintf('%s %s %s: %s',pctT('Paused'), $parityTuningPlusDescription, parityTuningPlusCompleted(), $msg));
                    sendTempNotification(opWithErrorCount(pctT('Pause')), $msg);
                }
            }
        } else {
			// RESUME?
        	// Check if we need to resume because drives cooled sufficiently. 
            if (! file_exists(PARITY_TUNING_PLUS_HOT_FILE)) {
				// No resume if temperature marker file not found
                parityTuningPlusLoggerDebug (pctT('Array operation paused but not for temperature related reason'));
				break;
            } else {
             	if (count($hotDrives) != 0) {
					// No resume if hot drives still present
             		parityTuningPlusLoggerDebug (pctT('Array operation paused with some drives still too hot to resume'));
					break;
                } else {
             		if (count($warmDrives) != 0) {
						// No resume if drives not sufficiently cooled
						parityTuningPlusLoggerDebug (pctT('Array operation paused but drives not cooled enough to resume'));
						// Generate notification if Pause seemes to be excessive
						// (this may be due to resume threshold being too high)
						$waitMinutes = (int)((time() - filemtime(PARITY_TUNING_PLUS_HOT_FILE)) / 60);
						$tooLongMinutes = $parityTuningPlusCfg['parityTuningPlusHeatTooLong'];
						if (($waitMinutes > $tooLongMinutes)
						&&  ($waitMinutes <= ($tooLongMinutes + $parityTuningPlusCfg['parityTuningPlusMonitorHeat'])))
						{
							sendTempNotification(opWithErrorCount(pctT('Waiting')), sprintf(pctT('Drives been above resume temperature threshold for %s minutes'),$waitMinutes));
						}
						break;

					} else {
						parityTuningPlusLoggerTesting ('Some drives spun down - assume they are cool');
					//
					// Spun-down disks have no current sensor reading; the next monitor rechecks active disks.
					//
                        if (!isIncrementActive($parityTuningPlusAction)) {
                            parityTuningPlusLoggerDebug(pctT('Outside increment scheguled time'));
                            parityTuningPlusLogger(pctT('Outside times for increments so not resuming'));
                            parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_HOT_FILE);
                            break;
                        }
                        if ($backgroundBlocked) break;
                        if (parityTuningPlusResume(false)) {
                            parityTuningPlusLogger(sprintf('%s %s %s %s',pctT('Resumed'),$parityTuningPlusDescription,parityTuningPlusCompleted(),pctT('Drives cooled down')));
                            sendTempNotification(opWithErrorCount(pctT('Resume')),pctT('Drives cooled down'));
                            parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_HOT_FILE);
                        }

                	}
				}
			}
        }
        break;

    // A resume of an array operation has been requested.
	// This could be via a scheduled cron task or a CLI command
		
    case 'resume':
		createMarkerFile(PARITY_TUNING_PLUS_INCREMENT_FILE);
        parityTuningPlusLoggerDebug (pctT('Resume request'));
		if (!$parityTuningPlusStarted) {
			parityTuningPlusLoggerTesting('Array not yet started so nothing to resume');
			break;
		}

		if (file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
			parityTuningPlusLoggerTesting('Resume ignored as restart pending');
			break;
		}
        if (! isArrayOperationActive()) {
        	parityTuningPlusLoggerDebug('Resume ignored as no array operation in progress');
			parityTuningPlusInactiveCleanup();			// tidy up any marker files
        	break;
        }
		if (parityTuningPlusPartial()) {
			parityTuningPlusLoggerDebug('Resume ignored as partial check in progress');
			break;
		}
		if (! file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
			parityTuningPlusProgressWrite(operationTriggerType());
		}
		if (!$parityTuningPlusPaused) {
			parityTuningPlusLoggerDebug(sprintf('... %s %s', $parityTuningPlusDescription, pctT('already running')));
			break;
		}
		if (file_exists(PARITY_TUNING_PLUS_HOT_FILE)) {
			parityTuningPlusLoggerDebug('Resume ignored as paused because disks too hot');
			break;
		}
		if (backGroundTaskRunning()) {
			parityTuningPlusLoggerDebug(pctT('Resume ignored as paused because background task running'));
			break;
		}

		// Handle special cases where pause had been because of mover running or disks
		// overheating and we are now outside the window for a scheduled resume
		if (!isActivePeriod()) {
			parityTuningPlusLoggerTesting('resume but not inside increments time window for operation so ignored');
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_HOT_FILE);
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MOVER_FILE);
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_BACKUP_FILE);
		}				
		if ($parityTuningPlusCLI || configuredAction()) {
			parityTuningPlusResume($parityTuningPlusCfg['parityTuningPlusNotify']);
		}
        break;

    // A pause of an array operation has been requested.
	// This could be via a scheduled cron task or a CLI command
	
    case 'pause':
	    parityTuningPlusLoggerDebug (pctT('Pause request'));
		parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_INCREMENT_FILE);
		if (!$parityTuningPlusStarted) {
			parityTuningPlusLoggerTesting('Array not yet started so nothing to pause');
			break;
		}
		if (file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
			parityTuningPlusLoggerTesting('Pause ignored as restart pending');
			break;
		}
        if (! isArrayOperationActive()) {
            parityTuningPlusLoggerDebug('Pause ignored as no array operation in progress');
            break;
		} else {
			parityTuningPlusLoggerTesting('Continue Pause as array operation active');
        }
		if (parityTuningPlusPartial()) {
			parityTuningPlusLoggerDebug('Pause ignored as partial check in progress');
			break;
		}
		// We expect a progress file to exists at this point, but lets play safe.
		if (! file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
			parityTuningPlusProgressWrite(operationTriggerType());
		}
		
		if ($parityTuningPlusCLI) {
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MOVER_FILE);
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_BACKUP_FILE);
		}
		// We only need to really issue the pause if not already paused
		if ($parityTuningPlusPaused) {
			parityTuningPlusLoggerDebug(sprintf('%s %s!', $parityTuningPlusDescription, pctT('already paused')));
			break;
		}

		if ($parityTuningPlusCLI || configuredAction()) {
			// Remove any files indicated we might have paused for some other reason
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MOVER_FILE);
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_BACKUP_FILE);
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_HOT_FILE);
			parityTuningPlusPause(actionDescription($parityTuningPlusAction),$parityTuningPlusCfg['parityTuningPlusNotify']);
		}
        break;	

	// Set up partial array parity checks for Parity Check Tuning Plus Assistant mode
	
    case 'partial':
        if (!$parityTuningPlusStarted || $parityTuningPlusActive || $parityTuningPlusNoParity
            || file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
            sendNotification(pctT('Partial check not started'), pctT('Start the array and wait for other array operations to finish'), 'warning');
            break;
        }
        try {
            $range = pctPartialCheckRange($parityTuningPlusCfg, $parityTuningPlusSize * 2);
        } catch (InvalidArgumentException $error) {
            sendNotification(pctT('Partial check not started'), pctT($error->getMessage()), 'warning');
            break;
        }
        $encoded = json_encode($range);
        if (file_put_contents(PARITY_TUNING_PLUS_PARTIAL_FILE, $encoded, LOCK_EX) !== strlen($encoded)) break;
        $cmd = '/usr/local/sbin/mdcmd check ' . ($range['correct'] ? 'correct' : 'nocorrect') . ' ' . $range['startSector'];
        exec($cmd, $partialOutput, $partialStatus);
        loadVars(5);
        if ($partialStatus !== 0 || !$parityTuningPlusActive || (int)$var['sbSynced'] <= 0
            || !startsWith($parityTuningPlusAction, 'check ')) {
            parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_PARTIAL_FILE);
            updateCronEntries();
            sendNotification(pctT('Partial check not started'), pctT('No array operation currently in progress'), 'warning');
            break;
        }
        $range['kernelStart'] = (int)$var['sbSynced'];
        $range['size'] = $parityTuningPlusSize;
        $encoded = json_encode($range);
        if (file_put_contents(PARITY_TUNING_PLUS_PARTIAL_FILE, $encoded, LOCK_EX) !== strlen($encoded)) {
            parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_PARTIAL_FILE);
            break;
        }
        pctSetOperationTrigger('PARTIAL');
        updateCronEntries();
        suppressMonitorNotification();
        parityTuningPlusProgressWrite('PARTIAL');
        $runType = $range['correct'] ? pctT('Correcting') : pctT('Non-Correcting');
        sendNotification(sprintf(pctT('Partial parity check (%s)'), $runType), parityTuningPlusPartialRange());
        break;

    //	------------------------------ Unraid Events --------------------------------------
	//							Options that are triggered by Unraid events


	case 'starting':		// Button to start the array has been used (or auto-start)
		parityTuningPlusLoggerDebug (pctT('Array is being started'));
    	suppressMonitorNotification();
		
		// consistency check
		if (! file_exists(UNRAID_PARITY_SYNC_FILE)) {
			createMarkerFile(PARITY_TUNING_PLUS_TIDY_FILE);
		} else {
			// Not sure this condition can actually arise but lets play safe 
			if (file_exists(PARITY_TUNING_PLUS_TIDY_FILE)) {
				parityTuningPlusLoggerDebug('plugin and Unraid disagree on whether unclean shutdown');
				parityTuningPlusDeleteFile (PARITY_TUNING_PLUS_TIDY_FILE);
			}
			parityTuningPlusLogger(pctT('Unclean shutdown detected'));
			sendNotification(pctT('Unclean shutdown detected') , (file_exists(PARITY_TUNING_PLUS_STOPPING_FILE)? pctT('Unable to stop array'): pctT('System crashed')),'alert'); 
			// Remove any state files that applied before the Unclean shutdown.
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MANUAL_FILE);
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_SCHEDULED_FILE);
		}
		break;


	// runs with 'md' devices valid and when array is about to be started
	// Other services dependent on array active are not yet started
	
    case 'array_started':
    	if (file_exists(PARITY_TUNING_PLUS_CRITICAL_FILE) && ($drives=file_get_contents(PARITY_TUNING_PLUS_CRITICAL_FILE))) {
			$reason = pctT('Detected shutdown that was due to following drives reaching critical temperature');
			parityTuningPlusLogger ("$reason\n$drives");
		}
		parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_CRITICAL_FILE);

		if (file_exists(PARITY_TUNING_PLUS_HOT_FILE) && $drives=file_get_contents(PARITY_TUNING_PLUS_HOT_FILE)) {
			$reason = pctT('Detected that array had been paused due to following drives getting hot');
			parityTuningPlusLogger ("$reason\n$drives");
	    }
		parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_HOT_FILE);
    	if (!file_exists(PARITY_TUNING_PLUS_TIDY_FILE)) {
    		parityTuningPlusLoggerTesting(sprintf(pctT('Tidy shutdown file not present in %s event'), $command));
			suppressMonitorNotification();
			if (file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
				if (file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
					sendNotification (pctT('Array operation will not be restarted'), pctT('Unclean shutdown detected'), 'warning');
					parityTuningPlusProgressWrite('RESTART CANCELLED');
					parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_RESTART_FILE);
				}
			}
			parityTuningPlusProgressWrite('ABORTED');
			parityTuningPlusProgressAnalyze();
			parityTuningPlusInactiveCleanup();
			createMarkerFile(PARITY_TUNING_PLUS_AUTOMATIC_FILE);	// Expect automatic check 
    	} 
    	break;

	// runs with when system startup complete and array is fully started
	
	case 'started':
        parityTuningPlusLoggerDebug (pctT('Array has just been started'));
		suppressMonitorNotification();
		parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_STOPPING_FILE);

		// Sanity Checks on restart that mean restart will not be possible if they fail
		// (not sure these are all really necessary - but better safe than sorry!)
		if (file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
			if (! file_exists(PARITY_TUNING_PLUS_DISKS_FILE)) {
				parityTuningPlusLogger(pctT('Something wrong: progress information present without disks file present'));
				goto end_started;
			}
        } else if (file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
			parityTuningPlusLogger(pctT('Something wrong: restart information present without progress present'));
		    goto end_started;
		}

		if (! file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
			parityTuningPlusLogger (pctT('No restart information present'));
			goto end_started;
		}
	
		// Get restart information
        if (!$parityTuningPlusCfg['parityTuningPlusRestart']) {
            parityTuningPlusLogger('Saved restart ignored because restart policy is disabled');
            goto end_norestart;
        }

        $restart = @parse_ini_file(PARITY_TUNING_PLUS_RESTART_FILE);
        $restartRange = pctRestartRange($restart);
        if ($restartRange === false) {
            parityTuningPlusLogger('Invalid saved restart state; native restart command rejected');
            sendNotification(pctT('Array operation will not be restarted'), '', 'alert');
            goto end_norestart;
        }
		parityTuningPlusLoggerTesting('restart information:');
		foreach ($restart as $key => $value) parityTuningPlusLoggerTesting("$key=$value");	
        $restartPos = $restartRange['sector'];
        $restartCorrect = $restartRange['correct'];
        $restartAction = $restartRange['action'];
        pctSetOperationTrigger(strtoupper($restart['triggerType'] ?? ''));
		$restartDescription = actionDescription($restartAction, $restartCorrect);	
		$restartPaused = ($restart['mdResync'] == 0);
		parityTuningPlusLoggerTesting("restartPos: $restartPos, paused: $restartPaused");
		switch (disksChanged()) {
			case 0:			
				parityTuningPlusLoggerTesting ('Disk configuration appears to be unchanged');
				break;
			case 1:
				$msg = pctT('Detected a change to the disk configuration');
				parityTuningPlusLogger ($msg);
				sendNotification (sprintf(pctT('%s will not be restarted'), $restartDescription), $msg, 'alert');
				goto end_norestart;
			case -1:
				$msg = pctT('Detected disk configuration reset');
				parityTuningPlusLogger ($msg);
				sendNotification (sprintf(pctT('%s will not be restarted'), $restartDescription), $msg, 'alert');
				goto end_norestart;
		}

        // Handle restarting array operations

		parityTuningPlusLogger('restart to be attempted');
		$savedProgress = @file(PARITY_TUNING_PLUS_PROGRESS_FILE, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        $lastProgress = $savedProgress ? explode('|', end($savedProgress)) : [];
        $restartStart = (int)($restart['sbSynced'] ?? $lastProgress[3] ?? 0);
        removeHistoryCancelEntry($restartStart, null, $restartAction);
		// Special case for restarting operations that are not parity checks and where Unraid
		// automatically starte the array operation again from the beginning so we need to cancel
		// it before restarting it at the offset previously reached.
		loadVars(5);
		if ($parityTuningPlusActive) {
			parityTuningPlusLogger(pctT('Cancel automatically started array operation') 
								.' ('.$parityTuningPlusAction
								. pctT('to get ready for restart').')');
            $cancelStart = (int)$var['sbSynced'];
            exec('mdcmd nocheck', $cancelOutput, $cancelStatus);
            for ($attempt = 0; $parityTuningPlusActive && $cancelStatus === 0 && $attempt < 6; $attempt++) loadVars(5);
            if ($parityTuningPlusActive) {
                sendNotification(sprintf(pctT('%s will not be restarted'), $restartDescription),
                    sprintf(pctT('Not allowed as %s already running'), $parityTuningPlusDescription), 'alert');
                goto end_norestart;
            }
			parityTuningPlusLoggerTesting('cancel completed');
			removeHistoryCancelEntry($cancelStart, (int)$var['sbSynced2'], $parityTuningPlusAction);
		} else {
			parityTuningPlusLoggerTesting('no array operation currently active');
		}
		// set up restart command
        $cmd = 'mdcmd check ' . ($restartCorrect ? 'correct' : 'nocorrect') . ' ' . $restartPos;
		suppressMonitorNotification();
		parityTuningPlusLoggerTesting('restart command: ' . $cmd);
        exec($cmd, $restartOutput, $restartStatus);
        for ($attempt = 0; !$parityTuningPlusActive && $restartStatus === 0 && $attempt < 6; $attempt++) loadVars(5);
        if (!$parityTuningPlusActive) {
            sendNotification(sprintf(pctT('%s will not be restarted'), $restartDescription), pctT('No array operation currently in progress'), 'alert');
            goto end_norestart;
        }
		// notification now array operation running
		suppressMonitorNotification();
		parityTuningPlusProgressWrite('RESUME (RESTART)');
		$actionDescription =  $restartDescription . parityTuningPlusCompleted();
		sendNotification(pctT('Array operation restarted'),  $actionDescription, 'normal');
		updateCronEntries();		// Make sure cron entries reflect operation in progress.
		
		if ($restartPaused) {
			parityTuningPlusLogger(pctT('operation was paused when reboot initiated so pause it immediately'));
			parityTuningPlusPause($restartDescription,$parityTuningPlusCfg['parityTuningPlusNotify']);
			goto end_started;			
		}
		// NOTE:  Monitor process can pause it later as well if conditions for that are met.
		if (!isIncrementActive($restartAction)) {
			parityTuningPlusLogger(pctT('Outside time slot for running operation type'));
			parityTuningPlusPause($restartAction,$parityTuningPlusCfg['parityTuningPlusNotify']);
		}
		goto end_started;

end_norestart:
  		if (file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
			// This means we got here without attempting restart
  			parityTuningPlusLogger(pctT('Restart will not be attempted'));
 			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_RESTART_FILE);
 			if (file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
 			    parityTuningPlusProgressWrite('RESTART CANCELLED');
				parityTuningPlusProgressWrite('ABORTED');
 			}
 		}
 		parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_DISKS_FILE);
        parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_SCHEDULED_FILE);
		parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MANUAL_FILE);
		parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_AUTOMATIC_FILE);
end_started:
		parityTuningPlusProgressAnalyze();
		if (file_exists(PARITY_TUNING_PLUS_TIDY_FILE)) {
			parityTuningPlusLoggerTesting(pctT("does not appear to be an unclean shutdown"));
			parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_TIDY_FILE);
		} else {
			// Unclean shutdown processing
			parityTuningPlusLoggerTesting(pctT("appears to be an unclean shutdown"));
			parityTuningPlusInactiveCleanup();
			if ($parityTuningPlusNoParity) {
				parityTuningPlusLoggerTesting(pctT("No parity present, so no automatic parity check"));
			} else {	
				loadVars(30);				// give time for any array operation to start
				if (!isArrayOperationActive()) {
					parityTuningPlusLoggerTesting("array operation not actually Started by Unraid");
				} else {
					parityTuningPlusLoggerTesting("array operation started by Unraid ($parityTuningPlusAction)");
					if (!startsWith($parityTuningPlusAction, 'check')) {
						parityTuningPlusLoggerTesting(sprintf(pctT('Not automatic check (%s)'), $parityTuningPlusAction));
					} else {
						parityTuningPlusLoggerTesting("array operation appears to be automatic check");
						pctSetOperationTrigger('AUTOMATIC');
						if (! $parityTuningPlusCfg['parityTuningPlusAutomatic']) {
							parityTuningPlusLoggerTesting(pctT('Automatic parity check pause not configured'));
						} else {
							parityTuningPlusLoggerTesting(pctT('Pausing Automatic parity check configured'));
							if (isActivePeriod()) {
								parityTuningPlusLoggerTesting(pctT('... but in active period so leave running'));
							} else{
								parityTuningPlusLoggerTesting(pctT('... outside active period so needs pausing'));
								parityTuningPlusPause(actionDescription(),$parityTuningPlusCfg['parityTuningPlusNotify']);
								parityTuningPlusLoggerTesting(pctT('Pausing automatic parity check'));
							}
						}
					}
				}
			}
		}
		parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_RESTART_FILE);
		if ($parityTuningPlusAction == 'check') suppressMonitorNotification();
		break;

	case 'stopping_array':	// The disks and user shares have been unmounted, 
		parityTuningPlusLoggerDebug(pctT('Array stopping'));
		suppressMonitorNotification();
		createMarkerFile(PARITY_TUNING_PLUS_STOPPING_FILE);
		break;

	//	Runs when the Stop button is used to stop the array 
	//	OR when the shutdown/reboot buttons are used.
	
    case 'stopping':
        parityTuningPlusLoggerDebug(pctT('Array stopping'));
		suppressMonitorNotification();
		createMarkerFile(PARITY_TUNING_PLUS_STOPPING_FILE);
        if (!isArrayOperationActive()) {
			// We need to know if this was a second event after array stopped
			if (! file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
				parityTuningPlusLoggerDebug (pctT('No array operation in progress and no restart information saved'));
				parityTuningPlusProgressAnalyze();
			} else {
				parityTuningPlusLoggerDebug (pctT('No array operation in progress but restart information saved'));
			}
        } else {
			parityTuningPlusLoggerDebug (sprintf(pctT('Array stopping while %s was in progress %s'), $parityTuningPlusDescription, parityTuningPlusCompleted()));
		    parityTuningPlusProgressWrite('STOPPING');
			sleep(1);
			if (! $parityTuningPlusCfg['parityTuningPlusRestart']) {
				parityTuningPlusLoggerTesting('Restart option not set');
				parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_RESTART_FILE);
			} else {
				parityTuningPlusLoggerTesting('Restart option set');
				parityTuningPlusLoggerTesting("parityTuningPlusAction=$parityTuningPlusAction");
				$restart = 'mdResync=' . $var['mdResync'] . "\n"
						   .'mdResyncPos=' . $var['mdResyncPos'] . "\n"
						   .'mdResyncSize=' . $var['mdResyncSize'] . "\n"
						   .'mdResyncAction=' . $var['mdResyncAction'] . "\n"
						   .'mdResyncCorr=' . $var['mdResyncCorr'] . "\n"
                           .'sbSynced=' . $var['sbSynced'] . "\n"
						   .'startMode=' . $var['startMode'] . "\n"
						   .'triggerType=' . operationTriggerType() . "\n";
				file_put_contents (PARITY_TUNING_PLUS_RESTART_FILE, $restart);
				parityTuningPlusLoggerTesting('Restart information ($restart) saved to ' 
								. parityTuningPlusMarkerTidy(PARITY_TUNING_PLUS_RESTART_FILE));
				parityTuningPlusProgressWrite('PAUSE (RESTART)');
				sendNotification(pctT('Array stopping: Restart will be attempted on next array start'), $parityTuningPlusDescription
				.parityTuningPlusCompleted());	
			}
			suppressMonitorNotification();
        }
    	break;


	//	Runs when system stopped.
	//	Occurs at end of cmdStop execution, or if cmdStart failed.
	//	The array has been stopped.
	
	case 'stopped':
	    createMarkerFile(PARITY_TUNING_PLUS_TIDY_FILE);
		parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_STOPPING_FILE);
		sleep(1);  // Give some time for file operations to complete
		if (!file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
			parityTuningPlusProgressAnalyze();
			parityTuningPlusInactiveCleanup();
		}
		suppressMonitorNotification();
		break;

//-------------------------------- CLI Options ---------------------------------------
// 					Options that are only currently for CLI use

    case 'analyze':
        parityTuningPlusProgressAnalyze();
        break;

CLI_Status:
    case 'status':
	    $msg = pctT('Status').': ';
		if (! $parityTuningPlusStarted) {
			$msg .= pctT('Array not yet started');
		} else {
			if (!isArrayOperationActive()) {
				$msg .=  pctT('No array operation currently in progress');
			}  else {
			$msg .= actionDescription($parityTuningPlusAction)
					. ($parityTuningPlusPaused ? ' ' . pctT('PAUSED').' ': ' ')
						. parityTuningPlusCompleted();
			}
		}
		parityTuningPlusLoggerCLI($msg);
		break;

    case 'check':
	    $dynamixCfg = parse_ini_file('/boot/config/plugins/dynamix/dynamix.cfg', true);
        $setting = strtolower($dynamixCfg['parity']['write'] ?? 'NOCORRECT');
        $command = $setting === '' ? 'correct' : 'nocorrect';
        parityTuningPlusLoggerCLI(sprintf(pctT('using scheduled mode of %s'),$command),
								PARITY_TUNING_PLUS_LOGGING_DEBUG);
        // fallthru now we know the mode to use
    case 'correct':
    case 'nocorrect':
        if (!$parityTuningPlusStarted) {
            parityTuningPlusLoggerCLI(pctT('Array not yet started'));
            break;
        }
        if (isArrayOperationActive()) {
            parityTuningPlusLoggerCLI(sprintf(pctT('Not allowed as %s already running'),
									$parityTuningPlusDescription));
            break;
        }
        pctSetOperationTrigger('MANUAL');
        exec("/usr/local/sbin/mdcmd check $command", $checkOutput, $checkStatus);
        loadVars(10);		// Need to give time for the operation to actually start.
        if ($checkStatus !== 0 || !$parityTuningPlusActive) {
            if (!$parityTuningPlusActive) parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MANUAL_FILE);
            parityTuningPlusLoggerCLI(pctT('No array operation currently in progress'));
            break;
        }
	    parityTuningPlusLoggerCLI(sprintf(pctT('%s started'), actionDescription($parityTuningPlusAction)));
        if ($parityTuningPlusAction == 'check' && ( $command == 'correct')) {
            if ($parityTuningPlusNoParity) {
            	parityTuningPlusLoggerCLI(pctT('Only able to start a Read-Check as no parity drive present'));
            } else {
            	parityTuningPlusLoggerCLI(pctT('Only able to start a Read-Check due to number of disabled drives'));
            }
        }
	    goto CLI_Status;

    case 'cancel':		// CLI Cancel request
        parityTuningPlusLoggerCLI(pctT('Cancel request'));
        if (isArrayOperationActive()) {
            parityTuningPlusLoggerTesting ('mdResyncAction=' . $parityTuningPlusAction);
            $cancelDescription = $parityTuningPlusDescription;
            exec('/usr/local/sbin/mdcmd nocheck cancel', $cancelOutput, $cancelStatus);
            parityTuningPlusLoggerCLI (sprintf(pctT('%s cancel request sent %s'), $parityTuningPlusDescription, parityTuningPlusCompleted()), PARITY_TUNING_PLUS_LOGGING_DEBUG);
            loadVars(5);
            if ($cancelStatus !== 0 || $parityTuningPlusActive) goto CLI_Status;
            $cancelled = (int)$var['sbSyncExit'] === -4;
            parityTuningPlusProgressWrite($cancelled ? 'CANCELLED' : 'COMPLETED');
            if ($cancelled) parityTuningPlusLoggerCLI(sprintf(pctT('%s Cancelled'),$cancelDescription));
            parityTuningPlusProgressAnalyze();
        }

        goto CLI_Status;

    case 'stop':
		if ($parityTuningPlusStartStop) {
			parityTuningPlusLoggerCLI(pctT('Stop array issued via Command Line'));
			exec('emcmd cmdStop=Stop');
		} else {
			parityTuningPlusLoggerCLI(pctT('Requires Unraid 6.10.3 or later'));
		}
		break;
    case 'start':
		if ($parityTuningPlusStartStop) {
			parityTuningPlusLoggerCLI(pctT('Start array issued via Command Line'));
			exec('emcmd cmdStart=Start');
		} else {
			parityTuningPlusLoggerCLI(pctT('Requires Unraid 6.10.3 or later'));
		}
		break;

    // Finally the error/usage case.   Hopefully we never get here in normal running when not using CLI
    case 'help':
    case '--help':
    default:
        parityTuningPlusLoggerCLI ('');       // Blank line to help break up debug sequences
        if (!in_array(strtolower($command), ['help','--help'], true)) {
            parityTuningPlusLoggerCLI (pctT('ERROR') . ': ' . pctT('Unrecognized option').' '.$command);
        }
        parityTuningPlusLoggerCLI (pctT('Usage') . ': ' . basename($argv[0]) . ' <' . pctT('action') . '>');
		parityTuningPlusLoggerCLI (pctT('where action is one of'));
		parityTuningPlusLoggerCLI ('  pause            ' . pctT('Pause a running array operation'));
		parityTuningPlusLoggerCLI ('  resume           ' . pctT('Resume a paused array operation'));
		parityTuningPlusLoggerCLI ('  analyze          ' . pctT('Analyze results from an array operation'));
		parityTuningPlusLoggerCLI ('  check            ' . pctT('Start a parity check with scheduled settings'));
		parityTuningPlusLoggerCLI ('  correct          ' . pctT('Start a correcting parity check'));
		parityTuningPlusLoggerCLI ('  nocorrect        ' . pctT('Start a non-correcting parity check'));
		parityTuningPlusLoggerCLI ('  status           ' . pctT('Show the status of a running parity check'));
		parityTuningPlusLoggerCLI ('  cancel           ' . pctT('Cancel a running parity check'));
		parityTuningPlusLoggerCLI ('  start            ' . pctT('Start the array'));
		parityTuningPlusLoggerCLI ('  stop             ' . pctT('Stop the array'));

		if ($parityTuningPlusCfg['parityTuningPlusLogging'] > 1) {
			parityTuningPlusLoggerCLI ('');
			parityTuningPlusLoggerCLI(pctT('The following are also available for testing purposes only'));
			parityTuningPlusLoggerCLI ('  updatecron      ' . pctT('Update cron table entries'));
			parityTuningPlusLoggerCLI ('  defaults        ' . pctT('Reset settings to defaults'));
			parityTuningPlusLoggerCLI ('  config          ' . pctT('Write current settings to syslog'));
			parityTuningPlusLoggerCLI ('  partial         ' . pctT('Start a partial parity check'));
		}

		parityTuningPlusLoggerCLI ($parityTuningPlusVersion);
		if (! $parityTuningPlusCLI) {
        	parityTuningPlusLogger (pctT('Command Line was') . ':');
        	$cmd = ''; for ($i = 0; $i < count($argv) ; $i++) $cmd .= $argv[$i] . ' ';
        	parityTuningPlusLoggerDebug($cmd);
        	parityTuningPlusProgressWrite('UNKNOWN');
        }
        break;
} // End of $command switch
spacerDebugLine(false, $command);
exit(0);

// Output a message to the console if running in CLI mode.
// An optional parameter specifies if it should also be written to the log file (and at what level)

//       ~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusLoggerCLI($string, $logging=PARITY_TUNING_PLUS_LOGGING_BASIC) {
//       ~~~~~~~~~~~~~~~~~~~~~~~
	global $parityTuningPlusCLI;
	$msg = 'CLI: ' . $string;
	switch ($logging) {
		case PARITY_TUNING_PLUS_LOGGING_BASIC:
			parityTuningPlusLogger($msg); break;
		case PARITY_TUNING_PLUS_LOGGING_DEBUG:
			parityTuningPlusLoggerDebug($msg); break;
		case PARITY_TUNING_PLUS_LOGGING_TESTING:
			parityTuningPlusLoggerTesting($msg); break;
		default:
	}
	if (($parityTuningPlusCLI)) echo $string . "\n";
}

// -------------------------------- Support Functions  -------------------------------------


// Helps break debug information into blocks to identify entries for a given entry point

//       ~~~~~~~~~~~~~~~
function spacerDebugLine($start, $cmd) {
//       ~~~~~~~~~~~~~~~
    // Not sure if this should be active at DEBUG level or only at TESTING level?
    parityTuningPlusLoggerTesting ('----------- ' . strtoupper($cmd) . ($start ? ' begin' : ' end') . ' ------');
}

// Convert an array of drive names/temperatures into a simple list for display.
//       ~~~~~~~~~~
function listDrives($drives) {
//       ~~~~~~~~~~
	global $parityTuningPlusTempUnit;
	$msg = '';
	foreach ($drives as $key => $value) {
		$msg .= $key . '(' . ($value=='*'?'*':tempInDisplayUnit($value) . $parityTuningPlusTempUnit) . ') ';
	}
    return $msg;
}

// Get the temperature in display units from Celsius

//		 ~~~~~~~~~~~~~~~~~
function tempInDisplayUnit($temp) {
//		 ~~~~~~~~~~~~~~~~~
	global $parityTuningPlusTempUnit;
	if ($parityTuningPlusTempUnit == 'C') {
		return $temp;
	}
	return round(($temp * 1.8) + 32);
}

// Write an entry to the progress file that is used to track increments
// This file is created (or added to) any time we detect a running array operation
// It is removed any time we detect there is no active operation so it contents track the operation progress.
// 
// Return values
//    1 (true)  Write was OK
//    0 (false)	Write was ignored or failed

//       ~~~~~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusProgressWrite($msg, $filename=PARITY_TUNING_PLUS_PROGRESS_FILE) {
//       ~~~~~~~~~~~~~~~~~~~~~~~~~
	global $var;
	global $parityTuningPlusAction, $parityTuningPlusCorrecting;
	
    parityTuningPlusLoggerTesting ($msg . ' record to be written');
	loadVars();	// Ensure these are up-to-date;
    global $parityTuningPlusStateValid;
    if (!$parityTuningPlusStateValid) return 0;
    // List of fields we save for progress.
	// Might not all be needed but better to have more information than necessary
	$progressFields = array('sbSynced','sbSynced2','sbSyncErrs','sbSyncExit',
	                       'mdState','mdResync','mdResyncPos','mdResyncSize','mdResyncCorr','mdResyncAction' );

    // Not strictly needed to have header but a useful reminder of the fields saved
    if (! file_exists($filename)) {
		copy (PARITY_TUNING_PLUS_EMHTTP_DISKS_FILE, PARITY_TUNING_PLUS_DISKS_FILE);
		parityTuningPlusLoggerTesting('Current disks information saved to ' . parityTuningPlusMarkerTidy(PARITY_TUNING_PLUS_DISKS_FILE));
        $line = 'type|date|time|';
        foreach ($progressFields as $name) $line .= $name . '|';
        $line .= "Description\n";
		file_put_contents($filename, $line);
		parityTuningPlusLoggerTesting ('written header record to  ' . parityTuningPlusMarkerTidy($filename));
    }
	//	It appears that under some conditions an attempt could be made to write a
	//  duplicate of the last entry.   If so ignore this attempt and return a failure.

	$lines = file($filename);
	$lineCount = count($lines);
    $last = explode('|', trim($lines[$lineCount-1]));
    $phase = static function($value) { return preg_replace('/ \([A-Z]+\)$/', '', $value); };
	if ($phase($last[0]) === $phase($msg) && count($last) >= 14
        && $last[3] === (string)$var['sbSynced'] && $last[4] === (string)$var['sbSynced2']
        && $last[6] === (string)$var['sbSyncExit'] && $last[8] === (string)$var['mdResync']) {
		parityTuningPlusLoggerTesting("record $lineCount in progress file already $msg");
		return 0;
	}
	
	// Now get on with adding new entry
    $line = $msg . '|' . date(PARITY_TUNING_PLUS_DATE_FORMAT) . '|' . time() . '|';
    foreach ($progressFields as $name) $line .= $var[$name] . '|';
    $line .= actionDescription($parityTuningPlusAction, $parityTuningPlusCorrecting, null, true, false) . "|\n";
	file_put_contents($filename, $line, FILE_APPEND | LOCK_EX);
    parityTuningPlusLoggerTesting ("written $msg as record $lineCount to " . parityTuningPlusMarkerTidy($filename));
	return 1;
}

//  Function that looks to see if a previously running array operation has finished.
//  If it has analyze the progress file to create a history record.
//  We then update the standard Unraid history file.  
//	If needed we patch an existing record.

//       ~~~~~~~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusProgressAnalyze() {
    $lock = pctCompletionLock(PARITY_TUNING_PLUS_BOOT_DIR);
    if (!$lock) {
        parityTuningPlusLoggerDebug('Completion analysis deferred: unable to acquire completion lock');
        return;
    }
    try {
        loadVars();
        global $parityTuningPlusStateValid;
        if (!$parityTuningPlusStateValid) return;
        parityTuningPlusProgressAnalyzeLocked();
    } finally {
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}

function parityTuningPlusProgressAnalyzeLocked() {
//       ~~~~~~~~~~~~~~~~~~~~~~~~~~~
	global $var;
	global $parityTuningPlusSizeInHistory;

    // Active partial checks keep diagnostic progress rather than full-check history.
    if (parityTuningPlusPartial()) {
        parityTuningPlusLoggerTesting(' ignoring progress file as was for partial check');
    	parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_PROGRESS_FILE);
		return;
    }
	// This is safety check - in ideal world we would not get here
    if (file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
	    parityTuningPlusLoggerTesting(' restart pending - so not time to analyze progress');
        return;
    }
    if (! file_exists(PARITY_TUNING_PLUS_PROGRESS_FILE)) {
        parityTuningPlusLoggerTesting('No progress file to analyze');
        return;
    }
	// This is safety check - in ideal world we would not get here
    if ($var['mdResyncPos'] != 0) {
        parityTuningPlusLoggerTesting(' array operation still running - so not time to analyze progress');
        return;
    }
    spacerDebugLine(true, 'PROGRESS_ANALYZE');
    $records = pctProgressRecords(@file(PARITY_TUNING_PLUS_PROGRESS_FILE));
    if (!$records) {
        parityTuningPlusLoggerTesting('Invalid progress protocol; preserving evidence and native notification fallback');
        return;
    }
    // Partial diagnostics remain recognizable after a missing/stale marker.
    // They cannot establish completion of a full-array check.
    foreach ($records as $record) {
        if (in_array($record[0], ['PARTIAL', 'PARTIAL STOP'], true)) {
            parityTuningPlusProgressSave();
            updateCronEntries();
            return;
        }
    }
    parityTuningPlusLoggerTesting('Previous array operation finished - analyzing progress information to create history record');

	// The following should always work unless race condition happens.
	if (! parityTuningPlusProgressSave()) {
		parityTuningPlusLoggerDebug('Abandon analyze');
		goto exit_analyze;
	}
    // Work out history record values
    $lines = file(PARITY_TUNING_PLUS_PROGRESS_SAVE);

    if ($lines == false){
        parityTuningPlusLoggerDebug('failure reading Progress file - analysis abandoned');
        goto exit_analyze;        // Cannot analyze a file that cannot be read!
    }
    // Check that there is enough information to analyze a completed operation.
    if (count($lines) < 2) {
        parityTuningPlusLoggerDebug('Progress file appears to be incomplete');
        goto exit_analyze;
    }
    $line = $lines[count($lines) - 1];
    if ((! startsWith($line,'COMPLETED')) && (!startsWith($line,'CANCELLED')) && (!startsWith($line,'ABORTED'))) {
        parityTuningPlusLoggerDebug("missing completion line in Progress file - add end TYPE and restart analyze");
        parityTuningPlusProgressWrite('COMPLETED',PARITY_TUNING_PLUS_PROGRESS_SAVE);
		$lines = file(PARITY_TUNING_PLUS_PROGRESS_SAVE);	// Reload file
    }
    $duration = $elapsed = $increments = $corrected = $size = 0;
    $thisStart = $thisFinish = $thisElapsed = $thisDuration = $thisOffset = 0;
    $lastFinish = $exitCode = $reachedSector = 0;
    $operationStart = 0;
    $countedSegments = $resumedSegments = [];

	$triggerType = '';
    $mdResyncAction = '';
	$startAction = '';		// This is to handle case where COMPLETE record has wrong type
    foreach ($lines as $line) {
    	parityTuningPlusLoggerTesting("$line");
        list($op,$stamp,$timestamp,$sbSynced,$sbSynced2,$sbSyncErrs,$sbSyncExit,,
             ,$mdResyncPos,$mdResyncSize,$mdResyncCorr,$mdResyncAction) = explode ('|',$line);
		if ($op === 'type') {
			parityTuningPlusLoggerTesting("ignore header record");
			continue;
		};
		// A progress file can have a time offset which we can determine by comparing text and binary timestamps
		// (This will only be relevant when testing Progress files submitted as part of a problem report)
        if (! $increments) {
        	$temp = strtotime(substr($stamp, 9, 3) . substr($stamp,4,4) . substr($stamp,0,5) . substr($stamp,12));
			if ($temp) {		// ignore any heading line
				$thisOffset = $temp - $timestamp;  // This allows for diagnostic files from a different timezone when debugging
				if ($thisOffset != 0) parityTuningPlusLoggerTesting ("Progress time offset = $thisOffset seconds");
			}
        }
		if ($mdResyncSize > $size) {
			parityTuningPlusLoggerTesting("Size reset from $size to $mdResyncSize");
			$size = $mdResyncSize;
		}
		if (! isset($correcting)) {
			parityTuningPlusLoggerTesting("correcting set to $mdResyncCorr");
			$correcting = $mdResyncCorr;
		}
		if ($startAction == '') $startAction = $mdResyncAction;
	
        switch ($op) {
        	case 'SCHEDULED':
        			$triggerType = $op;
        			break;
        	case 'AUTOMATIC':
			        $triggerType = $op;
					break;
        	case 'MANUAL':
        	        $triggerType = $op;
        	        break;
        	case 'UNKNOWN':
        			break;
            case 'STARTED': // First observed increment start.
            		if ($timestamp) $thisStart =  $thisFinish = $lastFinish = ($timestamp  + $thisOffset);
                    if (!$operationStart) $operationStart = $thisStart;
            		$increments = 1;		// Must be first increment!
					parityTuningPlusLoggerTesting("thisStart=$thisStart, thisFinish=$thisFinish, lastFinish=$lastFinish, thisDuration=$thisDuration"
											  . ",\n duration=$duration, elapsed=$elapsed, corrected=$corrected, exitCode=$exitCode");
                    break;

            // Preserve legacy annotations without counting the following transition twice.
			case 'RESUME (COOL)':
					break;
            case 'RESUME':
			case 'RESUME (MANUAL)':
            case 'RESUME (RESTART)':
                    if (isset($resumedSegments[$sbSynced])) break;
                    $resumedSegments[$sbSynced] = true;
                    $increments++;		// Must be starting new increment
            		if (! $thisStart) $thisStart = $timestamp + $thisOffset;
                    $thisFinish = (($sbSynced2 ==0) ? $timestamp : $sbSynced2) + $thisOffset;
                    $thisElapsed = ($lastFinish == 0) ? 0 : ($timestamp + $thisOffset - $lastFinish);
                    parityTuningPlusLoggerTesting("Resume: elapsed paused time $thisElapsed seconds");
                    $thisDuration = 0;
                    $elapsed += $thisElapsed;
                    $lastFinish = $thisFinish;
					parityTuningPlusLoggerTesting("thisStart=$thisStart, thisFinish=$thisFinish, lastFinish=$lastFinish, thisDuration=$thisDuration"
                    						  . ",\n duration=$duration, elapsed=$elapsed, corrected=$corrected, exitCode=$exitCode");
                    break;
				
            // Preserve legacy annotations without counting the following transition twice.
			case 'PAUSE (HOT)':
					break;
			case 'COMPLETED':
			case 'CANCELLED':
            case 'PAUSE':
			case 'PAUSE (MANUAL)':
            case 'PAUSE (RESTART)':

            case 'STOPPING':
					if ($reachedSector != $mdResyncPos) {
						parityTuningPlusLoggerTesting("changing reachedSector from $reachedSector to $mdResyncPos");
						$reachedSector = $mdResyncPos;
            		}
                    if ($increments == 0) $increments = 1;			// can only happen if we did not see start so assume first increment
                    if ($sbSyncErrs) $corrected = $sbSyncErrs;
                    $thisStart = $sbSynced + $thisOffset;
                    if (!$operationStart) $operationStart = $thisStart;
                    $thisFinish = (($sbSynced2 == 0) ? $timestamp : $sbSynced2) + $thisOffset;
                    $segmentDuration = max(0, $thisFinish - $thisStart);
                    $thisDuration = max(0, $segmentDuration - ($countedSegments[$sbSynced] ?? 0));
                    $countedSegments[$sbSynced] = max($segmentDuration, $countedSegments[$sbSynced] ?? 0);
                    parityTuningPlusLoggerTesting("increment duration = $thisDuration seconds");
                    $duration += $thisDuration;
                    $elapsed += $thisDuration;
                    parityTuningPlusLoggerTesting("new duration: $duration seconds, elapsed: $elapsed seconds");
                    $lastFinish = $thisFinish;
                    $exitCode = $sbSyncExit;
					parityTuningPlusLoggerTesting("thisStart=$thisStart, thisFinish=$thisFinish, lastFinish=$lastFinish, thisDuration=$thisDuration"
											  . ",\n duration=$duration, elapsed=$elapsed, corrected=$corrected, exitCode=$exitCode");
                    break;

            case 'RESTART CANCELLED':
        	case 'ABORTED': // Indicates that a parity check has been aborted due to unclean shutdown,
        					// (or Unraid version too old) so ignore this record
					$exitCode = -5;
					goto END_PROGRESS_FOR_LOOP;
            default :
                    parityTuningPlusLoggerDebug ("unexpected progress record type: $op");
                    break;
        } // end switch
    }  // end foreach
END_PROGRESS_FOR_LOOP:
    // A command hook can record a terminal row before the kernel publishes its final
    // status. Refresh only for that exact completed increment, never another run.
    if (in_array($op, ['COMPLETED', 'CANCELLED'], true)
        && (int)($var['mdResyncPos'] ?? -1) === 0
        && (int)($var['sbSynced'] ?? 0) === (int)$sbSynced
        && (int)($var['sbSynced2'] ?? 0) === (int)$sbSynced2 && (int)$sbSynced2 > 0
        && isset($var['sbSyncExit']) && preg_match('/^-?[0-9]+$/D', (string)$var['sbSyncExit'])) {
        $exitCode = (int)$var['sbSyncExit'];
    }
    switch ($exitCode) {
    	case 0:  $exitStatus = pctT("finished");
    			 break;
        case -4: $exitStatus = pctT("canceled");
                 break;
        case -5: $exitStatus = pctT("aborted");
        		 break;
        default: $exitStatus = pctT("exit code") . ": " . $exitCode;
        		 break;
    }
		
	if ($increments == 0) {
    	parityTuningPlusLoggerTesting('no increments found so no need to patch history file');
    } else if ($exitCode == -5) {
    	parityTuningPlusLoggerTesting('aborted so no need to patch history file');
    } else {
		parityTuningPlusLoggerTesting("ProgressFile start:" . date(PARITY_TUNING_PLUS_DATE_FORMAT,$thisStart) . ", finish:" . date(PARITY_TUNING_PLUS_DATE_FORMAT,$thisFinish) . ", $exitStatus");
		$unit='';
		if ($reachedSector == 0) $reachedSector = $mdResyncSize;		// position reverts to 0 at end
		global $display, $dynamixCfg;
		$display = $dynamixCfg['display'];
        if ($duration <= 0 || $thisFinish <= 0) {
            parityTuningPlusLoggerDebug('Incomplete completion timing; native notification remains available');
            goto exit_analyze;
        }
		$speed = my_scale(($reachedSector * (1024 / $duration)), $unit,1);
		$speed .= " $unit/s";
		parityTuningPlusLoggerTesting("totalSectors: $mdResyncSize, duration: $duration, speed: $speed");
        // Merge only the latest native entry for this run. The final progress status
        // and finish time are authoritative; a paused increment can have status -4.
        if (is_file(UNRAID_PARITY_HISTORY_FILE)) {
            copy(UNRAID_PARITY_HISTORY_FILE, PARITY_TUNING_PLUS_HISTORY_FILE . '.old');
            $lines = file(UNRAID_PARITY_HISTORY_FILE, FILE_SKIP_EMPTY_LINES);
            if ($lines === false) goto exit_analyze;
        } else {
            $lines = [];
        }
        $matchLine = count($lines);
        foreach ($lines as $index => $line) {
            $fields = explode('|', trim($line));
            if (count($fields) < 5) continue;
            $stamp = preg_split('/\s+/', trim($fields[0]));
            if (count($stamp) !== 4) continue;
            $logtime = strtotime($stamp[2] . ' ' . $stamp[1] . ' ' . $stamp[0] . ' ' . $stamp[3]);
            if ($logtime === false || $logtime <= $operationStart || $logtime > $thisFinish) continue;
            if (!empty($fields[5]) && trim($fields[5]) !== trim($startAction)) continue;
            $matchLine = $index;
        }
        if (isset($lines[$matchLine])) {
            $fields = explode('|', $lines[$matchLine]);
            $corrected = max($corrected, (int)$fields[4]);
        }
        if ((int)($var['sbSynced'] ?? 0) === (int)$sbSynced) {
            $corrected = max($corrected, (int)($var['sbSyncErrs'] ?? 0));
        }
        $gendate = date(PARITY_TUNING_PLUS_DATE_FORMAT, $thisFinish);
        if ($gendate[9] == '0') $gendate[9] = ' ';
		// generate replacement parity history record
		$generatedRecord = $gendate.'|'.$duration.'|'.$speed.'|'.$exitCode.'|'.$corrected.'|'.$startAction;
		// Extra field included as standard on Unraid 6.11 or later
		if ($parityTuningPlusSizeInHistory) {
			parityTuningPlusLoggerTesting('add size to history record: '. $size); 
			$generatedRecord .= '|'.$size;
		}
		$storedAction = actionDescription($startAction, $correcting, $triggerType, true, false);
		$pluginExtra='|'.$elapsed.'|'.$increments.'|'.$storedAction;
		parityTuningPlusLoggerTesting('add plugin specific fields history record: '.$pluginExtra); 
		$generatedRecord .= $pluginExtra."\n";
		parityTuningPlusLoggerTesting('log record generated from progress: '. $generatedRecord);    
		$lines[$matchLine] = $generatedRecord;
		file_put_contents(PARITY_TUNING_PLUS_HISTORY_FILE . '.log', $generatedRecord, FILE_APPEND);  // Save for debug purposes
		$history = implode('', $lines);
        if (file_put_contents(UNRAID_PARITY_HISTORY_FILE, $history, LOCK_EX) !== strlen($history)) {
            parityTuningPlusLoggerDebug('Completion history write failed; native notification remains available');
            goto exit_analyze;
        }
		// send Notification about operation
		$actionType = actionDescription($startAction, $correcting, $triggerType, true);
		$msg  = sprintf(pctT('%s %s (%d %s)'),
						$actionType, $exitStatus, $corrected, pctT('errors'));
		$desc = sprintf(pctT('%s %s, %s %s, %s %d, %s %s'),
						pctT('Elapsed Time'),this_duration($elapsed),
						pctT('Runtime'), this_duration($duration),
						pctT('Increments'), $increments,
						pctT('Average Speed'),$speed);
		parityTuningPlusLogger($msg);
		parityTuningPlusLogger($desc);
        if (sendNotification($msg, $desc, (($exitCode == 0 && $corrected == 0) ? 'normal' : 'alert'))) {
            pctCompletionReceipt(PARITY_TUNING_PLUS_BOOT_DIR, $var, $startAction, $exitCode, $corrected);
        }
		// Save new file for debugging
		copy(UNRAID_PARITY_HISTORY_FILE, PARITY_TUNING_PLUS_HISTORY_FILE . '.new'); 
	}
	updateCronEntries();
exit_analyze:
	parityTuningPlusShutdown(pctT('Array operation completed'));	// Shutdown server if set
	spacerDebugLine(false, 'PROGRESS_ANALYZE');
}

// This function renames the current progress file in preperation to analyzing it.
// It can also be useful for support purposes to have a recovrd of the actions 
// detected during the previous array operation.

//       ~~~~~~~~~~~~~~~~~~~~~~~~	
function parityTuningPlusProgressSave() {
//       ~~~~~~~~~~~~~~~~~~~~~~~~
	parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_PROGRESS_SAVE);
	if (rename (PARITY_TUNING_PLUS_PROGRESS_FILE, PARITY_TUNING_PLUS_PROGRESS_SAVE)) {
		parityTuningPlusLoggerDebug('Old progress file available as ' . PARITY_TUNING_PLUS_PROGRESS_SAVE);
		return 1;
	} else {
		// I think This should only happen if there is a race condition occuring?
		parityTuningPlusLoggerDebug('rename of progress file failed');
		return 0;
	}
}

//	Remove the last entry from the Parity History file that has been generated by a restart.
//	This should always be a 'cancelled entry) and be recent

//       ~~~~~~~~~~~~~~~~~~~~~~~~
function removeHistoryCancelEntry($expectedStart = 0, $expectedFinish = null, $expectedAction = null) {
    $lines = @file(UNRAID_PARITY_HISTORY_FILE, FILE_SKIP_EMPTY_LINES);
    if (!$lines || $expectedStart <= 0) return false;
    $fields = explode('|', trim($lines[count($lines)-1]));
    if (count($fields) < 5 || $fields[3] !== '-4' || !ctype_digit($fields[1])) return false;
    $stamp = preg_split('/\s+/', trim($fields[0]));
    if (count($stamp) !== 4) return false;
    $finish = strtotime($stamp[2].' '.$stamp[1].' '.$stamp[0].' '.$stamp[3]);
    if ($finish === false) return false;
    if ($expectedFinish !== null) {
        if ($finish !== (int)$expectedFinish) return false;
    } elseif ($finish - (int)$fields[1] !== (int)$expectedStart) return false;
    if ($expectedAction !== null && !empty($fields[5]) && trim($fields[5]) !== trim($expectedAction)) return false;
    copy(UNRAID_PARITY_HISTORY_FILE, PARITY_TUNING_PLUS_HISTORY_FILE.'.cancel');
    array_pop($lines);
    $text = implode('', $lines);
    if (file_put_contents(UNRAID_PARITY_HISTORY_FILE, $text, LOCK_EX) !== strlen($text)) return false;
    copy(UNRAID_PARITY_HISTORY_FILE, PARITY_TUNING_PLUS_HISTORY_FILE.'.cancelled');
    return true;
}

// /following 2 functions copied from parity history script

//       ~~~~~~~~
function this_plus($val, $word, $last) {
//       ~~~~~~~~
  return $val>0 ? $val.' '.$word.($last?'':', ') : '';
}

//       ~~~~~~~~~~~~
function this_duration($time) {
//       ~~~~~~~~~~~~
  if (!$time) return pctT('Unavailable');
  $days = floor($time/86400);
  $hmss = $time-$days*86400;
  $hour = floor($hmss/3600);
  $mins = ((int)($hmss/60))%60;
  $secs = $hmss%60;
  return this_plus($days,pctT('day'),($hour|$mins|$secs)==0).this_plus($hour,pctT('hr'),($mins|$secs)==0).this_plus($mins,pctT('min'),$secs==0).this_plus($secs,pctT('sec'),true);
}

function opWithErrorCount ($op) {
	global $parityTuningPlusErrors;
	return ($op . ($parityTuningPlusErrors > 0 ? " ($parityTuningPlusErrors " . pctT('errors') . ')' : ''));
}

// send a notification without checking if enabled in plugin settings
// (assuming even enabled at the system level)

//       ~~~~~~~~~~~~~~~~
function sendNotification($msg, $desc = '', $type='normal', $link='/Settings/Scheduler') {
//       ~~~~~~~~~~~~~~~~
	global $dynamixCfg, $docroot;
	global $parityTuningPlusServer;
    parityTuningPlusLogger (pctT('Send notification') . ': ' . "$msg: $desc (type=$type link=$link)");
    if (($dynamixCfg['notify']['system'] ?? '') == "" ) {
    	parityTuningPlusLogger (pctT('... but suppressed as system notifications do not appear to be enabled'));
        return false;
    } else {
        $cmd = $docroot. '/webGui/scripts/notify'
        	 . ' -e ' . (escapeshellarg(parityTuningPlusPartial() ? "Parity Check Tuning Plus Assistant" : "Parity Check Tuning Plus"))
        	 . ' -i ' . escapeshellarg($type)
	    	 . ($link == '' ? '' : ' -l ' . escapeshellarg($link))
	    	 . ' -s ' . escapeshellarg('[' . $parityTuningPlusServer . "] $msg")
	         . ($desc == '' ? '' : ' -d ' . escapeshellarg($desc));
    	parityTuningPlusLoggerTesting (pctT('... using ') . $cmd);
        exec($cmd, $output, $status);
        return $status === 0;
    }
}

// send a notification without checking if enabled.  Always add point reached.

//       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
function sendNotificationWithCompletion($op, $desc = '', $type = 'normal') {
//       ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	global $parityTuningPlusDescription;
    sendNotification ($op, $desc . (strlen($desc) > 0 ? '<br>' : '') . $parityTuningPlusDescription . parityTuningPlusCompleted(), $type);
}

// Send a notification if increment notifications enabled

//       ~~~~~~~~~~~~~~~~~~~~~
function sendArrayNotification ($op, $type='normal') {
//       ~~~~~~~~~~~~~~~~~~~~~
	global $parityTuningPlusCfg, $parityTuningPlusDescription;
    parityTuningPlusLoggerTesting("ArrayNotification($op)");
    if ($parityTuningPlusCfg['parityTuningPlusNotify'] == 0) {
        parityTuningPlusLoggerTesting (pctT('... but suppressed as notifications do not appear to be enabled for pause/resume'));
        parityTuningPlusLogger($op . ": " . $parityTuningPlusDescription
    							 	  . parityTuningPlusCompleted());		// Simply log message if not notifying
        return;
    }
    sendNotificationWithCompletion($op,'',$type);
}

// Send a notification if temperature related notifications enabled

//       ~~~~~~~~~~~~~~~~~~~~
function sendTempNotification ($op, $desc, $type='normal') {
//       ~~~~~~~~~~~~~~~~~~~~
	global $parityTuningPlusCfg;
    parityTuningPlusLoggerTesting("Heat notification message: $op: $desc");
    if ($parityTuningPlusCfg['parityTuningPlusHeatNotify'] == '0') {
        parityTuningPlusLogger($op);			// Simply log message if not notifying
        parityTuningPlusLogger($desc);
        return;
    }
    sendNotificationWithCompletion($op, $desc, $type);
}

// Suppress notifications about array operations from monitor task
// (duplicate processing from task but without notification specific steps)
// Should also stop monitor from adding parity history entries
// TODO: Check for each Unraid release that there are not version dependent changes

//       ~~~~~~~~~~~~~~~~~~~~~~~~~~~
function suppressMonitorNotification() {
//       ~~~~~~~~~~~~~~~~~~~~~~~~~~~
  global $var;

  $ram    = "/var/local/emhttp/monitor.ini";
  $rom    = "/boot/config/plugins/dynamix/monitor.ini";
  $saved  = @parse_ini_file($ram,true);
  $item = 'array';
  $name = 'parity';
  $last = $saved[$item][$name] ?? '';
  if ($var['mdResyncPos']) {
    if (!$last) {
      if (strstr($var['mdResyncAction'],"recon")) {
        $last = 'Parity sync / Data rebuild';
      } elseif (strstr($var['mdResyncAction'],"clear")) {
        $last = 'Disk clear';
      } elseif ($var['mdResyncAction']=="check") {
        $last = 'Read check';
      } elseif (strstr($var['mdResyncAction'],"check")) {
        $last = 'Parity check';
      }
      $saved[$item][$name] = $last;
    }
    parityTuningPlusLoggerTesting (sprintf(pctT('Suppressed built-in %s started notification'), $last));
  } else {
    if ($last) {
      parityTuningPlusLoggerTesting (sprintf(pctT('Suppressed built-in %s finished notification'), $last));
      unset($saved[$item][$name]);
    }
  }

  // save new status
  if ($saved) {
    $text = '';
    foreach ($saved as $item => $block) {
      if ($block) $text .= "[$item]\n";
      foreach ($block as $key => $value) $text .= "$key=\"$value\"\n";
    }
    if ($text) {
      if ($text != @file_get_contents($ram)) file_put_contents($ram, $text);
      if (!file_exists($rom) || exec("diff -q $ram $rom")) file_put_contents($rom, $text);
    } else {
      @unlink($ram);
      @unlink($rom);
    }
  }
}


// Remove the files (if present) that are used to indicate trigger type for array operation

//       ~~~~~~~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusInactiveCleanup() {
//       ~~~~~~~~~~~~~~~~~~~~~~~~~~~
	$ret  = parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_PARTIAL_FILE);
	$ret |= parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_SCHEDULED_FILE);
	$ret |= parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MANUAL_FILE);
	$ret |= parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_AUTOMATIC_FILE);
	$ret |= parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_HOT_FILE);
	$ret |= parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_SHUTDOWN_FILE);
	$ret |= parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_TIDY_FILE);
	$ret |= parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_RESTART_FILE);
	if ($ret) updateCronEntries();
	return $ret;
}

//  give the range for a partial parity check (in sectors or percent as appropriate)

//       ~~~~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusPartialRange() {
//       ~~~~~~~~~~~~~~~~~~~~~~~~
	$stored = json_decode((string)@file_get_contents(PARITY_TUNING_PLUS_PARTIAL_FILE), true);
    $range = pctT('Sectors') . ' ' . (int)($stored['startSector'] ?? 0) . '-' . (int)($stored['endSector'] ?? 0);
	return pctT('Range') . ': ' . $range;
}

//       ~~~~~~~~~~~~~~~~~~~~~
function parityTuningPlusCompleted() {
//       ~~~~~~~~~~~~~~~~~~~~~
	global $parityTuningPlusSize, $parityTuningPlusPos;

    $ret = ' ('
    	   . (($parityTuningPlusSize > 0)
    				? sprintf ("%.1f", ($parityTuningPlusPos/$parityTuningPlusSize*100)) : '0' )
    	   . '% ' .  pctT('completed') . ')';
	parityTuningPlusLoggerTesting("pos= parityTuningPlusPos, size=$parityTuningPlusSize, $ret");
	return $ret;
}

// Confirm that a pause or resume is valid according to user settings
// and the type of array operation currently in progress

//       ~~~~~~~~~~~~~~~~
function configuredAction() {
//       ~~~~~~~~~~~~~~~~
	global $parityTuningPlusCfg;
	global $parityTuningPlusAction, $parityTuningPlusDescription;

	// check configured options against array operation type in progress

    $triggerType = operationTriggerType();
    if (startsWith($parityTuningPlusAction,'recon')) {
    	$result = $parityTuningPlusCfg['parityTuningPlusRecon'];
    } else if (startsWith($parityTuningPlusAction,'clear')) {
    	$result = $parityTuningPlusCfg['parityTuningPlusClear'];
    } else if (! startsWith($parityTuningPlusAction,'check')) {
    	parityTuningPlusLoggerTesting("ERROR: unrecognized action type $parityTuningPlusAction");
    	$result = false;
    } else {
		switch ($triggerType) {
			case 'SCHEDULED':
					$result = $parityTuningPlusCfg['parityTuningPlusScheduled'];
					break;
			case 'AUTOMATIC':
					$result = $parityTuningPlusCfg['parityTuningPlusAutomatic'];
					break;
			case 'MANUAL':
					$result = $parityTuningPlusCfg['parityTuningPlusManual'];
					break;
			default:
					// Should not be possible to get here?
					parityTuningPlusLoggerTesting("ERROR: unrecognized trigger type '$triggerType' for $parityTuningPlusAction");
					$result = false;
					break;
		}
	}
	parityTuningPlusLoggerTesting("configuredAction()=$result ($parityTuningPlusDescription)");
    return $result;
}
																																		
// Check if an array operation is currently in progress
// Returns true even if it is currently paused

//       ~~~~~~~~~~~~~~~~~~~~~~
function isArrayOperationActive() {
//       ~~~~~~~~~~~~~~~~~~~~~~
	global $parityTuningPlusActive;
	global $parityTuningPlusPos;

	parityTuningPlusLoggerTesting("isArrayOperationActive - parityTuningPlusActive:$parityTuningPlusActive, parityTuningPlusPos:$parityTuningPlusPos");
	if (file_exists(PARITY_TUNING_PLUS_RESTART_FILE)) {
		parityTuningPlusLoggerTesting('  restart pending so treat as array operation active');
	} else if (!$parityTuningPlusActive) {
		parityTuningPlusLoggerTesting(pctT('No action outstanding'));
		parityTuningPlusLoggerTesting('isArrayOperationActive()=false');
		parityTuningPlusProgressAnalyze();
		return false;
	} 
	parityTuningPlusLoggerTesting('isArrayOperationActive()=true');
	return true;
}

// Determine if the current time is within a period specified for increments to be active
// Daily/weekly windows use their actual clock interval; custom windows follow cron markers.

//       ~~~~~~~~~~~~~~
function isActivePeriod($action = null) {
    global $parityTuningPlusCfg, $parityTuningPlusAction, $parityTuningPlusActive;
    $action = $action ?? $parityTuningPlusAction;
    if (!isRunInIncrements($action)) return 1;
    if (!$parityTuningPlusActive) return 0;
    if (($parityTuningPlusCfg['parityTuningPlusFrequency'] ?? '0') === '1') {
        return file_exists(PARITY_TUNING_PLUS_INCREMENT_FILE) ? 1 : 0;
    }
    $weekly = ($parityTuningPlusCfg['parityTuningPlusFrequency'] ?? '0') === '2';
    $edges = [];
    foreach (['Resume', 'Pause'] as $edge) {
        $values = [];
        foreach (['Hour'=>23, 'Minute'=>59] + ($weekly ? ['Day'=>6] : []) as $field => $maximum) {
            $value = (string)($parityTuningPlusCfg['parityTuningPlus'.$edge.$field] ?? '');
            if (!ctype_digit($value) || (int)$value > $maximum) return 0;
            $values[$field] = (int)$value;
        }
        $edges[] = ($values['Day'] ?? 0) * 1440 + $values['Hour'] * 60 + $values['Minute'];
    }
    [$resume, $pause] = $edges;
    if ($resume === $pause) return 0;
    $now = ($weekly ? (int)date('w') * 1440 : 0) + (int)date('H') * 60 + (int)date('i');
    return ($resume < $pause ? $now >= $resume && $now < $pause : $now >= $resume || $now < $pause) ? 1 : 0;
}

// Determine if the given operation type is set to be run in run in increments.

//       ~~~~~~~~~~~~~~~~~
function isRunInIncrements($action) {
//       ~~~~~~~~~~~~~~~~~
	global $parityTuningPlusCfg;

	$trigger = operationTriggerType();
	$action = strtok($action,' ');
	switch (strtolower($action)) {
		case 'recon':	$ret = ($parityTuningPlusCfg['parityTuningPlusRecon'] === '1') ? 1 : 0;
						break;
		case 'clear':   $ret = ($parityTuningPlusCfg['parityTuningPlusClear'] === '1') ? 1 : 0;
						break;
		case 'check':   
						switch (strtoupper($trigger)) {
							case 'SCHEDULED': 
								$ret=($parityTuningPlusCfg['parityTuningPlusScheduled'] === '1') ? 1 : 0;
								break;
							case 'MANUAL':	  
								$ret=($parityTuningPlusCfg['parityTuningPlusManual'] === '1') ? 1 : 0;
								break;
							case 'AUTOMATIC': 
								$ret=($parityTuningPlusCfg['parityTuningPlusAutomatic'] === '1') ? 1 : 0;
								break;
							default:
								parityTuningPlusLoggerTesting("Unexpected trigger: $trigger");
								$ret = 0;
								break;
						}
						break;
		default:
						parityTuningPlusLoggerTesting("Unexpected action: $action");
						$ret = 0; 
						break;
	}
	parityTuningPlusLoggerTesting("isRunInIncrements($action)=".$ret." (trigger type=$trigger)" );
	return $ret;
}

// Check if the operation type is being run in increments and if so if we are in that period.

//		 ~~~~~~~~~~~~~~~~~
function isIncrementActive($action) {
//		 ~~~~~~~~~~~~~~~~~
	parityTuningPlusLoggerTesting("isIncrementActive($action)");
	if (!isRunInIncrements($action)) return 1;	// If no increments used always assume true
	return isActivePeriod($action);
}


//       ~~~~~~~~~~~~~~~~~
function updateCronEntries() {
//       ~~~~~~~~~~~~~~~~~
	global $parityTuningPlusCfg, $parityTuningPlusActive;
	
	parityTuningPlusLoggerTesting("Creating required cron entries");
	$lines = [];
	$lines[] = "# Generated schedules for " . PARITY_TUNING_PLUS_PLUGIN . "\n";

	// Handle pause/resume of any operation type that has been specified to use increments
	if ($parityTuningPlusCfg['parityTuningPlusScheduled'] 
	 || $parityTuningPlusCfg['parityTuningPlusManual']
	 || $parityTuningPlusCfg['parityTuningPlusAutomatic']
	 || $parityTuningPlusCfg['parityTuningPlusClear']
	 || $parityTuningPlusCfg['parityTuningPlusRecon']) {
//
		$pausetime = '0';
		$resumetime = '0';
		switch ($parityTuningPlusCfg['parityTuningPlusFrequency']) {
			case 1: // custom
				$resumetime = $parityTuningPlusCfg['parityTuningPlusResumeCustom'];
				$pausetime  = $parityTuningPlusCfg['parityTuningPlusPauseCustom'];
				break;
			case 0: // daily
				$resumetime = $parityTuningPlusCfg['parityTuningPlusResumeMinute'] . ' '
							. $parityTuningPlusCfg['parityTuningPlusResumeHour'] . ' * * *';
				$pausetime  = $parityTuningPlusCfg['parityTuningPlusPauseMinute'] . ' '
							. $parityTuningPlusCfg['parityTuningPlusPauseHour'] . ' * * *';
				break;
			case 2: // weekly
				$resumetime = $parityTuningPlusCfg['parityTuningPlusResumeMinute'].' '
							. $parityTuningPlusCfg['parityTuningPlusResumeHour'].' * * '
							. $parityTuningPlusCfg['parityTuningPlusResumeDay'];
				$pausetime  = $parityTuningPlusCfg['parityTuningPlusPauseMinute'].' '
							. $parityTuningPlusCfg['parityTuningPlusPauseHour'].' * * '
							. $parityTuningPlusCfg['parityTuningPlusPauseDay'];
				break;
			default:  // Error?
				parityTuningPlusLoggerDebug("Invalid frequency value: ".$parityTuningPlusCfg['parityTuningPlusFrequency']);
				return false;
		}
        $resumetime = pctCronExpression($resumetime);
        $pausetime = pctCronExpression($pausetime);
        if ($resumetime === false || $pausetime === false || $resumetime === $pausetime) {
            parityTuningPlusLoggerTesting('Invalid schedule; preserving existing cron jobs');
            return false;
        }
		$lines[] = "$resumetime " . PARITY_TUNING_PLUS_PHP_FILE . ' "resume" &> /dev/null' . "\n";
		$lines[] = "$pausetime " . PARITY_TUNING_PLUS_PHP_FILE . ' "pause" &> /dev/null' . "\n";
	 parityTuningPlusLoggerDebug (sprintf(pctT('Created cron entry for scheduled pause and resume'),$pausetime,$resumetime));
	}

	
	// Decide on monitor frequency 

	if (parityTuningPlusPartial()) {
		parityTuningPlusLoggerTesting("Creating parity assistance cron entry");
		// Partial checks (default = 1 minute)
		$frequency=$parityTuningPlusCfg['parityTuningPlusMonitorPartial'];
	} else {
		if ($parityTuningPlusActive) {
			// Array operation already active (default = 6 minutes)
			$frequency=$parityTuningPlusCfg['parityTuningPlusMonitorBusy'];
		} else if ($parityTuningPlusCfg['parityTuningPlusHeat'] 
				|| $parityTuningPlusCfg['parityTuningPlusHeatShutdown']) {
			// check temperatures (default = 7 minutes)
			$frequency=$parityTuningPlusCfg['parityTuningPlusMonitorHeat'];
		} else {
			// Default if not monitoring more frequently for other 
			// reasons (default = 17 minutes)
			$frequency=$parityTuningPlusCfg['parityTuningPlusMonitorDefault'];
		}
	}
    if (!ctype_digit((string)$frequency) || (int)$frequency < 1 || (int)$frequency > 59) {
        parityTuningPlusLoggerTesting('Invalid monitor interval; preserving existing cron jobs');
        return false;
    }
	parityTuningPlusLoggerDebug (sprintf(pctT('Created cron entry for %s interval monitoring'), $frequency.' '.pctT('minute')));
	$lines[] = "*/$frequency * * * * " . PARITY_TUNING_PLUS_PHP_FILE . ' "monitor" &>/dev/null' . "\n\n";
    $previous = (string)@file_get_contents(PARITY_TUNING_PLUS_CRON_FILE);
    $next = implode('', $lines);
    $temporary = tempnam(dirname(PARITY_TUNING_PLUS_CRON_FILE), '.pct-cron-');
    if ($temporary === false) return false;
    if (file_put_contents($temporary, $next, LOCK_EX) !== strlen($next)
        || !rename($temporary, PARITY_TUNING_PLUS_CRON_FILE)) {
        @unlink($temporary);
        return false;
    }
    preg_match_all('/^[^\r\n]* "(?:resume|pause)"[^\r\n]*$/m', $previous, $oldWindow);
    preg_match_all('/^[^\r\n]* "(?:resume|pause)"[^\r\n]*$/m', $next, $newWindow);
    if ($oldWindow[0] !== $newWindow[0]) parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_INCREMENT_FILE);
	parityTuningPlusLoggerDebug(sprintf(pctT('Updated cron settings are in %s'),PARITY_TUNING_PLUS_CRON_FILE));
	// Activate any changes
	exec("/usr/local/sbin/update_cron");
    return true;
}

//		 ~~~~~~~~~~~~~~~~~
function parityTuningPlusPause($reason, $notifyFlag) {
//		 ~~~~~~~~~~~~~~~~~

    global $parityTuningPlusErrors, $parityTuningPlusActive, $parityTuningPlusPaused;
    if (!$parityTuningPlusActive) return false;
    if ($parityTuningPlusPaused) return true;
	parityTuningPlusLoggerTesting("parityTuningPlusPause($reason, $notifyFlag?'true':'false''), Errors so far: $parityTuningPlusErrors");
    exec('/usr/local/sbin/mdcmd "nocheck" "PAUSE"', $output, $status);
	loadVars(5);
    if ($status !== 0 || !$parityTuningPlusActive || !$parityTuningPlusPaused) {
        parityTuningPlusLoggerTesting('Pause request did not reach the paused state');
        return false;
    }
    parityTuningPlusProgressWrite('PAUSE');
	if ($notifyFlag) {
		sendArrayNotification( pctT('Paused').': '.ucwords($reason),$parityTuningPlusErrors == 0 ? 'normal' : 'warning');
	}
	suppressMonitorNotification();
    return true;
}

//		 ~~~~~~~~~~~~~~~~~~
function parityTuningPlusResume($notifyFlag) {
//		 ~~~~~~~~~~~~~~~~~~

    global $parityTuningPlusErrors, $parityTuningPlusActive, $parityTuningPlusPaused;
    if (!$parityTuningPlusActive) return false;
    if (!$parityTuningPlusPaused) return true;
	parityTuningPlusLoggerTesting("parityTuningPlusResume($notifyFlag?'true':'false'), Errors so far: $parityTuningPlusErrors");
	
    exec('/usr/local/sbin/mdcmd "check" "resume"', $output, $status);
	loadVars(5);
    if ($status !== 0 || !$parityTuningPlusActive || $parityTuningPlusPaused) {
        parityTuningPlusLoggerTesting('Resume request did not reach the running state');
        return false;
    }
    parityTuningPlusProgressWrite('RESUME');
	parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_MOVER_FILE);
	parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_BACKUP_FILE);
	if ($notifyFlag) {
		sendArrayNotification(pctT('Resumed'),$parityTuningPlusErrors == 0 ? 'normal' : 'warning');
	}
	suppressMonitorNotification();
    return true;
}

//	Function to initiate a tidy (hopefully) shutdown of the server
//  (as a safety check make sure option has not been uinset).

//		 ~~~~~~~~~~~~~~~~~~~~	
function parityTuningPlusShutdown($msg, $critical = false) {
//		 ~~~~~~~~~~~~~~~~~~~~
	global $parityTuningPlusCfg;
	if ($critical || file_exists(PARITY_TUNING_PLUS_SHUTDOWN_FILE)) {
		parityTuningPlusInactiveCleanup();
        $parityTuningPlusCfg = parse_plugin_cfg(PARITY_TUNING_PLUS_PLUGIN);
        if ($parityTuningPlusCfg[$critical ? 'parityTuningPlusHeatShutdown' : 'parityTuningPlusShutdown']) {
			sendNotification (pctT('Array shutdown'), $msg, 'alert');		
			sleep (30);	// add a delay for notification to be actioned
            $parityTuningPlusCfg = parse_plugin_cfg(PARITY_TUNING_PLUS_PLUGIN);
            if (!$parityTuningPlusCfg[$critical ? 'parityTuningPlusHeatShutdown' : 'parityTuningPlusShutdown']) {
                sendNotification(pctT('Shutdown aborted'), $msg, 'alert');
                return;
            }
			parityTuningPlusLogger (pctT('Starting Shutdown'));
			exec('/sbin/shutdown -h -P now');
		} else {
			sendNotification (pctT('Shutdown aborted'), $msg, 'alert');
		}
	}
}

// Check the stored disk information against the current assignments
//		0 (false)	Disks appear unchanged
//		-1			New disk present (New Config used?)
//		1			Disks changed in some other way

function disksChanged() {
    $normalize = function ($values) {
        if (!is_array($values)) return null;
        $result = [];
        foreach ($values as $key => $drive) {
            $name = $drive['name'] ?? $key;
            if (!preg_match('/^(parity[0-9]*|disk[0-9]+)$/D', $name)) continue;
            if (startsWith($drive['status'] ?? '', 'DISK_NP')) continue;
            if (!isset($drive['id'], $drive['size'], $drive['status']) || $drive['id'] === '') return null;
            $result[$name] = [(string)$drive['id'], (string)$drive['size'], (string)$drive['status']];
        }
        ksort($result);
        return $result ?: null;
    };
    $current = $normalize(@parse_ini_file(PARITY_TUNING_PLUS_EMHTTP_DISKS_FILE, true));
    $old = $normalize(@parse_ini_file(PARITY_TUNING_PLUS_DISKS_FILE, true));
    $changed = $current === null || $old === null || $current !== $old ? 1 : 0;
    foreach (($current ?? []) as $drive) if ($drive[2] === 'DISK-NEW') $changed = -1;
    if ($changed) parityTuningPlusDeleteFile(PARITY_TUNING_PLUS_AUTOMATIC_FILE);
    return $changed;
}
