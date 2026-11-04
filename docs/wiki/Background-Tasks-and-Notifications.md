# Background tasks and notifications

> Stable release: **2026.11.04.04** · Stable channel: **main** · Development channel: **dev**

## Detection

Mover detection validates `/var/run/mover.pid`, reads `/proc/<pid>/cmdline`, checks executable/script identity, and rechecks PID-file ownership. It recognizes native `mover`, the older mover script identity, and known `age_mover`/`share_mover` script names.

An unrelated grep, editor, Python command, or shell command string mentioning mover is insufficient. Missing, malformed, overflowing, stale, or unrelated PIDs are rejected.

Backup/restore detection uses the supported appdata backup marker paths in the current implementation. Other backup applications are not automatically supported because their names contain “backup”.

## Polling

Default intervals are 17 minutes for idle monitoring, 6 for active operations, 7 for temperature-oriented monitoring, and 1 for partial checks. A short task beginning and ending between observations may not produce a transition.

## Pause ownership

Background markers store JSON:

| Field | Meaning |
| --- | --- |
| `paused` | Plus owns the background pause for the observed blocker. |
| `notified` | Plus sent the start notification. |

Mover and backup are observed together under a background-state lock. Ownership can transfer through overlapping tasks. Finishing mover while backup remains active cannot cause an early resume.

A pre-existing manual pause is not acquired as a background pause. An explicit CLI pause releases background ownership. Temperature, partial-check, restart, and increment-window restrictions are checked before resume. Hot disks can transfer the pause to temperature handling.

## Notifications

Fresh informational background notifications default to **No**. Pause preferences remain independent. Updates preserve an existing saved choice.

Enabled task start/finish messages are paired through recorded state, avoiding repeated announcements on each poll. Unraid system notifications must also allow delivery.

Increment, heat, and informational background notifications are separate controls. Turning off delivery is not a way to disable the underlying pause policy.

## Completion coordination

Final progress status is reconciled with the kernel only for the same completed increment. An older history cancellation cannot replace that result. The latest matching native history entry is updated; missing/unmatched history receives a new record, preserving unrelated rows. Errors are merged before the message and severity are selected.

A successful operation keeps its final status in history even if an earlier increment left a canceled entry. Plus saves history and merges errors before sending its summary. Genuine cancellations and errors remain alerts.

A narrow wrapper around Unraid's native `notify` entry point suppresses matching parity-finish duplicates for a tracked run or a delivered Plus summary. New/unowned runs, changed errors, unknown state, unrelated alerts, and management commands pass through. The native monitor retains ownership of its own state. The installer preserves the original notifier and restores it on removal.

Only native parity/read-check/sync/rebuild/clear **finished** protocol messages enter coordination. Other arguments, output, and exit status pass to the saved native notifier. A shared completion lock serializes Plus analyzers and matching native finish requests. Progress can prove ownership of the current kernel increment. After Plus delivery succeeds, an atomic `completion.json` receipt records kernel start/end/status, category, reported errors, and creation time. A delayed snapshot is suppressed only when its identity still matches and its errors do not exceed the delivered summary.

A new run, changed kernel status, higher error count, invalid receipt, unknown state, or lock failure passes through. There is no arbitrary timeout that lets a delayed monitor revive the same duplicate. Failure to save history or deliver the Plus notification does not create a delivered-summary receipt. Existing notifications are historical; this affects subsequent processing. Live Unraid acceptance remains separate.

## Diagnose a mismatch

Record task states, whether the operation was already paused, the increment window, and temperature conditions. Preserve state before changes; do not delete ownership markers to force resume. See [diagnostics](Diagnostics-and-Support).
