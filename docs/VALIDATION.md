# Parity Check Tuning Plus validation

## First stable release: 2026.11.04.04

The main promotion candidate passed the complete **134-test Python suite**, fresh
**225 browser page cases**, **945 native-grid layouts**, all **42 language catalogs**,
**45 native exports**, and **602 original/current executable comparisons**. Main-channel
manifest/package/documentation checks passed, including exact source parity for the
114-file archive, installed references, 14 PHP/page syntax checks, canonical main
update/archive URLs, and matching current-version manifest snapshot/checksums.
Windows and Linux builds produced the same SHA256:
`c9720e3fd994c6ceddb4a6284b0b88fa7df941f9e7953eb8c0aa89cad3805667`.

Installed runtime source and earlier published artifacts are unchanged from the
reviewed dev candidate. The current stable root/snapshot manifests select `main`;
dev synchronization must restore `dev` in its own root/current-version snapshot.
Public artifact/release verification is performed after publication. Host acceptance
is owner-reported as described below; no physical-host automation was performed.

The first stable release is `2026.11.04.04` on `main`. Its [cumulative release notes](releases/2026.11.04.04.md) cover the fixes and improvements since the previous plugin. The release changes version/channel metadata and documentation; installed runtime source remains identical to the reviewed dev runtime. The preceding development candidate was `2026.11.04.03`. The [channel guide](STABLE-CHANNEL.md) records branch-correct metadata, fail-before-write checks, isolated main preparation, and installer/configuration preservation. On November 4, 2026, the owner reported completing the live Unraid acceptance checks previously discussed. This is owner-reported acceptance of the prior runtime; no host/version/log details were supplied, and the development agent did not execute physical-host tests. Installed runtime source is unchanged in this channel-preparation update.

The preceding channel-preparation suite passed **134 Python tests**, including four channel regressions and the dev/main/dev installer-switch regression. A separate focused installer run passed 17 tests. Dev and isolated-main package validation passed, including malformed/mixed/foreign channel rejection before artifact writes, no-write preview, unchanged settings/native backups, preserved historical artifacts, identical archive bytes, and branch-aware documentation checks. Windows/Linux builds reproduce the same 114-file package SHA256, `c9720e3fd994c6ceddb4a6284b0b88fa7df941f9e7953eb8c0aa89cad3805667`. The package is byte-identical to the prior runtime package; those preparation manifests identify version `2026.11.04.03` and their selected channel.

The preceding development candidate was `2026.11.04.02`. The [original-plugin compatibility review](UPSTREAM-COMPATIBILITY.md) pins the upstream repository and published package, documents intentional differences, and records the Defaults regression and repair. Final local qualification passed: 124 Python tests, 225 browser page cases, 945 native-grid layouts, all 42 catalogs, and source parity for 114 packaged files. The comparison checker runs 602 executable comparisons and passed on Windows and Linux. Independent matrices cover 768 cron scenarios and 384 native temperature-threshold evaluations; the permanent completion regression adds 48 legacy-input cases. These counts overlap other coverage and are not additional unittest methods.

The preceding development candidate was `2026.11.04.01`. Combined local qualification passed: 122 Python tests, 225 browser page/route cases, 945 native-grid layout cases, source parity for the 114-file package, and 336 active messages in each of 42 catalogs with 45 native exports. Windows/Linux builds produced identical package bytes. The [runtime cleanup report](CLEANUP-2026.11.04.md) documents removed surfaces, retained compatibility, configuration preservation, structural reference-check limits, and package checksum.

The preceding `2026.11.03.07` candidate had 114 Python synthetic tests, 225 browser page/route cases, and 945 native-grid layout cases. Five publication-boundary tests were added after the runtime audit without changing installed files or package bytes. The [comprehensive source audit](AUDIT-2026.11.03.md) maps those confirmed defects, repairs, reviewed components, regression names, compatibility decisions, and acceptance limits. The earlier remediation records below are retained for historical context.

The local `2026.11.03.02` candidate addresses upstream issues 16, 17, 19, 21, and 22. It also repairs connected assistant, settings, notification, and history paths exposed by the regression tests.

| Issue | Implementation | Synthetic verification |
| --- | --- | --- |
| 16: host permissions | Root archive entries, unrelated paths, unsafe types, non-root ownership, and unsafe modes are rejected. Package directories are root-owned and mode 755. | Historical root-metadata negative control; archive metadata checks; extraction preserves the temporary root's mode and ownership. |
| 17: version and translations | Version strings are validated; missing/invalid files yield escaped plain text. Bundled catalogs load independently of native page parsing. Dialog values use JSON encoding and help is rendered after catalog loading. | Version edge cases; locale switching; printf execution; injection checks; official native parser fixtures; all page entry routes. |
| 17: assistant interactions | Correct mode-setting binding, existing form-button references, validated submission, and safe popup output. | Browser dropdown/validation tests and rendered popup checks. |
| 19: endpoint help | Endpoint help describes the end point in the canonical source and all generated catalogs. | Catalog/source checks and rendered help in every locale. |
| 21: notification defaults | Informational notifications default off; saved choices survive updates. Background pauses record ownership and transitions. | Quiet and opt-in paths, duplicate suppression, manual pauses, overlapping tasks, inactive arrays, temperature transfer, restart/partial checks, and increment-window restrictions. |
| 22: mover detection | Validate mover PID, inspect process arguments, and recheck PID ownership. Recognize native mover and the tuned mover script identities. | Missing, malformed, stale, overflowing, and reused PIDs; valid native/tuned commands; unrelated commands and shell command strings. |

Partial-check validation also runs on the server before creating a marker or invoking `mdcmd`. Percentage bounds are derived from array size and stored in the running-check marker so later settings edits cannot change the stop point. History protocol fields remain English while presentation is translated. The Defaults action reloads the reset configuration before regenerating cron entries.

## Repository support configuration

The subsequent repository-only update adds five issue forms, 27 label definitions, chooser links, and a narrow publication allowlist. The installed plugin remains `2026.11.04.02`; its package bytes and runtime source are unchanged. Ten focused issue-form/publication regressions pass, including duplicate-YAML-key rejection, missing label detection, optional diagnostics, and rejection of arbitrary GitHub configuration. At that point the full suite contained 129 methods; the 124-method runtime qualification above remains the preceding complete run.

Install development dependencies with `python -m pip install -r requirements-dev.txt` and validate forms with `python -B scripts/check_issue_forms.py`. Publication checks verified 20 public file copies against reviewed bytes, all 27 live label names/descriptions/colors, and all three documentation contact links exposed by GitHub. The default-branch commit changes exactly seven issue-support files; its prior README/LICENSE blobs and the installed plugin package remain unchanged.

GitHub's blank-issue permission is viewer-specific: the authenticated maintainer can still create a blank issue, as documented, while the published chooser configuration disables it for ordinary contributors. The available browser redirects the chooser to GitHub sign-in, so authenticated visual rendering remains a manual check. No test issues or diagnostic uploads were created.

## Run the checks

```text
python -B scripts/build_i18n.py --check
python -B scripts/build_package.py
python -B scripts/check_branding.py
python -B scripts/check_runtime_references.py
```

Run the full Python suite on Linux or WSL:

```text
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
```

Run the actual browser fixtures from the repository root:

```text
npm ci --ignore-scripts
npx playwright install chromium
python -B tests/render_fixtures.py
npm run test:ui
```

The renderer uses the official Unraid Markdown and translation parsers preserved in `tests/fixtures/unraid/`, with source blob identifiers in `sources.json`. It deliberately performs native inline translation before evaluating plugin code. Synthetic native helpers and task commands are isolated in temporary directories. Browser cases cover 42 canonical locales and three native locale aliases across Settings, Plugins, assistant, popup, and history pages; Settings and assistant also receive mobile overflow checks. An unrelated native Scheduler Apply control is included as a negative control.

## Runtime cleanup checks

`scripts/check_runtime_references.py` combines PHP token reachability from entry points/callbacks with named page JavaScript references. The native parser API in `Legacy.php` is explicitly treated as externally callable. Structural references complement the actual runtime/browser tests; they do not establish every dynamic host interaction or branch. The cleanup regressions also cover configuration preservation, removal of stale installed integration files, and diagnostic-only handling of partial progress after its marker is missing.

## Languages

The bundled registry combines Unraid's official `languages.key` with published language-pack variants. Danish, Japanese, and Korean support both registry codes and language-pack codes. There are 42 canonical catalogs and 45 exported native catalogs. Runtime translation is offline and follows the current Unraid session locale; an empty session locale resets to English.

Catalogs cover labels, full dialogs, help, CLI text, history presentation, and notification templates. Source extraction, key coverage, protected markup/links, positional printf placeholders, unchanged prose, and actual formatting calls are checked. Arabic, Persian, and Hebrew use RTL presentation while editable machine values remain LTR. Names, paths, command arguments, notification severity codes, configuration keys, and persistent history tokens remain literal.

Translations were machine authored with structural and browser validation; they have not received native-speaker review. Maintainer catalog generation uses `python scripts/build_i18n.py --translate`, which contacts a translation service. `--check` and installed plugin operation use no translation service.

## Acceptance limits

These automated checks establish local source, fixture, and package behavior. The development agent did not perform live Unraid installation, native `upgradepkg`, scheduled array operations, reboot, physical sensor transitions, or native mover runs. The owner's subsequently reported completion of the discussed host checks is recorded above as separate evidence. Neither fixtures nor acceptance on an unspecified host establish every third-party mover implementation, historical/future Unraid build, or deployment environment.

## Scheduler layout regression in 2026.11.03.05

The native grid previously received extra definition terms containing late-rendered help. This displaced notification, mover, temperature, action-button, and history rows. Explicit Markdown block separation keeps each label paired with its control; custom-field wrappers are closed and action buttons share a native spaced wrapper. No host-wide CSS overrides are added.

`npm run test:ui` also runs 810 native-grid layout cases using the official `default-base.css` fixture with Git blob integrity checks. Both Scheduler and Plugins routes cover 45 locale codes, 1920/1280/390 widths, and daily/weekly/custom schedules. Checks include optional fields, disabled groups, expanded help, untouched native Scheduler controls, and an extra-help-label negative control that recreates the reported failure. The original source was confirmed to fail this matrix before the fix. This remains synthetic browser evidence rather than live-host acceptance.

## Completion/canceled notification regression in 2026.11.03.06

A successful operation keeps its final status in history even if an earlier increment left a canceled entry. Plus saves history and merges errors before sending its summary. Genuine cancellations and errors remain alerts.

A narrow wrapper around Unraid's native `notify` entry point suppresses matching parity-finish duplicates for a tracked run or a delivered Plus summary. New/unowned runs, changed errors, unknown state, unrelated alerts, and management commands pass through. The native monitor retains ownership of its own state. The installer preserves the original notifier and restores it on removal.

Completion tests execute the parity section of the verbatim, blob-verified `tests/fixtures/unraid/monitor`. A temporary notifier captures delivery without contacting external services. A barrier holds the real analyzer during delivery while a native snapshot attempts to emit: it must wait and then suppress its duplicate. Other cases preserve cancellation/errors, resolve stale terminal progress, retain native fallback on failure, preserve unrelated history, and check notifier install/update/removal and pass-through behavior.

The 62-test suite covers deterministic monitor overlap, duplicate analyzers, real cancellation/error outcomes, pause/resume timing, stale terminal progress, missing/unmatched history, higher error counts, delayed snapshots, invalid/unowned identities, native command/argument/output/exit-code passthrough, failed history/delivery, and notification-hook conflicts/upgrade/restoration. These checks do not establish live Unraid host acceptance.
