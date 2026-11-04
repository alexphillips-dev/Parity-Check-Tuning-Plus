<?php
/* Parity Check Tuning Plus completion notification coordination.
 * Copyright 2026 alexphillips-dev. Distributed under GPL version 2.
 */

function pctCompletionLock($directory) {
    $lock = @fopen($directory . '/parity.check.tuning.plus.completion.lock', 'c');
    if (!$lock) return false;
    if (!flock($lock, LOCK_EX)) { fclose($lock); return false; }
    return $lock;
}

/** Validate the shared progress protocol before claiming notification ownership or analysis. */
function pctProgressRecords($lines) {
    if (!is_array($lines)) return false;
    $records = [];
    foreach ($lines as $line) {
        if (trim($line) === '') continue;
        $fields = explode('|', rtrim($line, "\r\n"));
        if ($fields[0] === 'type') continue;
        if (count($fields) < 14 || count($fields) > 15 || (count($fields) === 15 && $fields[14] !== '')
            || !preg_match('/^[A-Z]+(?: [A-Z]+| \([A-Z]+\))*$/D', $fields[0])) return false;
        foreach ([2,3,4,5,6,8,9,10,11] as $index) {
            $value = $fields[$index];
            $canonical = ltrim($value, '0');
            if ($index === 6 && substr($value, 0, 1) === '-') $canonical = '-'.ltrim(substr($value, 1), '0');
            if (!preg_match($index === 6 ? '/^-?[0-9]+$/D' : '/^[0-9]+$/D', $value)
                || (string)(int)$value !== ($canonical === '' || $canonical === '-' ? '0' : $canonical)) return false;
        }
        if (!in_array($fields[7], ['STARTED','STOPPED'], true) || (int)$fields[2] <= 0) return false;
        $records[] = $fields;
    }
    return $records ?: false;
}

function pctParityKind($action) {
    $parts = preg_split('/\s+/', trim((string)$action));
    switch ($parts[0]) {
        case 'check': return count($parts) > 1 ? 'paritycheck' : 'readcheck';
        case 'recon': return ($parts[1] ?? '') === 'P' ? 'paritysync' : 'datarebuild';
        case 'clear': return 'diskclear';
        default: return '';
    }
}

// Native monitor subjects/events are protocol strings, independent of GUI locale.
function pctNativeFinishNotice(array $arguments) {
    $options = [];
    for ($i = 0; $i < count($arguments); $i++) {
        $argument = $arguments[$i];
        if ($argument === 'add') continue;
        if (in_array($argument, ['-x', '-t', '-b'], true)) continue;
        if (!in_array($argument, ['-e', '-s', '-d', '-i', '-m', '-l', '-r'], true)
            || !isset($arguments[$i + 1]) || isset($options[$argument])) return '';
        $options[$argument] = $arguments[++$i];
    }
    $event = $options['-e'] ?? '';
    if (substr($event, 0, 7) !== 'Unraid ') return '';
    $name = substr($event, 7);
    $kind = strtolower(str_replace(['-', ' '], '', $name));
    if (!in_array($kind, ['paritycheck', 'readcheck', 'paritysync', 'datarebuild', 'diskclear', 'paritysync/datarebuild'], true)) return '';
    if (!preg_match('/^Notice \[[^\]\r\n]+\] - ' . preg_quote($name, '/') . ' finished \(([0-9]+) errors\)$/D', $options['-s'] ?? '', $match)) return null;
    return ['kind' => $kind, 'errors' => (int)$match[1]];
}

function pctSameParityKind($first, $second) {
    if ($first === $second) return true;
    return $first === 'paritysync/datarebuild' && in_array($second, ['paritysync', 'datarebuild'], true);
}

function pctCompletionReceipt($directory, array $var, $action, $status, $errors) {
    // Never hide a kernel error by trusting a contradictory plugin result.
    if ((int)($var['mdResyncPos'] ?? 0) !== 0 || (int)($var['sbSynced'] ?? 0) <= 0
        || (int)($var['sbSynced2'] ?? 0) <= 0 || !isset($var['sbSyncExit'])
        || (int)$var['sbSyncExit'] !== (int)$status || !pctParityKind($action)) return false;
    $receipt = ['start' => (int)$var['sbSynced'], 'end' => (int)$var['sbSynced2'],
                'status' => (int)$status, 'errors' => (int)$errors, 'kind' => pctParityKind($action), 'created' => time()];
    $path = $directory . '/parity.check.tuning.plus.completion.json';
    $temporary = @tempnam($directory, '.completion-');
    if (!$temporary) return false;
    $text = json_encode($receipt) . "\n";
    $written = @file_put_contents($temporary, $text) === strlen($text) && @rename($temporary, $path);
    if (file_exists($temporary)) @unlink($temporary);
    return $written;
}

// Called under the same lock as completion analysis. Unknown state passes through.
function pctOwnsNativeFinish(array $notice, $directory, array $var, $now = null) {
    $kind = $notice['kind'];
    if (!$kind || !ctype_digit((string)($var['sbSynced'] ?? '')) || (int)$var['sbSynced'] <= 0) return false;
    $now = $now ?? time();
    $receipt = json_decode((string)@file_get_contents($directory . '/parity.check.tuning.plus.completion.json'), true);
    $valid = is_array($receipt) && is_string($receipt['kind'] ?? null);
    foreach (['start', 'end', 'status', 'errors', 'created'] as $key) $valid = $valid && isset($receipt[$key]) && is_int($receipt[$key]);
    if ($valid && $now >= $receipt['created']
        && ($var['mdResyncPos'] ?? null) === '0'
        && (int)$var['sbSynced'] === $receipt['start'] && isset($var['sbSynced2'], $var['sbSyncExit'])
        && ctype_digit((string)$var['sbSynced2']) && preg_match('/^-?[0-9]+$/D', (string)$var['sbSyncExit'])
        && (int)$var['sbSynced2'] === $receipt['end'] && (int)$var['sbSyncExit'] === $receipt['status']
        && $notice['errors'] <= $receipt['errors'] && isset($var['sbSyncErrs'])
        && ctype_digit((string)$var['sbSyncErrs']) && (int)$var['sbSyncErrs'] <= $receipt['errors']
        && pctSameParityKind($kind, $receipt['kind'])) return true;

    $lines = @file($directory . '/parity.check.tuning.plus.progress', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $records = pctProgressRecords($lines);
    if (!$records) return false;
    // Last complete record identifies the tracked kernel increment; another run cannot borrow its ownership.
    $fields = $records[count($records) - 1];
    return !in_array($fields[0], ['ABORTED', 'RESTART CANCELLED'], true)
        && (int)$fields[3] === (int)$var['sbSynced'] && pctSameParityKind($kind, pctParityKind($fields[12]));
}
