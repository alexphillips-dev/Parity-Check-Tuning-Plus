# Getting started

> Stable release: **2026.11.04.04** · Stable channel: **main** · Development channel: **dev**

## Find the controls

- Open **Settings > Scheduler** for the main Plus settings.
- Open **Tools > Parity Check Tuning Plus** for the assistant.
- Click a setting label or the Unraid Help icon to see explanatory help.
- Use the History control to view the shared array-operation history.

## First configuration

1. Confirm the displayed Plus version and installed Unraid version.
2. Check Unraid's native cumulative parity-check option. Avoid two increment schedulers managing the same operation.
3. Choose operation categories. Scheduled checks default on; manual/automatic checks, rebuild/sync, and clearing default off.
4. Review resume/pause times. Raw defaults are daily resume at `00:15` and pause at `07:30`.
5. Review background pauses. Mover and supported backup/restore pauses default on, while informational background notifications default off.
6. Leave temperature, restart, and shutdown options off unless you have reviewed their help and intend to use them.
7. Apply settings, then verify the generated schedule and observed behavior on a test host.

## What starts a check?

Normally Unraid starts the array operation and Plus controls when it runs. Configure normal monthly/daily starts in Unraid's Scheduler. Explicit CLI and assistant requests are separate operation-starting interfaces.

## What should be expected?

A check split into increments takes longer in calendar time than runtime. A paused operation remains an active operation for background coordination. Monitoring is periodic; task transitions and partial-check endpoints are not instantaneous.

The owner reports completing the discussed live Unraid acceptance checks for the previously tested runtime. That report and local validation do not establish every reboot/restart path, custom cron boundary, historical Unraid build, or third-party integration. See [compatibility and limitations](Compatibility-and-Limitations).
