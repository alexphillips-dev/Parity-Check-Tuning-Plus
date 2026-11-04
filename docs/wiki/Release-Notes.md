# Release notes

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

## 2026.11.04.05

- Point the plugin manager's **Support Thread** link to the [dedicated Unraid forum topic](https://forums.unraid.net/topic/201158-plugin-parity-check-tuning-plus/).
- Keep GitHub Issues for structured reports and synchronize the README, wiki, and Community Applications support links.
- Manifest and documentation update only; runtime files, language catalogs, saved settings, and native integration behavior are unchanged.

Local qualification passed: 21 focused channel/installer tests on Linux, package/source and checksum checks, documentation/wiki validation, and all 42 language catalogs. The runtime archive is byte-identical to the preceding version.

## 2026.11.04.04

First stable Plus release. This release brings the reviewed development fixes, independent Plus branding, offline language support, and separate stable/development update channels to `main`. The changes below are cumulative from the previous plugin's distributed `2026.04.24` baseline, including defects found and repaired during Plus development.

### Original repository issues resolved in Plus

All five open upstream reports reviewed for this release are addressed below. These are fixes in Plus; the original repository's tickets remain under its own maintainer's control. The [issue remediation guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Issue-Remediation) links each original report and records the implementation and synthetic evidence.

| Original issue | Reported problem | Resolution included in this release |
| --- | --- | --- |
| #16 | Installing the old package could change filesystem-root permissions/ownership and break SSH authentication. | Root-owned deterministic archives exclude the filesystem-root entry and unrelated paths. Validation rejects unsafe paths, entry types, ownership, and modes; extraction tests preserve destination-root metadata. This prevents the packaging defect rather than changing permissions on an already affected host. |
| #17 | The version was missing and the page emitted an invalid HTML tag. | Read the matching Plus runtime version file, validate the numeric version, and escape its presentation. Missing, empty, malformed, or HTML-looking values display a plain-text unknown fallback. |
| #19 | End-point help described the start point. | Correct the canonical end-point help and all generated offline catalogs; verify the rendered help. |
| #21 | Fresh installs unexpectedly sent informational mover/background notifications. | Default informational notifications off while retaining automatic pause/resume handling and saved user choices. Opted-in messages follow actual task transitions. |
| #22 | Mover detection counted process-name matches and could identify unrelated processes. | Use the mover PID file with validated numeric PID and process arguments; support native and tuned mover identities and reject missing, malformed, stale, reused, overflowing, or unrelated identities. |

The remaining sections include connected defects found while repairing those reports, the later code audit, and the subsequent Plus regressions and cleanup.

### Installation and migration

- Install the stable manifest through **Plugins > Install Plugin**: `https://raw.githubusercontent.com/alexphillips-dev/Parity-Check-Tuning-Plus/main/parity.check.tuning.plus.plg`.
- Remove the previous tuning plugin and conflicting integrations before the first Plus installation. Finish active array work before changing hook ownership.
- Plus has its own settings/state directory and `parity.check.plus` CLI. Original settings and in-progress markers are not imported automatically; recreate the desired settings through the Plus UI.
- Ordinary Plus updates preserve saved preferences and native backups. **Defaults** deliberately resets preferences, and uninstalling Plus deletes its configuration and state. Do not uninstall merely to switch Plus channels.
- Stable installations keep both update and package-download URLs on `main`. Development installations stay on `dev`. Explicitly installing the other manifest changes channels; equal/older versions may need native **Force Install**. Review the target version before a deliberate downgrade.

### Scheduling and operation controls

- Correct daily/weekly execution windows, overnight resume boundaries, and weekly day handling. Resume boundaries are inclusive and pause boundaries exclusive, including overnight and week crossings. Custom increment windows survive idle observations and unrelated monitor changes, and are cleared when their pause/resume schedule changes.
- Validate custom cron syntax, reject identical pause/resume times and injected commands, and preserve the last valid schedule after invalid input. Cron files are replaced only after successful validation and writing. Reject a zero-minute monitoring interval instead of replacing valid jobs with an invalid schedule.
- Verify native command success and observed state before announcing starts, pauses, resumes, cancellations, or restarts. Failed transitions retain appropriate ownership/retry state rather than reporting success.
- Preserve native argument quoting and observe state after commands. Correct scheduled/manual/automatic trigger ownership and the CLI correction preference; an unclean-start observation no longer reclassifies a rebuild as a parity check.
- Run native observation after the command, preserving every quoted argument and the native exit status. Bare check callbacks no longer read a missing optional argument, and padded parent-process names do not lose scheduled classification.
- Require a started array and an observed active operation for a full-check start. Map the native correction preference correctly; a missing preference defaults to non-correcting. Failed cancellation retains ownership and does not announce cancellation; successful cancellation retains the operation description.
- Handle missing, malformed, stopped, and overflowing native state safely while refreshing descriptions after state reloads. Marker timestamps now record the actual creation time.
- Correct detection of either parity slot and active/idle/paused CLI status. Applying Defaults reloads reset preferences before regenerating cron entries.

### Mover, backup, temperature, and restart handling

- Detect native/tuned mover activity using a validated PID and process identity, avoiding unrelated processes that merely contain the word mover. Retain the supported backup/restore marker paths.
- Coordinate overlapping mover/backup pauses, preserve manual pauses, transfer ownership correctly, and resume only when the relevant background, thermal, restart, partial-check, and increment-window restrictions clear.
- Explicit CLI pause relinquishes background resume ownership, including when the operation was already paused. Failed background or heat pauses claim no pause; failed resumes keep their markers so later monitoring can retry.
- Default informational mover/backup notifications to off for fresh installs; automatic pause/resume remains separately controlled and saved choices survive updates. Opted-in transition messages are not repeatedly duplicated.
- Follow native warning/critical temperature inheritance, including per-disk, SSD/NVMe, inherited, and explicitly disabled limits. Invalid saved offsets no longer stop monitoring with arithmetic errors.
- Separate critical-temperature shutdown from completion shutdown and heat-pause preferences. Check available critical temperatures before idle/stopped/partial exits, including pool disks, and reread the saved policy before shutdown.
- Validate saved restart positions, ranges, correction/action fields, operation identity, enabled policy, and disk assignments. Detect removed/replaced disks, bound restart polling, preserve trigger information, and reject failed attempts without a false success notification.
- Detect added or missing array assignments as well as removed/replaced disks, excluding pool disks from the restart identity snapshot. Check the current restart preference before acting. Each cancellation/start wait is limited to six five-second observations rather than waiting indefinitely.

### Completion, notifications, progress, and history

- A completed operation no longer inherits a stale canceled result from an earlier increment. Save history and merge errors before sending the completion summary.
- Coordinate native parity-finish delivery with operation identity, completion locking, and delivered-summary receipts to prevent misleading duplicate canceled notifications after a successful Plus summary.
- Preserve real cancellations, failures, new errors, unrelated notifications, and native delivery fallback when state is unowned/corrupt or delivery fails.
- Prevent duplicate pause/resume/stop/restart observations from double-counting runtime or increments. Retain correction labels, native action tokens, historical temperature annotations, and supported progress delimiter/history formats.
- Preserve the initial correcting/non-correcting policy after terminal native metadata clears. Resolve stale terminal progress only against the matching final native operation, and retain correct final time, elapsed time, runtime, increment count, and merged errors.
- Serialize duplicate analyzers and native finish delivery. Delayed snapshots still match the intended operation; higher native error counts, aborted runs, invalid receipts, failed history writes, and failed Plus delivery keep native warning/fallback delivery available. The notification wrapper passes unrelated commands, arguments, output, and exit status through.
- Limit canceled-history cleanup to the matching operation; retain unrelated rows and handle missing/malformed history safely. Escape history output.
- Render supported five-through-ten-field history rows without arithmetic errors from nonnumeric durations, missing-subtype warnings, or malformed header cells. Persisted history text cannot become HTML. Preserve corrupt progress for diagnosis rather than crashing analysis or suppressing native fallback.
- Partial progress with a missing running marker stays diagnostic-only and cannot produce full-check history, a full-check completion summary, or completion shutdown.
- Correct conflict/unknown-trigger diagnostics and native Unraid version-boundary checks at 6.10.3 and 6.11.0.
- Remove the extra dollar sign in trigger-conflict diagnostics and the undefined variable in unknown-trigger warnings. Include exactly 6.10.3 and 6.11.0 in their respective supported feature branches.

### Assistant, settings, and interface

- Repair Assistant mode selection, form/button references, sector-message popup paths/case, and escaped syslog output. Correct endpoint help and version display.
- Validate sector/percentage ranges on the server before invoking native commands; bind immutable bounds and correction policy to the actual partial operation. Stale markers cannot cancel another run, and failed stop requests retain retry state.
- Remove the ownership marker after a failed partial start, without claiming a started operation. Display the running operation's saved range and correction choice rather than later edited settings. Emit one valid language attribute in the syslog popup, with no undefined language variable or duplicate attribute.
- Keep Settings and Assistant labels/controls aligned in the native responsive grid, including conditional fields, expanded help, desktop/mobile layouts, and unrelated native Scheduler controls.
- Defaults can recover invalid schedules. Each actual submission selects its own command, so a blocked/canceled reset cannot turn a later Apply into another reset.
- Restore a compact normal-size plugin header and concise description, removing the oversized heading and broken inline image. Escape saved form values and retain native current/legacy history dialogs and parser fallback.

### Languages, installation safety, and maintenance

- Bundle **42 offline language catalogs**, three native aliases, and **45 native exports**, covering settings, help, dialogs, CLI text, history, and notifications. Arabic, Persian, and Hebrew support RTL presentation. Stored machine/protocol values remain language-independent.
- Load translations after native early parsing so settings, full help, dialogs, and notification/CLI templates translate reliably. Safely encode translated JavaScript/HTML and retain positional formatting placeholders and native parser fallback. Resolve Danish/Japanese/Korean aliases; empty or unknown locales reset to English instead of retaining a previous language.
- Keep action names and stored history descriptions in English even when their presentation is translated. Translate testing-mode CLI descriptions without translating command tokens. Invalidate only Plus translation caches during installation/removal, preserving other plugins' cached translations.
- Reject unsafe package paths/types/ownership/modes and filesystem-root metadata; use deterministic root-owned packages and preserve an existing archive if staged package validation fails.
- Keep archive MD5/SHA256 values, manifest snapshots, and checksum sidecars in sync. Check case-sensitive installed paths and source/package parity before publishing.
- Enforce native hook ownership, preserve original command/history/notification backups, block missing/foreign integrations, and restore native hooks on removal.
- Remove unfinished Docker/container controls, the unimplemented CLI history placeholder, unused helpers/branches/assignments, redundant UI logic, inert refresh integration, and nine event handlers with no operational work. Retain GUI history, six operational lifecycle hooks, and working native compatibility. Upgrades remove retired installed files while preserving saved configuration.
- Add detailed README/wiki guidance, five issue forms, a reviewed label catalog, synthetic/browser regressions, original-plugin comparisons, runtime-reference checks, and exact-index publication/privacy checks. GPLv2 and required original copyright/permission notices remain.
- Keep local agent instructions, editor/assistant sessions, credentials, private host data, downloaded tools, and generated reports out of publication. Review exact staged bytes and package members rather than relying on ignore rules.

### Verification and remaining limits

The runtime entering this release passed the combined **134-test Python suite**, **225 browser page cases**, **945 native-grid layouts**, locale checks, package/source parity, and Windows/Linux reproducibility checks. The offline original/current checker covers **602 executable comparisons**, with additional cron and native temperature matrices documented in the repository. Final stable-candidate checks are recorded in the validation guide.

The owner reports completing the discussed live Unraid acceptance checks for the prior runtime. That is separate from automated fixture evidence; no host/version/log details are published. This stable promotion changes release/channel metadata and documentation, not installed runtime code. The declared minimum remains Unraid **6.9.2**; testing does not certify every host, historical/future build, or third-party integration. Translation wording is machine-authored and has not received complete native-speaker review. Partial checks stop through periodic monitoring and can run beyond the selected endpoint; they do not replace a full parity check.

See the [installation and migration guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Installation-and-Migration), [validation record](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/VALIDATION.md), and [original-plugin comparison](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/UPSTREAM-COMPATIBILITY.md).

## Development history

## 2026.11.04.03

- Prepare distinct stable/main and development/dev self-update and package-download channels without changing plugin identity, saved preferences, native hooks, or installed runtime code.
- Reject unknown, mixed, or foreign channel URLs before writing package artifacts.
- Add build previews and isolated candidate roots, plus channel-aware package/documentation validation.
- Verify dev/main package identity, historical artifact preservation, failure-before-write behavior, and settings/native-backup preservation during explicit channel changes.
- Document both installation URLs, stable availability after promotion, explicit switching and native reinstall/downgrade controls, and owner-reported live acceptance.

This update is published on dev. Main promotion and public release remain separate authorized actions. See the [channel guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/STABLE-CHANNEL.md).

Local qualification passed: 134 Python tests, dev and isolated-main package/documentation validation, 17 focused installer cases, all language catalogs, and matching Windows/Linux archive bytes. Installed runtime source/package bytes are unchanged; the owner reports completing the prior runtime's discussed host acceptance checks.

## 2026.11.04.02

- Fix Settings submission so Defaults can recover invalid schedules and a canceled reset cannot turn a later Apply into another reset. Actual browser submitter selects the command on every attempt.
- Pin the original upstream repository/package and compare defaults, operation policies, native state, cron output, formatting, and notification arguments with current source.
- Add an offline checker with 602 executable comparisons and a negative control that detects a changed setting binding.
- Add 48 legacy-progress cases across four version branches, six operation/correction variants, and both delimiter representations; verify timing, native actions, history fields, and one delivered summary.

See the [original-plugin compatibility review](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/UPSTREAM-COMPATIBILITY.md) for the pinned baseline, intentional differences, exact evidence, and remaining live-host acceptance.

Local qualification passed: 124 Python tests including 48 legacy-input subcases, 225 browser page cases, 945 native-grid layouts, 42 catalogs, and source parity for 114 packaged files. The offline upstream checker passed all 602 comparisons on Windows and Linux.

## 2026.11.04.01

- Remove the unfinished Docker/container settings, empty selection callback, unused container-list helper, and experimental UI initialization. Normal updates preserve saved retired values; the runtime ignores them. Defaults intentionally resets to the current defaults.
- Remove the inert refresh page and nine no-op event dispatchers from the package. Upgrade cleanup removes those files from existing installations. Retain six operational lifecycle dispatchers.
- Remove uncalled suffix, inverse-temperature, and severity helpers; the unimplemented CLI history handler/help entry; never-produced starting/spinup marker constants; discarded assignments; and obsolete commented-out implementations.
- Remove duplicate page state reads/initialization, redundant Assistant forwarding code, repeated native configuration imports, an already-aligned restart adjustment, and one-iteration ownership lookup scaffolding.
- Preserve native parser/Markdown compatibility, current/legacy native history dialogs, live notification coordination, original notices, and valid older progress annotations.
- Keep marker-lost partial progress diagnostic-only so it cannot generate a full-check history row, completion summary, or completion shutdown.
- Replace the historical design-notes document with source-grounded kernel units and progress fields in the architecture/state guides.
- Add structural runtime-reference validation, installation cleanup regressions, and browser assertions for retired controls and retained compatibility paths.

Local qualification passed: 122 Python tests, 225 browser page cases, 945 native-grid layouts, 42 catalogs with 336 active messages each, and source parity for 114 packaged files. Windows/Linux package bytes match; the cleanup report records the SHA256 and acceptance limits.

See the [cleanup report](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/CLEANUP-2026.11.04.md), [architecture](Architecture), [configuration/state protocol](Configuration-and-State), and [installation cleanup](Installation-Hooks-and-Removal).

## 2026.11.03.07

- Verify native pause, resume, full-check, partial-check, cancellation, and restart outcomes before announcing success or transferring ownership.
- Correct CLI correction-mode mapping, automatic-check classification, and scheduled/restarted trigger metadata.
- Separate critical-temperature shutdown from completion shutdown; use native temperature inheritance and monitor idle, stopped, partial, and pool disks.
- Validate restart state and disk identities, bound restart polling, and scope canceled-history cleanup to its operation.
- Repair weekly/overnight increment windows and validate cron expressions before atomically replacing working schedules.
- Bind partial checks to a kernel operation and immutable range; preserve retry state after failed transitions.
- Prevent duplicate progress accounting, preserve correction labels, and keep native notifications available for corrupt progress.
- Escape saved fields and history text, tolerate malformed history, and align Assistant settings in the native grid.
- Retire the nonfunctional native-button scaffold and extend synthetic and browser regressions.

## 2026.11.03.06

- Keep the final progress/kernel result and finish time when replacing stale canceled history; merge errors before the summary.
- Serialize analysis and matching native finish delivery; guard duplicates with operation identity and a delivered-summary receipt.
- Preserve cancellations, errors, new/unowned runs, unrelated notifications, and delivery fallback.
- Back up and restore the notification hook; expand the synthetic suite to 62 tests.

## 2026.11.03.05

- Separate inline help from Markdown setting rows so Scheduler labels and controls remain paired in the native responsive grid.
- Keep action buttons in the control column and close custom-schedule field wrappers.
- Add 810 native-stylesheet layout cases across both settings routes, all locale codes, three widths, and daily/weekly/custom schedules, with conditional fields, expanded help, and a malformed-row negative control.

## 2026.11.03.04

- Restore a compact, normal-size bold plugin-name header above the short Plugins-page description.

## 2026.11.03.03

- Condense the installed Plugins-page description to a feature summary, settings location, and documentation link.
- Remove the large Markdown heading and broken relative image from that description.

## 2026.11.03.02

- Safe archive paths/types/permissions and deterministic ownership; failure-safe staged replacement.
- Validated PID-based mover identity.
- Informational background notifications off by default; saved preferences retained.
- Pause ownership, overlap, manual-pause preservation, temperature/window/restart/partial restrictions.
- Correct assistant setting selection, button references, range validation, endpoint help, and escaped popup output.
- Server-side partial validation and stored end bounds.
- Safe version fallback and stable history identity across languages.
- Defaults/config reload and active/idle status repairs exposed by connected tests.
- 42 offline catalogs, 368 messages each, and three native aliases.
- Actual native parser fixtures, 40 synthetic tests, 225 browser cases.
- Detailed README/wiki and explicit dev publishing policy.

Live install/lifecycle/mover/temperature acceptance and native-speaker review are separate.

## 2026.11.03.01 local baseline

Established Plus runtime/configuration/CLI/UI/translation identities, replaced active project metadata, removed historical distributions/editor sessions from the active tree, and retained required notices/history. The current development candidate supersedes that local baseline.
