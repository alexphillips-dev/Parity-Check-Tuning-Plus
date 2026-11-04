# Parity Check Tuning Plus

> Stable release: **2026.11.04.04** · Stable channel: **main** · Development channel: **dev** · Maintainer: **alexphillips-dev**

Parity Check Tuning Plus manages the execution of long-running Unraid array operations. It can apply scheduled increments, coordinate pauses around mover/backup activity, monitor temperature conditions, and extend operation history. The assistant can investigate a selected range after parity-error sectors have been identified.

## Start here

1. [Installation and migration](Installation-and-Migration): install the stable channel and understand the independent namespace.
2. [Getting started](Getting-Started): review defaults before relying on schedules.
3. [Scheduling](Scheduling): connect Unraid's start schedule with the plugin's execution windows.
4. [Settings reference](Settings-Reference): every raw default and its purpose.
5. [Compatibility and limitations](Compatibility-and-Limitations): distinguish implemented code from live-host acceptance.

## User guides

- [Background tasks and notifications](Background-Tasks-and-Notifications)
- [Temperature management](Temperature-Management)
- [Parity assistant](Parity-Assistant)
- [Parity history](Parity-History)
- [CLI reference](CLI-Reference)
- [Languages and accessibility](Languages-and-Accessibility)
- [Troubleshooting](Troubleshooting)
- [Diagnostics and support](Diagnostics-and-Support)

## Maintenance and development

- [Configuration and state](Configuration-and-State)
- [Installation hooks and removal](Installation-Hooks-and-Removal)
- [Architecture](Architecture)
- [Development and testing](Development-and-Testing)
- [Packaging and publishing](Packaging-and-Publishing)
- [Issue remediation](Issue-Remediation)
- [Release notes](Release-Notes)
- [FAQ](FAQ)

The first stable release, 2026.11.04.04, is published on `main`; its manifest and package-download URLs remain on main. Development installations follow `dev`. Future dev pushes do not change the stable channel or create a Community Applications listing. The owner reports completing the discussed host acceptance checks; this is separate from automated evidence. Native-speaker translation review remains outstanding. Read the [complete stable release notes](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/releases/2026.11.04.04.md).

The current validation suite includes 134 Python tests, 225 browser page cases, and 945 native-grid layout cases. The [comprehensive source audit](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/AUDIT-2026.11.03.md) records the preceding runtime audit. Local fixture/package results and physical Unraid acceptance remain separate.

The `2026.11.04.01` [runtime cleanup](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/CLEANUP-2026.11.04.md) removes unimplemented controls and unused integration files while retaining native compatibility, operational lifecycle hooks, and language-neutral progress/history fields. See [release notes](Release-Notes) for upgrade behavior and retired preferences.

The [original-plugin compatibility review](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/UPSTREAM-COMPATIBILITY.md) records the checked baseline, compatibility evidence, Settings reset fix, and live acceptance boundary.
