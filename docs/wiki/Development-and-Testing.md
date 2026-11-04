# Development and testing

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

Inspect intended files, callers, state owners, and tests before editing. Work/publish on `dev` unless another action is explicitly authorized. Local agent instructions and workspace configuration are not public repository inputs.

## Offline catalog check

```text
python -B scripts/build_i18n.py --check
```

Checks extraction, coverage, protected markup/links, positional printf placeholders, unsafe markup, and unchanged prose. Neither this check nor installed lookup contacts a translation service.

## Package checks

```text
python -B scripts/build_package.py --branch dev --dry-run
python -B scripts/build_package.py --branch dev
python -B scripts/check_branding.py --branch dev
python -B scripts/check_runtime_references.py
```

The builder validates a staged archive before final replacement. Checks include canonical same-channel update/archive URLs, source parity, checksums, modes/ownership, case-sensitive references, settings/help connections, and PHP/page syntax.

## Synthetic suite

Install development-only issue-form dependencies first:

```text
python -m pip install -r requirements-dev.txt
python -B scripts/check_issue_forms.py
```

The form checker validates five YAML forms, label references/metadata, unique fields, optional diagnostics, and chooser links. Negative controls reject duplicate YAML keys, a missing automatic label, and required diagnostic uploads. Publication tests reject arbitrary GitHub workflows/private files despite the narrowly allowed support files. GitHub's live chooser is checked separately after default-branch publication. PyYAML is not included in the installed plugin.

Run on Linux/WSL:

```text
python3 -B -m unittest discover -s scripts -p 'test_*.py' -v
```

The suite has 143 tests covering installer/remover ownership, root metadata, failed-build preservation, mover identity, manual/overlap/temperature pause state, partial bounds, versions, defaults/status/history, locale switching, printf execution, escaping, parser-fixture integrity, all-language Testing-mode CLI help, publication boundaries, runtime references, compatibility, and cleanup behavior. One completion test includes 48 legacy-input subcases; a comparison negative control detects a deliberately changed setting binding.

Completion tests execute the parity section of the verbatim, blob-verified `tests/fixtures/unraid/monitor`. A temporary notifier captures delivery without contacting external services. A barrier holds the real analyzer during delivery while a native snapshot attempts to emit: it must wait and then suppress its duplicate. Other cases preserve cancellation/errors, resolve stale terminal progress, retain native fallback on failure, preserve unrelated history, and check notifier install/update/removal and pass-through behavior.

## Browser fixtures

```text
npm ci --ignore-scripts
npx playwright install chromium
python -B tests/render_fixtures.py
npm run test:ui
```

The 225 cases combine 42 canonical locales and three aliases with Settings, Plugins, assistant, popup, and history routes. Settings/assistant also receive mobile overflow checks. Actual Unraid Markdown/translation parsers reproduce translation-before-evaluation order. An unrelated Scheduler Apply control is a negative control.

The additional `tests/settings-layout.cjs` matrix uses the official native stylesheet recorded in the fixture registry. Its 945 layout cases cover Scheduler, Plugins, and Assistant routes, all 45 locale codes, widths 1920/1280/390, and daily/weekly/custom schedules. Optional backup, temperature, critical-temperature, and background fields are exercised; disabled groups, expanded help, unrelated native controls, and a malformed-row negative control are checked. Browser assertions require the retired Docker controls/help to be absent and retain positive cases for native history dialog fallback, active Assistant controls/refresh scheduling, and popup behavior.

## Runtime reference review

```text
python -B scripts/check_runtime_references.py
```

The checker tokenizes owned PHP code without executing Unraid operations, builds references from entry points and callbacks, and follows the resulting function graph. Native parser functions in `Legacy.php` are explicit external roots: `_`, `parse_lang_file`, `parse_help_file`, `parse_text`, `parse_file`, and `parse_plugin`. They are host compatibility entry points, not unused functions merely because a direct plugin call is absent.

Named page JavaScript functions are checked for references after comments are excluded. This structural check complements source review, runtime fixtures, and browser interactions. It does not prove every dynamic host path or branch reachable, and it must not justify removing native hooks or protocol compatibility without inspecting their owners. See the [cleanup report](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/CLEANUP-2026.11.04.md) for the reviewed removals and retained behavior.

## Translation authoring

```text
python -B scripts/build_i18n.py --translate
```

This maintainer operation contacts a translation service, uses resumable caches, protects literal markup/protocol components, rejects damaged output, and regenerates native exports. Review overrides and wording. Passing tests is not native-speaker review.

## Publication validation

After staging explicit reviewed paths, run `python -B scripts/check_publish_files.py`. It checks exact index bytes and packaged members rather than trusting ignore rules or later worktree edits. Regressions verify force-added local instructions, unexpected files, staged secrets, workstation paths, and archive bypass attempts. Use a secret scanner for broader detection and review findings locally; do not publish raw scan reports. See [packaging and publishing](Packaging-and-Publishing).

## Live acceptance

The `2026.11.04.01` local candidate passed the complete 122-test Python suite, 225 browser page cases, and 945 native-grid layouts. Catalog, runtime-reference, source/package, syntax, documentation, and Windows/Linux reproducibility checks passed. Exact package checksum and retained-host limits are recorded in the [cleanup report](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/CLEANUP-2026.11.04.md).

Do not label fixtures as physical install/reboot/mover/temperature validation. Record host, theme, language, integration versions, and operation category during live testing.

## Comprehensive audit

The [source audit report](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/AUDIT-2026.11.03.md) maps findings to regressions. Added tests cover real fixture CLI execution, accepted and failed native commands, critical protection, inherited temperature limits, restart validation and bounded waits, operation identity, corrupted state, and duplicate progress. Browser checks reject invalid custom schedules, honor weekly days, recover Apply after valid edits, and preserve unrelated Scheduler controls.

## Compare the original distribution

The [compatibility review](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/UPSTREAM-COMPATIBILITY.md) pins the upstream commit and original package checksum. Provide a local checkout of that pinned baseline in the ignored `build/upstream-verification` directory, then run:

```text
git -C build/upstream-verification checkout 5580d8f2a93223c81d805fbe556b00385b3201a7
python -B scripts/check_upstream_compatibility.py --upstream build/upstream-verification
```

The checker verifies source/archive parity and runs 602 comparisons without running either CLI entry point or native host actions. The permanent negative control detects a changed manual/scheduled binding. The completion suite additionally covers 48 original-progress/version/operation cases. Actual button-submit tests cover invalid Defaults recovery, blocked invalid Apply, and valid Apply after a canceled reset.

## Stable-channel preparation

The [channel guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/STABLE-CHANNEL.md) describes the shared branch entity, strict update/archive URL checks, non-writing preview, isolated main candidate, and explicit native channel switching. Runtime/configuration/hook identity does not vary by channel.
