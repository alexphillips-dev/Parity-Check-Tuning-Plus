# Issue remediation in 2026.11.03.02

> Stable release: **2026.11.04.04** · Stable channel: **main** · Development channel: **dev**

The work addressed all five reviewed upstream issue areas. This describes local Plus changes/evidence; it does not claim upstream issues were closed or a physical host tested.

| Report | Plus change | Evidence |
| --- | --- | --- |
| 16: installation permissions | Deterministic safe metadata, prohibited root/unrelated paths, validated staged archive. | Historical metadata negative control; root-preserving extraction; source/package checks. |
| 17: version HTML | Matching runtime version path, format validation, escaped presentation. | Missing/empty/malformed/HTML-looking version fixtures. |
| 17: translations | Offline late lookup independent of native early parsing. | 42 catalogs, actual native parsers, 225 browser cases. |
| 17: assistant interactions | Correct setting binding, real button, scoped validation, popup behavior. | Mode/range/browser and popup escaping checks. |
| 19: endpoint help | Canonical help describes the end point. | Source/catalog and rendered help checks. |
| 21: background defaults | Informational messages off on fresh install; saved choices preserved. | Fresh/update configuration and quiet/opt-in transitions. |
| 21: connected state | Explicit ownership replaces undefined notification state; overlapping/manual/heat/restart/window coordination. | Synthetic transitions and actual pause/resume function checks. |
| 22: mover identity | PID/command validation replaces process-match counts. | Native/tuned positives and unrelated/stale/malformed negatives. |

## Connected repairs

- Defaults reloads reset settings before regenerating cron.
- Assistant validation runs on the server before an operation command.
- Percentage end bounds remain independent of later settings edits.
- Both parity slots are detected correctly.
- Active/idle CLI status avoids inherited string-arithmetic/inverted-branch failure.
- Stored history protocol fields remain English under translated presentation.
- Testing-mode CLI descriptions translate while action names remain literal.
- Settings validation preserves an unrelated native Scheduler Apply control.
- Failed archive generation does not expose a partially written final artifact.

See [development and testing](Development-and-Testing) and repository `docs/VALIDATION.md` for reproducible checks and their limits.
