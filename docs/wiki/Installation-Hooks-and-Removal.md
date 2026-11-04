# Installation hooks and removal

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

## Native integrations

Ownership is recorded through symlinks and separate backups, not inferred from a native path's name alone.

| Native path | Plus target |
| --- | --- |
| `/usr/local/sbin/mdcmd` | Runtime `parity.check.tuning.plus.mdcmd` |
| `/usr/local/emhttp/plugins/dynamix/scripts/parity_history` | Runtime `parity.check.tuning.plus.history.php` |
| Legacy `/usr/local/emhttp/plugins/dynamix/include/ParityHistory.php` | Same renderer for the legacy hook |
| `/usr/local/emhttp/webGui/scripts/notify` | `parity.check.tuning.plus.notify.php`, forwarding to the saved native notifier |

The backup suffix `.parity.check.tuning.plus.orig` is appended to the native path. The original is saved once and preserved through Plus updates.

## Lifecycle hooks and upgrade cleanup

The package retains six operational lifecycle dispatchers: `starting`, `array_started`, `started`, `stopping_array`, `stopping`, and `stopped`.

The `2026.11.04.01` installer removes the previously shipped inert refresh page and these nine event files during an update: `driver_loaded`, `disks_mounted`, `svcs_restarted`, `docker_started`, `libvirt_started`, `stopping_svcs`, `stopping_libvirt`, `stopping_docker`, and `unmounting_disks`. Their runtime handlers had no operational action. Explicit removal matters because dropping a file from a new archive alone does not establish that an existing installation no longer contains it.

This cleanup leaves saved settings and native-hook backups under their existing owners. Retired Docker/container keys in saved configuration are ignored; the installer does not reset the configuration to remove them. Defaults is the explicit action that replaces saved configuration with current defaults.

## Conflicts

Preflight rejects the previous tuning plugin and foreign native-hook symlinks. A missing required hook or backup is reported; the installer/remover does not invent a replacement.

## Removal sequence

1. Restore hooks still pointing to Plus from saved backups.
2. Remove the CLI link only if it still targets Plus.
3. Remove the package and invalidate Plus translation caches.
4. Remove Plus runtime and configuration/state directories.
5. Regenerate cron.

A hook replaced by another owner is preserved. A missing required backup stops removal before deleting the active integration. Temporary filesystem fixtures cover these paths.

## Permissions and archive safety

The package uses explicit root ownership and file/directory modes. It may not contain a filesystem-root entry, unrelated host paths, group/world-writable entries, unsafe special modes, or symlinks. A staged archive is validated before replacing the final artifact.

Local tests include unsafe historical root metadata as a negative control and verify extraction-root preservation. They do not execute Unraid's native `upgradepkg`; live install/remove qualification remains separate.

## Catalog caches

Only `paritychecktuningplus.dot` caches are invalidated. Other plugins' caches remain. Runtime lookup uses bundled JSON directly, so native page-entry order does not determine whether Plus strings are available.
