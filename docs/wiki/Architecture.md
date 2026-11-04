# Architecture

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

## Runtime responsibilities

| File | Responsibility |
| --- | --- |
| `parity.check.tuning.plus.php` | CLI/event/cron entry point, operation orchestration, progress/history, native actions. |
| `parity.check.tuning.plus.helpers.php` | Configuration, observed Unraid state, descriptions, logging, utilities. |
| `parity.check.tuning.plus.completion.php` | Completion lock, native protocol and operation/receipt ownership. |
| `parity.check.tuning.plus.notify.php` | Narrow native notification guard with pass-through. |
| `parity.check.tuning.plus.temperature.php` | Shared native-compatible temperature inheritance and critical classification. |
| `parity.check.tuning.plus.background.php` | PID detection and coordinated background pause ownership. |
| `parity.check.tuning.plus.assistant.php` | Partial-range validation and stored monitor bounds. |
| `parity.check.tuning.plus.i18n.php` | Offline locale lookup, encoding, help, and version validation. |
| `Legacy.php` | Conditional native parser/Markdown compatibility when native translation support is unavailable. |
| `Parity.check.tuning.plus.page` | Settings. |
| `Parity.check.tuning.plus.problems.page` | Assistant. |
| `parity.check.tuning.plus.entries.php` | Escaped kernel-entry popup. |
| `parity.check.tuning.plus.history.php` | History presentation. |
| `parity.check.tuning.plus.mdcmd` | Native command wrapper. |
| `event/` | Unraid event dispatchers. |
| `default.cfg` | Raw shipped defaults. |

## State flow

1. Load configuration and observed host state.
2. Interpret the event/cron/CLI request.
3. Apply operation settings, lifecycle markers, background ownership, increment, and temperature constraints.
4. Invoke native commands when permitted.
5. Reconcile later observations, progress, history, and notifications.

A notification is not proof that the host reached its intended state. Synthetic transitions and physical host observations are separate evidence.

## Background coordination

A locked handler observes both supported task classes together. It records whether Plus caused the pause and sent the start message. Ownership transfers through overlap and is not assigned to a pre-existing manual pause.

## Localization boundary

Plus lookup occurs during plugin evaluation, independently of native early inline parsing. Dialog values are JSON literals; labels are escaped; help is rendered after lookup. Native `.txt` exports support host integration.

State/protocol identity is not translated. Display descriptions can change language while stored history remains stable.

## Packaging

The builder reads installed source, catalogs, and notices; applies deterministic metadata; validates the staged archive; and replaces the final artifact only after completion. Source parity and root/snapshot manifest checksums are checked separately.

## Native command sequencing

The Bash wrapper preserves argument quoting and returns native write failures. A preparation callback reconciles old inactive progress before a new check; a separate callback observes state after the native write. Pause/resume/full/partial/cancel/restart paths verify command status and observed native state. Restart polling is bounded to six five-second observations per wait. Native Unraid owns button updates; the inert refresh integration has been removed.

## Lifecycle entry points

Six dispatchers remain: `starting`, `array_started`, `started`, `stopping_array`, `stopping`, and `stopped`. They handle unclean-start observations, restart attempts, saved operation state, stop markers, and completion reconciliation. The installer removes nine old dispatchers whose handlers only returned without an operational action; those events no longer start a PHP process for diagnostic observation alone. See [installation hooks](Installation-Hooks-and-Removal) for the exact retired list.

## Kernel state and units

The runtime observes `/var/local/emhttp/var.ini`. `mdResyncPos` and `mdResyncSize` use 1 KiB units; multiplying by two produces the 512-byte sector units used for partial/restart command offsets. Requested start offsets align down to a multiple of eight sectors. A started array with a positive position is active; an active operation with `mdResync` zero is paused. Positive `mdResync` indicates that the operation is running; it must not be interpreted as a Boolean-only protocol field.

`mdResyncAction` carries native machine tokens such as `check`, `check P`, `recon ...`, and `clear`. A bare `check` is presented as a read check; check subtypes with parity tokens use the correction flag. `mdResyncCorr` controls correcting/non-correcting presentation for parity checks. Names and numeric state remain machine data, independent of translated descriptions. See [configuration and state](Configuration-and-State) for progress fields and timing.

## Retained compatibility and reference checks

The runtime still conditionally loads `Legacy.php`, uses native history-dialog fallback functions, and coordinates native notifications through the existing state/receipt owners. These paths are retained intentionally. Older valid progress annotations remain readable, including temperature and restart annotations, rather than being removed because new writers no longer produce every historical token.

Run `python -B scripts/check_runtime_references.py` when changing runtime functions. It builds PHP token references and follows entry-point/callback roots, explicitly includes native parser APIs, and checks named JavaScript references in page source. Browser and synthetic runtime tests establish behavior separately. Dynamic host interaction and arbitrary branch reachability still require review; the structural check is not an absolute proof about all possible execution paths.

## Stable-channel preparation

The [channel guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/STABLE-CHANNEL.md) describes the shared branch entity, strict update/archive URL checks, non-writing preview, isolated main candidate, and explicit native channel switching. Runtime/configuration/hook identity does not vary by channel.
