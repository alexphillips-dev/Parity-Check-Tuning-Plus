# Runtime cleanup: 2026.11.04.01

This development update removes reviewed unused code, unfinished controls, and obsolete integration files. It retains implemented array-operation behavior, native compatibility, source notices, and stable state/history protocols. The prior [runtime audit](AUDIT-2026.11.03.md) remains a historical record; this document describes the subsequent cleanup.

## Removed files and surfaces

| Surface | Source evidence and cleanup |
| --- | --- |
| Inert button-refresh page | The retired page emitted no updater, script, or form. Its native Buttons registration and packaged file are removed, and the installer removes the stale installed file during an upgrade. Native Unraid remains responsible for button updates. |
| Nine event dispatchers | `driver_loaded`, `disks_mounted`, `svcs_restarted`, `docker_started`, `libvirt_started`, `stopping_svcs`, `stopping_libvirt`, `stopping_docker`, and `unmounting_disks` reached handlers with no operational action. Their files and handlers are removed; upgrade cleanup removes previously installed copies. |
| Unfinished Docker/container controls | The selection callback was empty, option generation was commented out, and no array-operation pause/resume owner consumed the settings. The controls, help targets, initialization, container-list helper, and shipped defaults are retired. |
| CLI history placeholder | The command only logged that it was not implemented. Its handler and help entry are removed. GUI history remains active. |
| Unused helpers | `endsWith`, `tempFromDisplayUnit`, `ParityTuningPlusSeverity`, and `dockerContainerList` had no active runtime callers. Their definitions and tests limited to retired utilities are removed. |
| Redundant page logic | The unused JavaScript weekday global, duplicate preset call, duplicate Assistant state read/local active copy, trivial `changeProblemType` forwarding wrapper, and obsolete popup-sizing proposal are removed. Native onchange now calls the live method directly. |
| Runtime scaffolding | Unused optional case-insensitive prefix and saved-drive-list branches, already-aligned restart adjustment, duplicate native configuration imports, one-iteration record-selection loop, unused assignments, unconsumed critical-drive accumulation, never-produced starting/spinup marker constants, and commented-out implementation proposals are removed. |
| Historical design notes | The old document contained Unraid 6.7 reverse-engineering notes, outdated statements, and misspelled protocol fields. Useful current facts are now documented from the checked source in the architecture/state guides. |

Two connected diagnostic defects were also reproduced and repaired: a trigger-conflict warning included an extra dollar sign, and an unknown-trigger warning read an undefined variable. Focused regressions cover both paths.

## Retained behavior and compatibility

- Six operational lifecycle dispatchers remain: `starting`, `array_started`, `started`, `stopping_array`, `stopping`, and `stopped`.
- `Legacy.php` remains conditionally loaded when native translation support is unavailable. Its parser API is also callable by the native host, so direct plugin-reference counts alone do not establish that those functions are unused.
- Modern and legacy native history-dialog paths remain. Browser interactions cover both branches.
- Native command sequencing, background ownership, temperature handling, restart validation, history reconciliation, and notification coordination remain under their existing owners.
- Older valid progress tokens remain accepted, including temperature and restart annotations. The writer preserves the established pipe-separated field schema even where a consumer no longer binds an unused column.
- Recognized partial progress with a missing running marker is saved as diagnostic evidence. It cannot create a full-array completion record/summary or invoke completion shutdown.
- GPLv2 license text, inherited copyright and permission notices, and attribution remain. Published Plus archives remain available as distribution inputs.

## Configuration and upgrades

Normal installer updates preserve the saved configuration rather than rewriting it to remove retired preferences. Existing `parityTuningPlusDocker` and `parityTuningPlusContainers` values are ignored by the current runtime. Fresh installations use the current defaults; **Defaults** explicitly replaces the saved configuration with that defaults file.

Dropping a file from a new package is not sufficient evidence that an existing installation no longer has it. Post-install cleanup therefore removes the old refresh file and the exact nine retired event files. Native integration backups and the six operational event files are retained.

## State facts retained from the checked implementation

The runtime observes `/var/local/emhttp/var.ini`. `mdResyncPos` and `mdResyncSize` use 1 KiB units; multiplying by two gives the 512-byte sector units used in offset commands. Start offsets align down to multiples of eight sectors. A positive position on a started array establishes an active operation; `mdResync` zero marks an active operation as paused.

Progress records retain operation type, readable timestamp, epoch time, native segment start/finish, errors/status, array state, running/position/size/correction/action fields, and an English description. Timing and position have different units; translated UI text does not become stored protocol identity. See the current [configuration/state guide](wiki/Configuration-and-State.md) and [architecture guide](wiki/Architecture.md) for the exact field order and native connections.

## Validation scope

Run the structural check from the repository root:

```text
python -B scripts/check_runtime_references.py
```

It tokenizes owned PHP without executing Unraid actions, follows entry-point/callback references, and treats the native parser API as explicit external roots. It also checks references to named JavaScript functions in page source. The check complements source review and behavioral tests; it is not an absolute proof of every dynamic host interaction or arbitrary branch's reachability.

Combined local qualification passed: **122 Python tests**, **225 browser page cases**, **945 native-grid layouts**, source parity for **114 packaged files**, and **42 locale catalogs** with **336 active messages** each and **45 native exports**. Runtime reference checks, 14 PHP/page syntax checks, manifest/checksum/metadata checks, and documentation checks passed. Windows and Linux builds produced identical package bytes.

The package SHA256 for `2026.11.04.01` is `91f23ffc30acb6d85c0a570c0751dbeb038d86e3aa523865227fac85b65c63a9`.

Regressions cover retired UI absence, retained history dialog fallback, active Assistant disabled/refresh behavior, stale-file upgrade cleanup, saved configuration preservation, partial-progress compatibility, and trigger diagnostics. The structural checker has negative controls for unreachable function cycles, literal callbacks, host parser contracts, and comments that mention otherwise-unused JavaScript.

Physical Unraid installation, disk I/O, native lifecycle/notification timing, actual sensors, real mover/backup transitions, and native-speaker wording review remain separate acceptance work.
