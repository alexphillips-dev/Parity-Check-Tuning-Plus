<?php
// SPDX-License-Identifier: GPL-2.0-only
// Copyright 2026, alexphillips-dev.

/** Validate submitted values independently of the browser before invoking mdcmd. */
function pctPartialCheckRange(array $cfg, $totalSectors) {
    $totalSectors = (int)$totalSectors;
    if ($totalSectors <= 0) throw new InvalidArgumentException('Array size is not available');
    $type = $cfg['parityProblemPlusType'] ?? '';
    if ($type === 'sector') {
        $values = [];
        foreach (['Start', 'End'] as $edge) {
            $value = (string)($cfg['parityProblemPlus' . $edge . 'Sector'] ?? '');
            if (!preg_match('/^(0|[1-9][0-9]*)$/D', $value) || (float)$value > $totalSectors) {
                throw new InvalidArgumentException('Sector endpoints must be whole numbers within the disk');
            }
            $values[] = (int)$value;
        }
        [$start, $end] = $values;
    } elseif ($type === 'percent') {
        $values = [];
        foreach (['Start', 'End'] as $edge) {
            $value = (string)($cfg['parityProblemPlus' . $edge . 'Percent'] ?? '');
            if (!preg_match('/^(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)$/D', $value)
                || !is_finite((float)$value) || (float)$value > 100) {
                throw new InvalidArgumentException('Percentage endpoints must be between 0 and 100');
            }
            $values[] = (float)$value;
        }
        $start = (int)floor($values[0] / 100 * $totalSectors);
        $end = (int)ceil($values[1] / 100 * $totalSectors);
    } else {
        throw new InvalidArgumentException('Choose sectors or percentages');
    }
    if ($end <= $start) throw new InvalidArgumentException('The end point must be larger than the start');
    $correct = (string)($cfg['parityProblemPlusCorrect'] ?? '');
    if (!in_array($correct, ['0', '1'], true)) throw new InvalidArgumentException('Choose whether to write corrections');
    return ['startSector' => $start - ($start % 8), 'endSector' => $end, 'correct' => $correct === '1'];
}

function pctPartialEndSector() {
    $range = json_decode((string)@file_get_contents(PARITY_TUNING_PLUS_PARTIAL_FILE), true);
    return (int)($range['endSector'] ?? 0);
}

function pctPartialOwner(array $var) {
    $range = json_decode((string)@file_get_contents(PARITY_TUNING_PLUS_PARTIAL_FILE), true);
    if (!is_array($range)) return false;
    foreach (['startSector','endSector','kernelStart','size'] as $key) {
        if (!isset($range[$key]) || !is_int($range[$key]) || $range[$key] < 0) return false;
    }
    if (!isset($range['correct']) || !is_bool($range['correct']) || $range['endSector'] <= $range['startSector']
        || $range['kernelStart'] <= 0 || $range['kernelStart'] !== (int)($var['sbSynced'] ?? 0)
        || $range['size'] !== (int)($var['mdResyncSize'] ?? 0)
        || $range['correct'] !== ((int)($var['mdResyncCorr'] ?? -1) === 1)
        || !preg_match('/^check [PQ](?: [PQ])?$/D', (string)($var['mdResyncAction'] ?? ''))) return false;
    return $range;
}
