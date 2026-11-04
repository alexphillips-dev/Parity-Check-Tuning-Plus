# CLI reference

> Stable release: **2026.11.04.04** · Stable channel: **main** · Development channel: **dev**

The installer creates `/usr/local/bin/parity.check.plus` as a symlink to the Plus PHP entry point. That command name participates in CLI-mode detection; invoking the PHP file directly is not identical.

```text
parity.check.plus help
parity.check.plus status
```

| Action | Behavior |
| --- | --- |
| `help`, `--help` | Show usage without an unrecognized-option error. |
| `status` | Report state through shared reconciliation helpers. |
| `pause` | Request pause; explicit CLI pause releases background resume ownership. |
| `resume` | Request resume through plugin checks. |
| `analyze` | Analyze eligible progress and update history. |
| `check` | Use the inherited scheduler-mode-selection path. |
| `correct` | Explicit correcting-check request when allowed. |
| `nocorrect` | Explicit non-correcting-check request when allowed. |
| `cancel` | Request cancellation. |
| `start`, `stop` | Request array start/stop on supported versions. |
| `config` | Log/reload configuration and regenerate schedules. |
| `updatecron` | Regenerate plugin cron entries. |
| `defaults` | Replace settings, reload defaults, and regenerate schedules. |
| `partial` | Start from saved assistant inputs after backend validation. |

## Operational effects

These entry points share lifecycle/history reconciliation. They are not a guarantee of side-effect-free inspection. Start, stop, cancel, and correcting commands have operational effects. Use explicit `correct`/`nocorrect` when reviewing the requested mode directly rather than inferring the inherited `check` selection.

View history through the GUI History control. The former unimplemented `history` CLI placeholder was removed from the command handler and help.

## Testing-mode help

Testing mode exposes descriptions for additional maintenance actions. All 42 catalogs translate those descriptions; action names remain literal. Changing language must not change command syntax.

## Missing command or version

Inspect the CLI symlink and runtime entry point after installation. Do not point the link at another plugin. For `unknown` version, inspect the runtime version file and installation evidence using [troubleshooting](Troubleshooting).

## Confirmed native transitions

`check` maps native `write=NOCORRECT` to a non-correcting request and an empty native write option to a correcting request; missing preference defaults to non-correcting. Full and partial starts require a started array and observed active operation. Failed pause/resume/cancel requests do not announce success. Successful CLI cancellation retains the original operation description.
