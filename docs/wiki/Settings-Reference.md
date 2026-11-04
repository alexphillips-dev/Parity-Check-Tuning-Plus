# Complete settings reference

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

The table is derived from checked `default.cfg`. Raw values do not imply that every field is visible or fully host-qualified. Prefer the UI for normal configuration.

| Raw key | Default | Meaning |
| --- | --- | --- |
| `parityTuningPlusScheduled` | `1` | Scheduled checks use increments. |
| `parityTuningPlusManual` | `0` | Manual checks use increments. |
| `parityTuningPlusAutomatic` | `0` | Automatic checks use increments. |
| `parityTuningPlusFrequency` | `0` | 0 daily, 1 custom, 2 weekly. |
| `parityTuningPlusResumeCustom` | `5,15,25,35,45,55 * * * *` | Five-field custom resume cron entry. |
| `parityTuningPlusResumeDay` | `0` | Resume weekday; Sunday is 0. |
| `parityTuningPlusResumeHour` | `0` | Resume hour in server time. |
| `parityTuningPlusResumeMinute` | `15` | Resume minute. |
| `parityTuningPlusPauseCustom` | `0,10,20,30,40,50 * * * *` | Five-field custom pause cron entry. |
| `parityTuningPlusPauseDay` | `0` | Pause weekday; Sunday is 0. |
| `parityTuningPlusPauseHour` | `7` | Pause hour in server time. |
| `parityTuningPlusPauseMinute` | `30` | Pause minute. |
| `parityTuningPlusNotify` | `1` | Increment pause/resume notification preference. |
| `parityTuningPlusRecon` | `0` | Optional parity-sync/data-rebuild increment handling. |
| `parityTuningPlusClear` | `0` | Optional disk-clear increment handling. |
| `parityTuningPlusRestart` | `0` | Attempt eligible restart after lifecycle interruption. |
| `parityTuningPlusShutdown` | `0` | Completion shutdown policy. |
| `parityTuningPlusMover` | `1` | Pause around recognized mover activity. |
| `parityTuningPlusBackup` | `1` | Pause around supported backup/restore activity. |
| `parityTuningPlusBackground` | `0` | Informational task notification preference, independent of pause behavior. |
| `parityTuningPlusHeat` | `0` | Temperature pause/resume policy. |
| `parityTuningPlusHeatHigh` | `3` | Pause offset below warning limit, Celsius. |
| `parityTuningPlusHeatLow` | `8` | Resume offset below warning limit; should exceed pause offset. |
| `parityTuningPlusHeatNotify` | `1` | Temperature notification preference. |
| `parityTuningPlusHeatShutdown` | `0` | Separate critical-temperature shutdown policy. |
| `parityTuningPlusHeatCritical` | `2` | Shutdown offset below critical limit. |
| `parityTuningPlusHeatTooLong` | `30` | Minutes for excessive heat-pause notification handling. |
| `parityTuningPlusLogging` | `0` | 0 Basic, 1 Debug, 2 Testing. |
| `parityTuningPlusLogTarget` | `1` | 0 syslog, 1 syslog+flash, 2 flash; UI forces 0 outside Testing. |
| `parityTuningPlusMonitorDefault` | `17` | Idle monitor interval, minutes. |
| `parityTuningPlusMonitorHeat` | `7` | Temperature-oriented monitor interval, minutes. |
| `parityTuningPlusMonitorBusy` | `6` | Active-operation monitor interval, minutes. |
| `parityTuningPlusMonitorPartial` | `1` | Partial monitor interval, minutes. |
| `parityProblemPlusType` | `sector` | Assistant method: sector or percent. |
| `parityProblemPlusStartSector` | `0` | Saved sector start. |
| `parityProblemPlusStartPercent` | `0` | Saved percentage start. |
| `parityProblemPlusEndSector` | `100` | Saved sector end. |
| `parityProblemPlusEndPercent` | `0` | Saved percentage end. |
| `parityProblemPlusCorrect` | `0` | 0 non-correcting, 1 correcting. |

## Important distinctions

- Fresh informational background messages default off; mover/backup pauses default on.
- Updates preserve saved settings rather than forcibly applying these defaults.
- Defaults replaces saved values, reloads them, and regenerates schedules.
- Raw log target defaults to 1. The UI forces target 0 in Basic/Debug; inspect effective values when diagnosing flash writes.
- Monitor fields control periodic cron observations, not instantaneous subscriptions.
- Percentage and sector fields are separate; backend validation derives the selected method's authoritative running range.
- Retired Docker/container keys can remain in saved configurations after a normal update, but current runtime code ignores them. Defaults intentionally replaces the saved file with the current defaults.

Read [scheduling](Scheduling), [background tasks](Background-Tasks-and-Notifications), [temperature management](Temperature-Management), and [assistant](Parity-Assistant) before changing policies.

## Apply and Defaults

Apply validates enabled increment schedules before saving. Defaults restores the shipped configuration even when the edited schedule is invalid. Each submission derives its command from the button used; a canceled Defaults submission cannot leave a reset selected for a later Apply. Defaults deliberately replaces saved preferences, while ordinary updates preserve them.
