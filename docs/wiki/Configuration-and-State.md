# Configuration and state

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

## Locations

| Item | Location |
| --- | --- |
| Runtime | `/usr/local/emhttp/plugins/parity.check.tuning.plus/` |
| Persistent configuration/state | `/boot/config/plugins/parity.check.tuning.plus/` |
| Configuration | State-directory `parity.check.tuning.plus.cfg` |
| Displayed version | Runtime-directory `parity.check.tuning.plus.version` |
| Shared history | `/boot/config/parity-checks.log` |
| Native catalogs | `/usr/local/emhttp/languages/<locale>/paritychecktuningplus.txt` |
| Bundled catalog data | Runtime `locales/` directory |

## State suffixes

These use the `parity.check.tuning.plus.` prefix in the state directory.

| Suffix | Purpose |
| --- | --- |
| `cfg` | Saved settings. |
| `cron` | Generated schedules. |
| `progress`, `progress.save` | Observations and saved analysis input. |
| `restart`, `disks` | Restart information and disk-identity snapshot. |
| `scheduled`, `manual`, `automatic` | Trigger classification. |
| `increment` | Increment-window state. |
| `mover`, `backup` | Background observation/pause-ownership JSON. |
| `background.lock` | Serializes background-state handling. |
| `completion.lock` | Serializes history/notification analysis and matching native finish requests. |
| `completion.json` | Delivered-summary receipt: kernel start/end/status, category, reported errors, and creation time. New identities do not reuse it. |
| `partial` | Validated running partial range. |
| `hot`, `critical` | Temperature state. |
| `stopping`, `tidy` | Lifecycle observations. |
| `shutdown` | Completion shutdown policy marker. |
| `log` | Flash-target log when configured. |
| `history` and diagnostic suffixes | Copies/evidence around history processing. |

## Preserve relationships

Markers express decisions from different lifecycle stages. Removing one can discard ownership or evidence. Progress, restart information, and disk snapshots must describe the same operation. Do not copy markers from another installation or use deletion to force resume.

Use the UI for settings and collect evidence before changing state. Updates preserve configuration; Defaults replaces it and regenerates schedules; removal deletes the state directory.

The current defaults omit retired Docker/container settings. A normal installer update preserves existing configuration bytes; obsolete values are ignored by the runtime. Defaults deliberately resets the complete saved file to current defaults. The old `starting` and disk-spinup marker constants had no producer and are no longer part of the active runtime state surface.

## Language boundary

Keys, state identity, filenames, and protocol values are stable. Locale changes affect presentation. An empty Unraid session locale selects English.

## Validation and ownership

Kernel numeric fields must fit the host integer range; unavailable, incomplete, or corrupt state cannot create an active-operation claim. Reloading state refreshes displayed descriptions. Explicit scheduled/manual/automatic trigger markers are mutually exclusive. Restart state validates action, bounds, integer overflow, and correction flag; removed, added, or replaced array assignments prevent offset restart. Pool-only assignment changes do not invalidate the array snapshot. Canceled-history cleanup must match the saved operation, never just the latest canceled row.

## Progress record protocol

The progress writer stores a header followed by pipe-separated observations in this order:

```text
type|date|time|sbSynced|sbSynced2|sbSyncErrs|sbSyncExit|mdState|mdResync|mdResyncPos|mdResyncSize|mdResyncCorr|mdResyncAction|Description
```

Data rows retain the existing trailing separator. `date` is a human-readable timestamp and `time` is Unix epoch seconds. `sbSynced` identifies the native increment start and `sbSynced2` is its finish time when available; zero means no published finish. Runtime accounting uses segment timing and kernel-start identity. `sbSyncErrs` stores the error count, and `sbSyncExit` carries native status, including success `0` and cancellation `-4`. The writer preserves every field even when a particular reader does not bind an otherwise unused column.

Operation types, field names, action tokens, and stored descriptions remain English protocol values. The history renderer translates presentation without rewriting those values. Older temperature/restart annotations remain accepted. Recognized `PARTIAL`/`PARTIAL STOP` diagnostics do not establish a full-array completion: if their running marker is missing, analysis saves the progress as diagnostic evidence rather than generating a full-check history row, summary, or completion-shutdown action.
