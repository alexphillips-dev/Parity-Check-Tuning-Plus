<?php
// SPDX-License-Identifier: GPL-2.0-only
// Copyright 2026, alexphillips-dev.

function pctLocaleDefinition() {
    static $metadata;
    if ($metadata === null) $metadata = json_decode(file_get_contents(__DIR__ . '/locales/locales.json'), true);
    $requested = str_replace('-', '_', (string)($_SESSION['locale'] ?? 'en_US'));
    $requested = $metadata['aliases'][$requested] ?? $requested;
    $locale = isset($metadata['locales'][$requested]) ? $requested : 'en_US';
    return ['locale' => $locale] + $metadata['locales'][$locale];
}

/** Bundled catalogs work in embedded pages, standalone endpoints, and cron, offline. */
function pctT($message) {
    static $catalogs = [];
    $locale = pctLocaleDefinition()['locale'];
    foreach (['en_US', $locale] as $code) {
        if (!isset($catalogs[$code])) {
            $catalogs[$code] = json_decode((string)@file_get_contents(__DIR__ . '/locales/' . $code . '.json'), true) ?: [];
        }
    }
    return $catalogs[$locale][$message] ?? $catalogs['en_US'][$message] ?? $message;
}

function pctEscape($value) {
    return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function pctH($message) { return pctEscape(pctT($message)); }

function pctJ($message) {
    return json_encode(pctT($message), JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
}

function pctHelp($key) {
    $text = pctT('_' . $key);
    if (function_exists('Markdown')) return '<div data-pct-help="' . pctEscape($key) . '">' . Markdown($text) . '</div>';
    // Keep help usable if a minimal host cannot provide its Markdown renderer.
    return '<blockquote>' . nl2br(pctEscape(preg_replace('/^> ?/m', '', $text))) . '</blockquote>';
}

function pctVersion($file) {
    $version = trim((string)@file_get_contents($file));
    return preg_match('/^\d{4}\.\d{2}\.\d{2}(?:\.\d+)?$/D', $version) ? $version : pctT('unknown');
}
