<?php
// SPDX-License-Identifier: GPL-2.0-only
// Copyright 2026 alexphillips-dev.

// Match native Unraid inheritance: explicit nonnegative per-disk value (zero disables),
// NVMe-reported limits, SSD global override, then the general global setting.
function pctDiskTemperatureLimit(array $disk, array $display, $field) {
    if (is_numeric($disk[$field] ?? null) && (float)$disk[$field] >= 0) return (float)$disk[$field];
    if (($disk['transport'] ?? '') === 'nvme' && function_exists('get_nvme_info')) {
        $limits = get_nvme_info($disk['device'] ?? '', 'temp');
        $value = $limits[$field === 'hotTemp' ? 0 : 1] ?? -1;
        if (is_numeric($value) && $value >= 0) return (float)$value;
    }
    $key = $field === 'hotTemp' ? 'hot' : 'max';
    if (($disk['rotational'] ?? '1') == '0' && is_numeric($display[$key.'ssd'] ?? null) && $display[$key.'ssd'] >= 0) {
        return (float)$display[$key.'ssd'];
    }
    return is_numeric($display[$key] ?? null) ? (float)$display[$key] : ($key === 'hot' ? 45 : 55);
}

function pctCriticalTemperatureDrives(array $disks, array $display, $offset) {
    $critical = [];
    foreach ($disks as $key => $disk) {
        $name = $disk['name'] ?? $key;
        if ($name === 'flash' || strpos($disk['status'] ?? '', 'DISK_NP') === 0 || !is_numeric($disk['temp'] ?? null)) continue;
        $limit = pctDiskTemperatureLimit($disk, $display, 'maxTemp');
        if ($limit > 0 && (float)$disk['temp'] >= $limit - (float)$offset) $critical[$name] = $disk['temp'];
    }
    return $critical;
}
