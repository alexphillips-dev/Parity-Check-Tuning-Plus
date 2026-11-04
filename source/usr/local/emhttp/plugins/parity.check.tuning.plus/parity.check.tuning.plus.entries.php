<?PHP
/*
 * Script that is run to display any error parity check related entries from syslog
 *
 * Copyright 2019-2025, Dave Walker (itimpi).
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
?>
<?
require_once '/usr/local/emhttp/plugins/parity.check.tuning.plus/parity.check.tuning.plus.helpers.php';
?>
<!DOCTYPE html>
<html dir="<?=pctLocaleDefinition()['rtl'] ? 'rtl' : 'ltr'?>" lang="<?=pctEscape(pctLocaleDefinition()['tag'])?>">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta http-equiv="Content-Security-Policy" content="block-all-mixed-content">
<meta name="format-detection" content="telephone=no">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<meta name="referrer" content="same-origin">
<link type="text/css" rel="stylesheet" href="<?autov("/webGui/styles/default-fonts.css")?>">
</head>
<body>

<table class='share_status'><tbody>
<?
	// Build a list of entries from syslog that relate to parity checks
	//
	// Example syslog messages
	// ~~~~~~~~~~~~~~~~~~~~~~~
	// kernel: mdcmd (36): check nocorrect
	// kernel: md: recovery thread: check P Q
	// kernel: md: recovery thread: P corrected, sector=496
	// kernel: md: recovery thread: P incorrect, sector=432
	// kernel: md: sync done. time=105689sec
	// kernel: md: recovery thread: exit status: 0
    $entryCount = 0;
    $handle = @fopen('/var/log/syslog', 'r');
    if ($handle !== false) {
        while (($line = fgets($handle)) !== false) {
            if (strpos($line, 'kernel: md: recovery thread: ') === false || strpos($line, 'TESTING') !== false) continue;
            echo '<tr><td dir="ltr"><bdi>' . pctEscape(rtrim($line)) . '</bdi></td></tr>';
            $entryCount++;
        }
        fclose($handle);
    }
    if ($entryCount === 0) {
        echo '<tr><td colspan="5" style="text-align:center;padding-top:12px">' . pctH('No parity check entries found in syslog') . '!</td></tr>';
    }
?>
</tbody></table>
<div style="text-align:center;margin-top:12px"><input type="button" value="<?=pctH('Done')?>" onclick="window.close()"></div>
</body>
</html>
