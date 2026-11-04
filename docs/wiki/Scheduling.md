# Scheduling

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

## Two schedules with different jobs

Unraid's Scheduler starts normal scheduled parity checks. Plus controls pause/resume windows after an operation exists. Plus does not normally generate the monthly parity-check start event.

Scheduled, manual, automatic, parity-sync/data-rebuild, and disk-clear categories are configured independently. Extending rebuild/sync or clear work also extends the time before that operation finishes; those choices default off.

## Daily increments

Set resume and pause times. Raw defaults are `00:15` and `07:30`. For three-hour windows, use `00:15` and `03:15`. A 30-hour operation may then span about ten windows, before other pauses and interruptions.

Times use the server's configuration. Windows can span midnight. Editing a schedule does not itself create a new monthly check.

## Weekly increments

Select days as well as clock times. Cron uses Sunday as day `0`. Active-window evaluation uses days and minutes within the week, including Sunday/Monday crossings. Resume is inclusive and pause is exclusive. Clock-controlled regressions cover the boundary; actual cron execution and DST remain host acceptance work.

## Custom increments

Use five fields:

```text
minute hour day-of-month month day-of-week
```

For example, `15 0 * * *` represents a daily `00:15` event. Pause/resume entries must not be identical. The UI and backend validate field bounds, lists, ascending ranges, positive steps on stars/ranges, and three-letter month/day names. Command text, newlines, zero steps, out-of-range values, and identical normalized schedules are rejected. Monitor minute intervals must be whole numbers from 1 through 59.

Supported syntax follows the standard five-field subset described in [crontab(5)](https://www.man7.org/linux/man-pages/man5/crontab.5.html). Extensions such as `L`, `#`, `?`, and macros are not supported. Custom windows follow scheduled pause/resume events through an increment marker; idle monitoring preserves that marker. Changing pause/resume jobs clears it, while changing only monitor cadence preserves it. Invalid configuration preserves the last valid cron file. Complex schedules and DST/time-zone changes still need focused host testing. Do not edit increment markers as a scheduling method.

## Other pause conditions

Background activity, temperature, manual requests, and restart state affect execution. A background task finishing does not justify resuming a pause that Plus did not own.

## Inspecting schedules

Plus generates `parity.check.tuning.plus.cron` in its configuration directory and invokes Unraid's `update_cron`. Inspect that file during diagnosis. It is regenerated from configuration and is not the authoritative settings source.
