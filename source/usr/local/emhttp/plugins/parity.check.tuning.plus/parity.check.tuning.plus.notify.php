#!/usr/bin/php
<?php
/* Narrow native parity-finish notification guard; all other requests pass through.
 * Copyright 2026 alexphillips-dev. Distributed under GPL version 2.
 */
require_once __DIR__ . '/parity.check.tuning.plus.completion.php';

$arguments = array_slice($argv, 1);
$native = '/usr/local/emhttp/webGui/scripts/notify.parity.check.tuning.plus.orig';
if (!is_file($native) || !is_executable($native)) {
    fwrite(STDERR, "Parity Check Tuning Plus: native notification backup is unavailable.\n");
    exit(1);
}
$notice = pctNativeFinishNotice($arguments);
if ($notice) {
    $directory = '/boot/config/plugins/parity.check.tuning.plus';
    $lock = pctCompletionLock($directory);
    if ($lock) {
        $var = @parse_ini_file('/var/local/emhttp/var.ini', false, INI_SCANNER_RAW);
        $owned = is_array($var) && pctOwnsNativeFinish($notice, $directory, $var);
        flock($lock, LOCK_UN);
        fclose($lock);
        if ($owned) exit(0);
    }
}
$command = implode(' ', array_map('escapeshellarg', array_merge([$native], $arguments)));
passthru($command, $status);
exit($status);
