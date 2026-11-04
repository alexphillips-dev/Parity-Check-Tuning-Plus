# Original issue remediation

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

The first stable Plus release includes the repairs begun in `2026.11.03.02` and the subsequent connected fixes. All five reports reviewed during that work are summarized below using their original issue numbers. These are Plus fixes; this does not claim the original tickets have been closed. See [Release Notes](Release-Notes) for the complete cumulative fixes, later audit repairs, and cleanup. Local synthetic evidence and owner-reported host acceptance are recorded separately in the validation guide.

| Report | Plus change | Evidence |
| --- | --- | --- |
| #16: installation permissions | Deterministic safe metadata, prohibited root/unrelated paths, validated staged archive. Prevent the packaging defect; do not change permissions on an already affected host. | Historical metadata negative control; root-preserving extraction; source/package checks. |
| #17: version HTML | Matching runtime version path, numeric format validation, escaped presentation, plain-text unknown fallback. | Missing/empty/malformed/HTML-looking version fixtures. |
| #19: endpoint help | Canonical help describes the end point. | Source/catalog and rendered help checks. |
| #21: background defaults | Informational messages off on fresh install; saved choices and automatic pause/resume preserved. | Fresh/update configuration and quiet/opt-in transitions. |
| #22: mover identity | PID/command validation replaces process-match counts. | Native/tuned positives; missing, unrelated, stale, reused, malformed, and overflowing PID negatives. |

## Connected repairs

- Offline late translation lookup works independently of native early parsing: 42 catalogs, actual native parsers, and 225 browser cases.
- Assistant setting binding, real button references, scoped validation, and escaped popup output are corrected; mode/range/browser regressions cover them.
- Explicit background pause ownership replaces undefined notification state and coordinates overlapping/manual/heat/restart/partial/window restrictions.
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
