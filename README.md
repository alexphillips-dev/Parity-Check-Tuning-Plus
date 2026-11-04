# Parity Check Tuning Plus

![Parity Check Tuning Plus](parity.check.tuning.plus.svg)

**Maintainer:** [alexphillips-dev](https://github.com/alexphillips-dev)
**Stable release:** `2026.11.04.05`
**Update channels:** `main` (stable), `dev` (development)
**Minimum declared Unraid version:** `6.9.2`

Parity Check Tuning Plus adjusts when long-running Unraid array operations run. It can split selected operations into scheduled increments, pause operations around mover or supported appdata backups, and respond to disk temperature conditions. It also provides extended parity history and an assistant for investigating reported parity-error sectors.

The normal scheduled workflow starts with an array operation initiated by Unraid. The plugin manages its execution after it starts. Explicit CLI and assistant commands can initiate operations, so review those controls separately.

The first stable Plus release is published on `main`. It consolidates the fixes and improvements made since the previous plugin; read the [complete release notes](docs/releases/2026.11.04.04.md) before migrating. The owner reports completing the discussed live Unraid acceptance checks for the tested runtime. Local checks and owner-reported acceptance are recorded separately in [validation](docs/VALIDATION.md).

The `2026.11.04.05` metadata update connects the plugin manager's **Support Thread** link to the [Unraid forum topic](https://forums.unraid.net/topic/201158-plugin-parity-check-tuning-plus/). See the [update notes](docs/releases/2026.11.04.05.md).

The cumulative notes cover all five reviewed original issue reports (#16, #17, #19, #21, and #22), the completed/canceled notification fix, and every connected repair from the source audit and later Plus development. The [issue remediation guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Issue-Remediation) links the original reports and their evidence.

## Documentation and support

- [Unraid support thread](https://forums.unraid.net/topic/201158-plugin-parity-check-tuning-plus/)
- [Complete wiki](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki)
- [Getting started](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Getting-Started)
- [Installation and migration](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Installation-and-Migration)
- [Settings reference](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Settings-Reference)
- [Troubleshooting](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Troubleshooting)
- [Report a Plus issue](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/issues)
- [Local validation details](docs/VALIDATION.md)
- [First stable release notes](docs/releases/2026.11.04.04.md)
- [Stable/development channels and promotion workflow](docs/STABLE-CHANNEL.md)
- [Comprehensive source audit and regression evidence](docs/AUDIT-2026.11.03.md)
- [Runtime cleanup and retained compatibility](docs/CLEANUP-2026.11.04.md)
- [Original-plugin compatibility review](docs/UPSTREAM-COMPATIBILITY.md)
- [Wiki source pages](docs/wiki/Home.md)

## Source audit and runtime cleanup

The `2026.11.03.07` [audit](docs/AUDIT-2026.11.03.md) repaired operation commands, pause ownership, temperature shutdown, restart validation, scheduling, progress accounting, and rendering. The `2026.11.04.01` [cleanup](docs/CLEANUP-2026.11.04.md) removes unused helpers, unfinished controls, obsolete event dispatchers, and redundant logic while retaining working features, native compatibility, and stable progress/history protocol fields. Structural reference checks complement the behavioral tests; live Unraid acceptance remains separate.

The `2026.11.04.02` [original-plugin comparison](docs/UPSTREAM-COMPATIBILITY.md) checks the pinned upstream repository and distributed package against current behavior. It also fixes Defaults recovery for invalid schedules and prevents a canceled reset from changing a later Apply into a reset. The offline checker runs 602 original/current comparisons; permanent regressions cover 48 legacy-progress cases.

## Capabilities

| Area | Behavior |
| --- | --- |
| Increment scheduling | Select scheduled, manual, and automatic checks independently; configure daily, weekly, or custom pause/resume schedules. |
| Other array operations | Optional increment handling for parity sync/data rebuild and disk clear. These options are disabled by default. |
| Background activity | Pause around native/tuned mover and recognized appdata backup/restore activity. |
| Pause ownership | Resume background pauses only when the plugin owned the pause and other blocking conditions permit it. |
| Temperature handling | Optional pause/resume thresholds relative to Unraid warning temperatures, plus a separately controlled critical-temperature shutdown option. |
| Restart attempts | Optional inherited support for resuming eligible operations after an array stop/start or reboot, subject to saved state and disk-identity checks. Owner-reported host acceptance is recorded separately from synthetic evidence. |
| Parity history | Additional elapsed-time and increment information, with translated presentation and stable stored protocol fields. |
| Assistant | Sector/percentage range selection, server-side validation, and a popup showing matching kernel parity messages. |
| CLI | `parity.check.plus` exposes status and operation controls. |
| Languages | 42 bundled offline catalogs, three native locale aliases, and RTL presentation for Arabic, Persian, and Hebrew. |

## Installation and update channels

Install the stable release with this manifest URL:

```text
https://raw.githubusercontent.com/alexphillips-dev/Parity-Check-Tuning-Plus/main/parity.check.tuning.plus.plg
```

For development builds, explicitly use this separate channel:

```text
https://raw.githubusercontent.com/alexphillips-dev/Parity-Check-Tuning-Plus/dev/parity.check.tuning.plus.plg
```

1. Read [installation and migration](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Installation-and-Migration), especially the independent settings namespace and native-hook ownership rules.
2. Remove the previous parity tuning plugin and any conflicting integration before installing Plus. Avoid changing plugin ownership during an active array operation.
3. In Unraid, open **Plugins > Install Plugin**, paste the chosen published channel's manifest URL, and install.
4. Open **Settings > Scheduler** and review the Plus settings. Use the Help icon or click a setting label for explanations.
5. Confirm the displayed version, review the schedule and notification options, and perform the live-host acceptance checks appropriate to your intended use.

The plugin is configured under **Settings > Scheduler**. Its assistant is under **Tools > Parity Check Tuning Plus**.

An update from an existing Plus installation preserves the saved configuration. A fresh installation uses Plus defaults. Each installed manifest keeps both update and package-download URLs on its selected channel; a dev push does not move stable installations to dev. Switch channels by explicitly installing the target manifest, with native Force Install where needed for an equal/older version; do not uninstall merely to switch because removal deletes saved configuration. Verify the target exists and review any downgrade. See the [channel guide](docs/STABLE-CHANNEL.md). No Community Applications listing or stable-channel promotion is implied by a `dev` push.

The cleanup removes previously shipped inert files during upgrade: the button-refresh scaffold and nine event dispatchers with no operational handlers. Six lifecycle hooks remain. Retired Docker/container preference values may remain in an existing configuration, but are ignored; normal updates do not rewrite them. **Defaults** intentionally replaces saved configuration with the current defaults.

## Migration and coexistence

Plus has its own plugin ID, files, configuration keys, state markers, language catalogs, and CLI command. It does not automatically import settings or active-operation state from the previous plugin.

Recreate desired settings through the Plus UI. Copying the previous configuration verbatim does not convert its keys. Do not copy old progress, restart, temperature, or pause-ownership markers into Plus.

The installer rejects the previous plugin and foreign symlink ownership of the native command/history hooks. Those hooks cannot be shared safely by two tuning integrations. Unraid's shared `/boot/config/parity-checks.log` remains the system history file.

## Initial defaults and first configuration

| Setting | Fresh-install default |
| --- | --- |
| Scheduled parity checks use increments | Enabled |
| Manual checks use increments | Disabled |
| Automatic checks use increments | Disabled |
| Increment frequency | Daily |
| Resume / pause | `00:15` / `07:30`, using the server's time configuration |
| Increment pause/resume notifications | Enabled |
| Pause while mover runs | Enabled |
| Pause while supported backup/restore runs | Enabled when the relevant integration is available |
| Informational mover/backup notifications | Disabled |
| Temperature pause/resume | Disabled |
| Critical-temperature shutdown | Disabled |
| Resume attempts after array restart | Disabled |
| Shutdown after completion | Disabled |
| Logging level | Basic |

Unraid's native cumulative parity-check option and the plugin's increment scheduling should not both manage the same operation. The UI disables incompatible increment choices when cumulative mode is enabled.

The [complete settings reference](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Settings-Reference) includes raw configuration defaults, monitor intervals, and the distinction between UI-enforced logging targets and the raw default file.

## Scheduling example

Suppose a complete parity check needs about 30 hours and you want it to run for three hours overnight. Configure a resume time of `00:15` and a pause time of `03:15`, and enable increments for the relevant operation category. The work can then span roughly ten overnight windows, with elapsed calendar time exceeding actual runtime.

The plugin does not itself create the normal monthly parity-check start schedule. Configure that in Unraid's Scheduler. Background tasks, temperature conditions, interruptions, and monitoring intervals can extend the calendar time further.

Custom schedules use five cron fields. The UI rejects missing fields and identical custom pause/resume entries. Complex cron boundary behavior, time-zone/DST changes, and physical host timing require test-host qualification; local tests do not certify every possible cron expression.

## Background tasks and notifications

The plugin validates `/var/run/mover.pid` against the process command line instead of counting `grep` matches. Native mover and the known `age_mover`/`share_mover` script identities are recognized. Missing, malformed, stale, and unrelated PIDs do not count as an active mover.

Mover/backup activity is sampled by the monitor. A short task that starts and ends between polls may not be observed.

Background markers record whether Plus owned the pause and whether it sent the start notification. Overlapping mover and backup activity is evaluated together. Finishing one task cannot resume an operation while another blocking task remains active. A manually paused operation is not automatically resumed merely because a background task finishes.

Informational background notifications are opt-in on fresh installations. Changing that notification preference does not disable pause/resume handling. Existing saved preferences survive updates. Unraid's own system-notification configuration must also allow delivery.

## Temperature behavior

Temperature thresholds are offsets from Unraid's warning/critical limits, not absolute temperature values. With a warning temperature of `45°C`, pause offset `3`, and resume offset `8`, the corresponding thresholds are `42°C` and `37°C`. Per-drive overrides and disabled native thresholds affect the result.

Critical-temperature shutdown is a separate option and is disabled by default. Completion shutdown is also disabled by default and does not check whether unrelated server work is running. Read the built-in help before enabling either option.

## Assistant and partial checks

The assistant accepts sector numbers or percentages. The backend independently validates the selected method, numeric bounds, ordering, array size/state, and correction option before issuing `mdcmd`.

Each running marker includes the observed kernel start time and array size. A failed start leaves no partial owner; stale or legacy unbound markers are discarded without canceling an operation. A failed stop remains eligible for retry. Start/completion notifications use the stored range and correction policy.

Starting sectors are aligned down to a multiple of eight 512-byte sectors. The validated end sector is stored with the running partial check. Changing configuration later does not move that stored stop boundary.

The default partial-check monitor runs once per minute, so stopping can occur beyond the requested endpoint. Partial checks are diagnostic tools and do not replace a complete parity check after the underlying problem is addressed. Writing corrections changes parity; choose that option deliberately.

The sector popup shows matching kernel parity messages as escaped literal text. Hostnames, timestamps, sector numbers, and other machine data are not translated.

## CLI

```text
parity.check.plus help
parity.check.plus status
```

| Action | Purpose |
| --- | --- |
| `pause`, `resume` | Request operation pause/resume through plugin checks. |
| `analyze` | Reconcile saved progress into history when eligible. |
| `check` | Use the inherited scheduler-mode selection path. Use explicit correcting/non-correcting commands when you need to review the requested mode directly. |
| `correct`, `nocorrect` | Start an explicitly correcting or non-correcting check when allowed. |
| `cancel` | Cancel an active check. |
| `start`, `stop` | Request array start/stop on supported Unraid versions. |
| `config`, `updatecron` | Log/reload configuration or regenerate plugin cron entries. |
| `defaults` | Replace Plus settings with defaults and regenerate schedules. |
| `partial` | Start a validated partial check from saved assistant settings. |

These entry points share reconciliation code. Treat commands as operational interfaces, not as a guarantee of side-effect-free inspection. Use the GUI History control to view operation history. See the [CLI reference](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/CLI-Reference).

## Languages

Language selection follows Unraid's session locale. Translation is offline after installation; the plugin does not call a translation service at runtime. An empty session locale returns to English.

There are 42 canonical catalogs with 336 messages each, plus native exported aliases for Danish (`da_DA`), Japanese (`ja_JA`), and Korean (`ko_KO`). Supported variants include Brazilian/European Portuguese and Simplified/Traditional Chinese. Labels, dialogs, help, CLI descriptions, history presentation, and notification templates are covered.

Paths, IDs, command names, severity codes, configuration keys, and history protocol fields remain stable. Translations are machine authored and structurally/browser validated; native-speaker review remains outstanding. See [Languages and accessibility](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Languages-and-Accessibility) for the complete locale table.

## Completion notifications

A successful operation keeps its final status in history even if an earlier increment left a canceled entry. Plus saves history and merges errors before sending its summary. Genuine cancellations and errors remain alerts.

A narrow wrapper around Unraid's native `notify` entry point suppresses matching parity-finish duplicates for a tracked run or a delivered Plus summary. New/unowned runs, changed errors, unknown state, unrelated alerts, and management commands pass through. The native monitor retains ownership of its own state. The installer preserves the original notifier and restores it on removal.

See [notification coordination](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Background-Tasks-and-Notifications).

## Files, backups, and removal

| Item | Location |
| --- | --- |
| Runtime files | `/usr/local/emhttp/plugins/parity.check.tuning.plus/` |
| Configuration/state directory | `/boot/config/plugins/parity.check.tuning.plus/` |
| Configuration | `parity.check.tuning.plus.cfg` in the configuration directory |
| Cron, progress, and markers | Plugin-prefixed files in the configuration directory |
| Displayed version | Runtime-directory `parity.check.tuning.plus.version` |
| Native catalogs | `/usr/local/emhttp/languages/<locale>/paritychecktuningplus.txt` |
| Shared Unraid history | `/boot/config/parity-checks.log` |
| Native-hook backups | Original hook path plus `.parity.check.tuning.plus.orig` |

The installer saves native hooks once and preserves those backups through updates. Removal restores a hook only if it still points to Plus, preserves foreign hook ownership, removes Plus configuration/state, and updates cron. A missing required backup stops removal. Back up desired configuration before uninstalling; removal deletes that directory.

## Validation and development

```text
python -B scripts/build_i18n.py --check
python -B scripts/build_package.py
python -B scripts/check_branding.py
python -B scripts/check_runtime_references.py
python -B scripts/check_publish_files.py
```

Run the complete Python suite on Linux/WSL:

```text
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
```

Run browser fixtures:

```text
npm ci --ignore-scripts
npx playwright install chromium
python -B tests/render_fixtures.py
npm run test:ui
```

The current validation suite contains 134 synthetic tests, including 48 legacy-progress subcases, 225 browser page/route cases, and 945 native-grid layout cases. Install development dependencies with `python -m pip install -r requirements-dev.txt` before discovering the suite; PyYAML is used only for repository issue-form checks. The optional offline upstream checker adds 602 executable comparisons. The browser renderer uses official Unraid Markdown/translation parser fixtures. Checks for the 114-file package cover source parity, checksums, ownership/modes, dangerous paths, root-preserving extraction, and failure-safe archive replacement. Reproducibility checks compare Windows/Linux package bytes. See [validation evidence and limits](docs/VALIDATION.md).

The runtime reference check tokenizes owned PHP functions and follows entry-point/callback references, with native parser compatibility functions declared as external roots. It also checks named page JavaScript references. These checks help catch unused functions and complement real-browser/runtime tests; they do not prove every dynamic host path or branch is reachable.

Only product source, licenses, public documentation, reproducible development inputs, and published install artifacts belong in Git. Local agent instructions, editor state, credentials, host diagnostics, and generated output are ignored. After staging explicit reviewed paths, run `scripts/check_publish_files.py`: it inspects the exact index and package contents, including force-added files, and reports only paths/categories. It complements manual review and secret scanning; it cannot prove the absence of every kind of private information. Raw scan reports stay local. See [publication rules](docs/wiki/Packaging-and-Publishing.md).

Completed updates are committed and pushed to `dev` with:

```text
git push --no-verify origin dev
```

`--no-verify` is the maintainer's requested push workflow; required local checks still run beforehand. `main` promotion, history rewriting, and public releases require separate authorization. The wiki has its own Git repository and publication commit.

## Troubleshooting and support

Start with the [troubleshooting guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Troubleshooting) and [diagnostics guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/wiki/Diagnostics-and-Support).

Open the [issue chooser](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/issues/new/choose) for a bug report, feature request, translation problem, documentation correction, or question/troubleshooting report. Each form applies its report-type label and `needs-triage`. Logs and screenshots are optional; relevant settings and operation details are more useful than a full diagnostics archive.

The [label catalog](.github/labels.json) defines report types, investigation status, affected components, priorities, and contribution/closure labels. Component and priority labels are assigned during maintainer triage. `needs-testing` distinguishes a proposed fix awaiting reporter or live-host confirmation from a verified host result. Form/label maintenance and the submission checklist are documented in [Diagnostics and Support](docs/wiki/Diagnostics-and-Support.md).

Include the Plus version, Unraid version, operation category, relevant settings, exact steps, and expected/observed behavior. For a translation report, include the selected language, entry route, and exact untranslated text. For a pause/resume report, include background-task state, temperature conditions, and increment timing.

Sanitize hostnames, disk serials, network addresses, private paths, and unrelated syslog content before publishing diagnostics. Keep relevant timestamps and event order.

## License and attribution

The inherited plugin source is distributed under **GNU GPL version 2**. [LICENSE](LICENSE) is the canonical license text; [NOTICE](NOTICE) records source attribution and Plus changes. The build uses `LICENSE` to supply the installed package's `COPYING` file. Required original copyright and permission notices remain in source headers. Third-party test fixtures retain their own notices.

Required attribution remains in the notices and source headers. Original authorship does not identify the current Plus maintainer or support destination.
