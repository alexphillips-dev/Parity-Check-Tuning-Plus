# Troubleshooting

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

## Version shows unknown

Inspect `/usr/local/emhttp/plugins/parity.check.tuning.plus/parity.check.tuning.plus.version`. The installer and helper use that same runtime path. Missing, empty, or malformed contents produce plain `unknown`; HTML-looking values are not version markup.

Preserve installer messages and verify package integrity before reinstalling. Do not manufacture a version file to hide an incomplete installation.

## Installation is rejected

Read preflight output. Check the previous tuning plugin and foreign native-hook ownership. Do not delete the native command or backups indiscriminately. See [hook ownership](Installation-Hooks-and-Removal).

## An expected pause/resume did not happen

Record operation category, increment preferences, server clock/time zone, pause/resume times, and Unraid cumulative mode. Include background activity and temperature state. Polling can miss a short task occurring entirely between observations.

## A paused operation remains paused

Check whether its pause was manual, background-owned, temperature-related, outside a window, partial, or associated with pending restart. One finished task is insufficient when another blocker remains. Preserve state before changes.

## Unexpected notifications

Check Unraid delivery settings and the separate increment, heat, and background controls. Fresh informational background messages default off, but an existing saved preference can remain on. A paused operation still exists and participates in background observations.

For completion followed by a native canceled notification, update to `2026.11.03.06` or later. If it recurs, preserve history/progress-save, the completion receipt, kernel operation identity, both notification sources/timestamps, and Unraid version. See [completion coordination](Background-Tasks-and-Notifications).

## Mover detection mismatch

Record the PID file, referenced process arguments, Unraid version, and mover-plugin version. An unrelated process merely mentioning mover should not count. A custom implementation using another identity can require explicit compatibility work.

## Assistant Check is disabled

Check array state, size reporting, another active operation, mode, endpoint syntax, bounds, and ordering. Percentages must be within 0–100. Unknown/zero size is rejected. Validation is repeated by the backend.

## Popup failure

Allow the expected local popup and record its URL/error. The endpoint is Plus `parity.check.tuning.plus.entries.php`. A popup blocker should not crash the assistant itself.

## English or incorrect text

Record locale, entry route (Settings, Plugins, Tools, popup, CLI), exact phrase, and version. Missing translation and poor wording are separate problems. Include proposed wording where possible.

## Unexpected history

Preserve relevant shared history and progress/progress-save records. Include event order, cancellations, restarts, disk-assignment changes, and language changes. Do not erase the evidence before reporting.
