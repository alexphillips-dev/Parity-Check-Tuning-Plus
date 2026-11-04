<?php
// Synthetic Unraid host using the official Markdown/translation parser fixtures.
$fixture = getenv('PCT_PLUS_FIXTURE');
$docroot = $fixture . '/usr/local/emhttp';
$_SESSION = ['locale' => $argv[1], 'buildDate' => '20261103'];
$login_locale = $argv[1];
$_SERVER['REQUEST_URI'] = $argv[3] ?? '/Settings/Scheduler';
set_error_handler(function($severity, $message) {
    if (!(error_reporting() & $severity)) return true;
    throw new ErrorException($message, 0, $severity);
});
require_once "$docroot/webGui/include/Translations.php";
$page = "$docroot/plugins/parity.check.tuning.plus/" . $argv[2];
$source = preg_replace('/^#![^\n]*\n/', '', file_get_contents($page));
$source = str_replace(["\r\n", "\r"], "\n", $source);
$body = strpos($source, "---\n") !== false ? explode("---\n", $source, 2)[1] : $source;
// This order reproduces the host's early inline translation before plugin evaluation.
$parsed = Markdown(parse_text($body));
ob_start();
eval('?>' . $parsed);
$html = ob_get_clean();
echo '<!doctype html><html><head><meta charset="utf-8"><style>';
echo 'body{font:16px sans-serif;margin:16px}input,select,button{max-width:100%;box-sizing:border-box}';
echo 'blockquote{display:none}dt{margin-top:8px}dd{margin:0 0 8px}form{max-width:100%}';
echo '</style></head><body>';
if (strpos($argv[2], '.plus.page') !== false) echo '<form id="native-scheduler"><input id="Apply" type="submit" value="Native Apply" disabled></form>';
echo $html . '<iframe name="progressFrame" hidden></iframe></body></html>';
