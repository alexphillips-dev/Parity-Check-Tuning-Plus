# Temperature management

> Stable release: **2026.11.04.04** · Stable channel: **main** · Development channel: **dev**

## Relative thresholds

Settings are offsets from Unraid warning/critical limits, not absolute temperatures. With a warning limit of `45°C`:

| Setting | Offset | Result |
| --- | --- | --- |
| Pause | 3 | `42°C` |
| Resume | 8 | `37°C` |

The resume offset should exceed the pause offset so its resulting temperature is lower. This hysteresis avoids repeatedly switching near one threshold.

Explicit nonnegative per-drive limits take precedence; zero disables that limit. Negative per-drive values inherit native NVMe-reported limits, SSD overrides, or general Unraid limits. Malformed or negative Plus offsets use shipped defaults in memory without rewriting saved settings. The implementation uses Celsius internally and converts display values where required.

## Pause/resume

Monitoring is disabled by default. When enabled, the heat marker identifies a temperature pause. Cooling must satisfy configured resume conditions and the relevant operation increment window. Native command status and observed state must confirm pause/resume before success notices or marker removal. Failed eligible resumes retain the heat marker for retry. Background handling cannot override an existing heat pause, and cooling cannot resume while a background blocker remains active.

Spun-down disks may lack readable current temperatures. The inherited handling includes assumptions for that case and has not been qualified on every physical disk/controller combination.

## Critical shutdown

This is separate and disabled by default. It does not require completion shutdown or enable heat pausing. Critical monitoring covers available array and pool disks even while idle, stopped, restarting, or running an assistant check. Unknown/spun-down temperatures cannot be evaluated. The saved shutdown policy is reread before the power command, including after the notification delay. The default offset is 2 below the configured critical limit: a `55°C` limit gives `53°C`.

Shutdown affects more than parity performance. Review built-in help and validate the intended policy on a test host before enabling it.

## Excessive pause notification

The raw `parityTuningPlusHeatTooLong` default is 30 minutes. A heat pause remaining above the resume threshold can produce the corresponding notification when heat notifications are enabled.

## Reporting

Include native warning/critical limits, per-drive overrides, Plus offsets, temperature units, observed disk temperatures, and pause/background/cooling order. One later temperature screenshot does not establish the state during an earlier transition.
