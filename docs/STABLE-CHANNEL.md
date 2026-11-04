# Stable and development update channels

Stable release `2026.11.04.04` is published on `main`, with its matching manifest
and package. Development builds are published separately on `dev`. Both channels
retain their own update and download URLs. Version `2026.11.04.03` introduced the
channel-preparation tooling; the first stable release includes all earlier Plus fixes.
Read the [complete release notes](releases/2026.11.04.04.md) before migrating.

## Channel contract

The root manifest declares `<!ENTITY branch "dev">` or `<!ENTITY branch "main">`.
Both `pluginURL` and the archive download URL expand the same branch entity.
The builder and package validator reject unknown branches, wrong identities,
foreign URLs, or a self-update/archive URL pair from different channels.

| Channel | Manifest | Package |
| --- | --- | --- |
| Stable | `https://raw.githubusercontent.com/alexphillips-dev/Parity-Check-Tuning-Plus/main/parity.check.tuning.plus.plg` | `main/archives/parity.check.tuning.plus-<version>.txz` |
| Development | `https://raw.githubusercontent.com/alexphillips-dev/Parity-Check-Tuning-Plus/dev/parity.check.tuning.plus.plg` | `dev/archives/parity.check.tuning.plus-<version>.txz` |

The native Unraid plugin manager reads the installed manifest's `pluginURL` when
checking for updates. A stable installation therefore follows `main`, and a
development installation follows `dev`. New dev pushes do not change the stable
manifest. The native behavior was checked in
[Unraid's plugin manager](https://github.com/unraid/webgui/blob/master/emhttp/plugins/dynamix.plugin.manager/scripts/plugin).

Channel selection does not change the plugin ID, CLI, configuration directory,
configuration keys, native hook paths/backups, archive naming, or numeric runtime
version format. The two channels share one installed plugin; they are not side-by-side
installations. When installed source is identical, archive bytes and hashes are
identical across channels; the root/snapshot manifest URLs differ.

## Build and validate dev

From the dev checkout after selecting a new unused manifest version:

```text
python -B scripts/build_package.py --branch dev --dry-run
python -B scripts/build_package.py --branch dev
python -B scripts/check_branding.py --branch dev
python -B scripts/check_docs.py --branch dev
```

Without `--branch`, the builder preserves the already declared channel. Validators
default to `dev`, so accidentally changing dev metadata to `main` cannot pass normal
dev validation. The dry-run validates and previews without creating directories,
rewriting manifests, or changing archives/checksums. Invalid input is rejected
before any package output is written.

## Prepare an isolated main candidate

Do not run a main build in the active dev checkout. It rewrites the root manifest
and that version's archived manifest snapshot. Prepare a separate candidate from
the reviewed dev commit, preserving all unrelated work:

```text
git worktree add --detach build/stable-candidate dev
python -B scripts/build_package.py --root build/stable-candidate --branch main --dry-run
python -B scripts/build_package.py --root build/stable-candidate --branch main
python -B scripts/check_branding.py --root build/stable-candidate --branch main
python -B scripts/check_docs.py --root build/stable-candidate --branch main
```

Inspect a pre-existing candidate directory/worktree instead of overwriting or
deleting it. The `--root` option performs local preparation only; it does not
merge, commit, push, install on a host, or create a release. Run the appropriate
functional suite and installation/channel regressions against the final candidate.

Before a separately authorized promotion, integrate current main changes, review
the full promotion diff, preserve the issue forms and existing notices, and check
the candidate's main URLs, package/hash/snapshot parity, version, documentation,
and settings/hook preservation. Preserve historical published artifacts on each
branch. Branch-specific root/snapshot manifests must not be blindly synchronized
back into dev; dev must retain its own update/download channel.

After authorized publication, verify public main manifest/archive/checksum bytes
and confirm that the installed manifest's next update check still points to main.
Preparing a local main candidate does not prove that the public main URLs exist.

## Installation and explicit channel switching

Use the chosen published manifest URL in **Plugins > Install Plugin**. The main
URL installs the stable release; dev is an explicit development-channel choice. Ordinary updates remain on the installed channel. A merge or a new dev
build does not automatically switch existing installations.

To switch an existing Plus installation, finish active array work, save the relevant
settings, review the target version, and explicitly install the target channel's
manifest. Do not uninstall Plus merely to change channels: removal deletes its
saved configuration/state. The installer preserves existing Plus configuration and
native backups during a normal install/update.

Unraid can refuse reinstalling an equal or older version. Current native Unraid
provides **Force Install** for that case; use it deliberately only after checking
the target version and host compatibility. Installing an older target is a
downgrade, not an automatic channel update. Consult the native controls available
on the installed Unraid version rather than assuming every historical UI exposes
the same option. See the checked
[native installation page](https://github.com/unraid/webgui/blob/master/emhttp/plugins/dynamix.plugin.manager/PluginInstall.page).

After switching, verify the displayed version, selected manifest/update URL, saved
preferences, and native hook ownership before starting new work. This channel
switching policy applies to Plus-to-Plus installations. It does not import settings
from the original plugin or allow both implementations to own the hooks.

## Acceptance evidence

The combined local suite passed **134 Python tests**. Four channel methods cover
dev/main/dev package identity, canonical XML-expanded URLs, immutable installed
scripts/version fields, no-write previews, historical snapshots, mixed/foreign
metadata rejection, and failure-before-artifact-write behavior. The 17-test installer
suite includes an explicit dev/main/dev switch preserving configuration and native
backups, followed by correct native-hook restoration on removal. Both dev and
isolated-main package/documentation validators passed. Windows/Linux builds produce
the same archive SHA256,
`c9720e3fd994c6ceddb4a6284b0b88fa7df941f9e7953eb8c0aa89cad3805667`.

On November 4, 2026, the owner reported completing the live Unraid acceptance
checks discussed before stable preparation. This records owner-reported acceptance
of the previously tested runtime; no host/version/log details were supplied, and
the development agent did not run those physical-host checks. This update changes
channel/build metadata and documentation, not installed runtime behavior. It does
not imply acceptance on every supported Unraid version or third-party integration.
