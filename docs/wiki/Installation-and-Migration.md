# Installation and migration

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

## Channel install URLs

Stable (`main`, recommended release channel):

```text
https://raw.githubusercontent.com/alexphillips-dev/Parity-Check-Tuning-Plus/main/parity.check.tuning.plus.plg
```

Development (`dev`, for development updates):

```text
https://raw.githubusercontent.com/alexphillips-dev/Parity-Check-Tuning-Plus/dev/parity.check.tuning.plus.plg
```

Use **Plugins > Install Plugin** in Unraid and paste the chosen published URL. The manifest declares a minimum Unraid version of `6.9.2`. Its explicit branch entity keeps both future update checks and the matching archive download on that channel. Stable version 2026.11.04.05 is published on main; future main promotions remain explicit maintainer actions.

## Before installation

- Finish or deliberately resolve active array work before changing ownership of tuning hooks.
- Record the settings you intend to recreate.
- Remove the previous parity tuning plugin and conflicting command/history integrations.
- Review the [declared compatibility and acceptance limits](Compatibility-and-Limitations).

Preflight blocks the previous plugin when its manifest or runtime directory exists. It also rejects native-hook symlinks owned by another integration. Investigate conflict messages rather than deleting arbitrary native files.

## Independent settings

Plus uses `/boot/config/plugins/parity.check.tuning.plus/`. Keys use `parityTuningPlus` and `parityProblemPlus` prefixes. No automatic configuration or in-progress-state migration is implemented.

Recreate settings through the UI. Do not copy old restart, progress, temperature, or background markers. Copying a configuration using other key names does not convert it into a Plus configuration.

## Installation sequence

1. Preflight checks inspect conflicts before changing hooks.
2. The installer checks the downloaded archive against its pinned SHA256.
3. The package installs Plus files and native catalogs.
4. Post-install preserves native backups, installs Plus symlinks, and creates the CLI link.
5. Fresh defaults are copied only if the Plus configuration does not exist.
6. The runtime version is written and `config` generates cron state.

## Updating Plus

An existing configuration is preserved. Only stale Plus `.dot` caches are invalidated. Native backups are not overwritten merely because Plus is updated.

The runtime cleanup also removes obsolete installed integration files: the inert button-refresh page and nine no-op event dispatchers. Six operational lifecycle hooks remain. Previously saved Docker/container preference values can remain in the preserved configuration, but no current controls or runtime actions consume them. Defaults intentionally replaces saved configuration with current defaults. See [installation hooks and removal](Installation-Hooks-and-Removal).

Use Unraid's normal plugin update mechanism for the installed channel, then verify version and settings. Installer success alone does not prove runtime state or persistence.

## Switching Plus channels

Finish active array work, save relevant settings, check the target channel/version, and explicitly install its manifest. Do not uninstall just to switch: removal deletes configuration/state. Equal/older versions may require the native Force Install option; review any downgrade and the controls supported by the installed Unraid version. The plugin identity, preferences, CLI, and native hook backups remain shared. Verify the installed version/update URL and preferences afterward. See the [complete channel guide](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/STABLE-CHANNEL.md).

## Removal

Removal deletes Plus configuration/state. Save desired settings before uninstalling. See [installation hooks and removal](Installation-Hooks-and-Removal) for restoration rules and missing-backup behavior.
