<?php
// SPDX-License-Identifier: GPL-2.0-only
// Copyright 2026, alexphillips-dev.
require_once __DIR__ . '/parity.check.tuning.plus.temperature.php';

/** Identify a mover process, rather than a command merely mentioning mover. */
function pctMoverCommand(array $args) {
    $names = ['mover', 'mover.old', 'age_mover', 'share_mover'];
    if (!$args) return false;
    if (in_array(basename($args[0]), $names, true)) return true;
    if (!in_array(basename($args[0]), ['bash', 'sh', 'dash', 'ash', 'ksh'], true)) return false;
    foreach (array_slice($args, 1) as $arg) {
        if ($arg === '--') continue;
        if (isset($arg[0]) && $arg[0] === '-') {
            // A shell command string is not a mover script invocation.
            if (strpos($arg, 'c') !== false) return false;
            continue;
        }
        return in_array(basename($arg), $names, true);
    }
    return false;
}

function isMoverRunning($pidFile = '/var/run/mover.pid', $procRoot = '/proc') {
    $pid = trim((string)@file_get_contents($pidFile));
    if (!preg_match('/^[1-9][0-9]*$/D', $pid) || (string)(int)$pid !== $pid) return false;
    $command = @file_get_contents($procRoot . '/' . $pid . '/cmdline');
    if ($command === false || $command === '') return false;
    $args = explode("\0", rtrim($command, "\0"));
    // Recheck ownership of the PID file if mover exited/restarted while reading procfs.
    return pctMoverCommand($args) && trim((string)@file_get_contents($pidFile)) === $pid;
}

function isBackupRunning() {
    return file_exists('/tmp/appdata.backup/running')
        || file_exists('/tmp/ca.backup2/tempFiles/backupInProgress')
        || file_exists('/tmp/ca.backup2/tempFiles/restoreInProgress');
}

function pctBackgroundHeatBlock() {
    global $parityTuningPlusCfg, $dynamixCfg, $disks;
    if (($parityTuningPlusCfg['parityTuningPlusHeat'] ?? '0') !== '1') return false;
    $hot = [];
    foreach (($disks ?? []) as $name => $disk) {
        if (!preg_match('/^(parity\d*|disk\d+)$/D', $name) || !is_numeric($disk['temp'] ?? null)) continue;
        $warning = pctDiskTemperatureLimit($disk, $dynamixCfg['display'] ?? [], 'hotTemp');
        $threshold = $warning - (float)$parityTuningPlusCfg['parityTuningPlusHeatHigh'];
        if ($warning > 0 && (float)$disk['temp'] >= $threshold) $hot[] = $name;
    }
    if ($hot) {
        // Transfer the pause to the existing temperature handler, which waits for cooling.
        file_put_contents(PARITY_TUNING_PLUS_HOT_FILE, implode(' ', $hot), LOCK_EX);
        return true;
    }
    return false;
}

/** One snapshot of both tasks prevents an early resume while another task is active. */
function pctHandleBackgroundTasks(array $tasks) {
    global $parityTuningPlusCfg, $parityTuningPlusActive, $parityTuningPlusPaused, $parityTuningPlusAction;
    $notify = ($parityTuningPlusCfg['parityTuningPlusBackground'] ?? '0') === '1';
    $owned = false;
    $blocking = [];
    foreach ($tasks as &$task) {
        $task['prior'] = is_file($task['marker'])
            ? json_decode((string)file_get_contents($task['marker']), true) : null;
        $owned = $owned || !empty($task['prior']['paused']);
        $task['enabled'] = ($parityTuningPlusCfg[$task['config']] ?? '0') === '1';
        if ($task['running'] && $task['enabled']) $blocking[] = $task['label'];
    }
    unset($task);
    if (!$parityTuningPlusActive) {
        foreach ($tasks as $task) parityTuningPlusDeleteFile($task['marker']);
        return false;
    }
    if ($blocking && !$parityTuningPlusPaused) {
        parityTuningPlusPause(sprintf(pctT('Background activity: %s'), implode(', ', $blocking)), $notify);
        $owned = (bool)$parityTuningPlusActive && (bool)$parityTuningPlusPaused;
    }
    foreach ($tasks as $task) {
        if ($task['running']) {
            $started = is_array($task['prior']);
            $notified = !empty($task['prior']['notified']);
            if (!$started && $notify) {
                sendNotification(sprintf(pctT('%s running'), $task['label']));
                $notified = true;
            }
            // Never acquire ownership of a pause that was already manual/temperature-driven.
            $state = ['paused' => $owned && $task['enabled'], 'notified' => $notified];
            if ($state !== $task['prior']) {
                file_put_contents($task['marker'], json_encode($state), LOCK_EX);
            }
        } elseif (is_file($task['marker'])) {
            parityTuningPlusDeleteFile($task['marker']);
            if ($notify && !empty($task['prior']['notified'])) {
                sendNotificationWithCompletion(sprintf(pctT('%s no longer running'), $task['label']));
            }
        }
    }
    if ($blocking) return true;
    if ($owned && $parityTuningPlusPaused
        && !file_exists(PARITY_TUNING_PLUS_HOT_FILE)
        && !file_exists(PARITY_TUNING_PLUS_RESTART_FILE)
        && !parityTuningPlusPartial() && !pctBackgroundHeatBlock()) {
        if (isIncrementActive($parityTuningPlusAction)) {
            parityTuningPlusResume($notify);
            if ($parityTuningPlusActive && $parityTuningPlusPaused) {
                foreach ($tasks as $task) {
                    if (!empty($task['prior']['paused'])) {
                        file_put_contents($task['marker'], json_encode(['paused'=>true, 'notified'=>false]), LOCK_EX);
                        break;
                    }
                }
            }
        } elseif ($notify) {
            sendNotificationWithCompletion(pctT('Array operation not resumed - outside increment window'));
        }
    }
    return false;
}

function backGroundTaskRunning() {
    $lock = @fopen(PARITY_TUNING_PLUS_FILE_PREFIX . 'background.lock', 'c');
    if ($lock === false || !flock($lock, LOCK_EX)) {
        if (is_resource($lock)) fclose($lock);
        parityTuningPlusLogger('Unable to lock background task state');
        return true;
    }
    try {
        return pctHandleBackgroundTasks([
            ['config' => 'parityTuningPlusMover', 'label' => pctT('mover'),
             'marker' => PARITY_TUNING_PLUS_MOVER_FILE, 'running' => isMoverRunning()],
            ['config' => 'parityTuningPlusBackup', 'label' => pctT('backup'),
             'marker' => PARITY_TUNING_PLUS_BACKUP_FILE, 'running' => isBackupRunning()],
        ]);
    } finally {
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}
