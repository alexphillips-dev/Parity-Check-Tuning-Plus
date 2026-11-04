# Original-plugin compatibility review

This review compares Plus `2026.11.04.02` with the original plugin at
pinned commit `5580d8f2a93223c81d805fbe556b00385b3201a7`,
including its distributed `2026.04.24` package. The original archive SHA256 is
`f6f6458db47d08c16f29726e958642b09e9cf839d37444ae8ca5f82bb06ae71f`.
All 28 packaged files match the original repository after line-ending normalization
and accounting for its popup filename case difference. Neither the original CLI
entry point nor its installer was run against a host.

## Confirmed regression and repair

Plus had introduced form-wide schedule validation. With an invalid schedule,
**Defaults** set the hidden command to `defaults`, then validation blocked submission.
After correcting the entry, **Apply** could submit that leftover reset command.
The original form did not run this new form-wide validation.

The form now selects its command from the actual submitter on every submission.
Defaults can recover invalid schedules; Apply selects `config` before validating.
The browser regression exercises actual clicks, canceled submission, invalid
Apply, and a subsequent valid Apply. An event listener captures the native event
ordering and blocks network submission. This fix changes no translation keys,
default values, stored state, cron rules, or native host controls.

## Preserved contracts

| Area | Checked original/current behavior |
| --- | --- |
| Settings | All 39 retained keys/defaults match after naming normalization except the explicitly quieter background-information default. |
| Operation policies | Scheduled, manual, automatic, read-check, parity-check, rebuild/sync, and clear flag bindings retain their behavior. |
| Scheduling | Valid daily, weekly, and custom cron output retains the same native command forms and monitor intervals after naming normalization. |
| Kernel state | Running speed values above one remain valid. Paused state is an active operation with zero `mdResync`; malformed/stopped state is now guarded. |
| Position units | Native positions/sizes are in 1 KiB units. Command offsets use 512-byte sectors and align down to eight sectors. |
| Lifecycle | The six retained dispatchers have the same executable bodies after naming normalization. The nine retired handlers only exited. |
| Restart | Saved native state fields remain supported. New operation identity strengthens validation, with fallback for older restart files lacking `sbSynced`. |
| Progress/history | Original field order, trailing delimiter, older no-trailing input, HOT/COOL annotations, correction flags, and native action tokens remain readable. Native five-through-ten-field history presentation remains supported. |
| Assistant | All six form inputs remain; server validation enforces the original UI's no-parity restriction and binds the requested range to the operation. |
| Background activity | All three backup/restore marker paths remain; mover uses validated PID/process identity instead of process-list string counts. Manual pauses and overlapping tasks have explicit ownership. |
| Temperature | Pause/resume offsets and array-disk scope remain. Threshold inheritance follows native Unraid expressions, including disabled and inherited limits. |
| Notifications | Existing preference gating, severity/link arguments, descriptions, shell quoting, and error counts remain. Completion delivery now reconciles history and ownership before suppressing duplicates. |
| Native integration | Current/legacy history hooks/dialogs, conditional parser fallback, and native command argument protocols remain. Hook backup/ownership/restoration is tested. |

## Intentional differences

Plus is an independent plugin: paths, configuration keys, CLI name, package,
catalogs, and hook backups have their own namespace. **Original-plugin settings
are not automatically imported.** Remove the original integration and review
Plus settings before use. Normal updates between Plus versions preserve saved
configuration. Installation rejects conflicting native-hook ownership.

The background-information notification default changes from enabled to disabled;
automatic pause/resume remains enabled by its separate preferences. The unfinished
Docker/container controls, inert refresh page, and CLI history placeholder were
removed; GUI history remains. Copyright, permission notices, and GPLv2 remain.

Behavior repairs are intentional differences from upstream, including confirmed
native command outcomes, validated restart/partial state, real weekly/custom
windows, command-safe cron validation, native-compatible temperature inheritance,
critical protection independent of completion shutdown, and completion summaries
that do not inherit stale cancellation status. The preceding
[audit](AUDIT-2026.11.03.md) and [cleanup](CLEANUP-2026.11.04.md) document those repairs.
Matching a defective upstream result is not a compatibility requirement.

## Executed comparisons and regressions

The offline comparison checker verifies the original commit, manifest version,
archive checksum, and source/archive parity before executing extracted functions:

Provide a local checkout of that pinned baseline in the ignored
`build/upstream-verification` directory, then run:

```text
git -C build/upstream-verification checkout 5580d8f2a93223c81d805fbe556b00385b3201a7
python -B scripts/check_upstream_compatibility.py --upstream build/upstream-verification
```

Its **602 executable comparisons** cover 480 operation-policy combinations,
36 duration/temperature/drive-list/error-format cases, 24 native-state combinations,
30 cron/monitor cases, and 32 notification-policy combinations. Original identifiers
and notification branding are mechanically normalized; native side effects are
fixture callbacks. Nine stopped-array cases explicitly assert the safer inactive
result instead of inheriting upstream's stale positive-position interpretation.

An additional independent local matrix compared **768 cron scenarios** across all
32 increment-flag combinations, three frequencies, active/idle state, heat
monitoring, and partial monitoring. **384 temperature-threshold evaluations** matched
the exact expressions in the blob-verified native monitor fixture. These overlap
other coverage and are not counted as additional Python test methods.

The permanent completion regression covers **48 legacy-input cases**: four Unraid
version branches (6.9.2, 6.10.3, 6.11.0, 7.2.0), six operation/correction variants,
and both delimiter representations. It verifies 2,700 seconds of runtime, 3,600
seconds elapsed, two increments despite duplicate HOT/COOL annotations, one history
row, successful final status, unchanged native action tokens, appropriate history
column count, and one delivered summary. This executes the current analyzer in an
isolated filesystem, not each physical Unraid version.

The behavioral-comparison negative control changes the manual setting binding to
the scheduled setting: the checker must fail. A top-level exception in the fixture
also proves that the comparison extracts functions without executing CLI dispatch.

## Acceptance boundary

Final local qualification passed: **124 Python tests** (including the 48 legacy-input
subcases), **225 browser page cases**, **945 native-grid layouts**, all **42 locale
catalogs** with 336 active messages each and 45 native exports, PHP/reference checks,
and source parity for **114 packaged files**. The 602-comparison checker passed on
both Windows and Linux. Windows/Linux builds produced identical package bytes;
the `2026.11.04.02` archive SHA256 is
`c9720e3fd994c6ceddb4a6284b0b88fa7df941f9e7953eb8c0aa89cad3805667`.

These comparisons and the complete local suite provide evidence for the listed
contracts and repaired regressions. They do not prove that every host interaction
will succeed. Physical disk I/O, native `upgradepkg`, array-stop/reboot timing,
real mover/backup processes, sensor transitions, DST behavior, and every supported
Unraid build remain live acceptance work.

Before stable promotion, qualify on an Unraid test host: install/update/remove and
hook restoration; valid/invalid Apply and Defaults recovery; scheduled/manual
pause/resume; mover/backup overlap; non-correcting Assistant bounds; genuine
completion/cancellation/error notifications; history persistence; and optional
restart/thermal policies under controlled conditions. Record expected state and
actual native state separately from the notification text.
