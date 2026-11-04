# Compatibility and limitations

> Stable release: **2026.11.04.04** · Stable channel: **main** · Development channel: **dev**

## Declared platform

The manifest declares Unraid `6.9.2` or later and supports current/legacy history hook locations. Source support does not establish acceptance on every Unraid version, controller, disk, theme, or plugin combination.

## Current evidence

Local source, synthetic filesystem/runtime, browser, catalog, package-integrity, and Windows/Linux reproducibility checks are available. Official parser fixtures include source blob identifiers.

Automated tests do not execute real Unraid `upgradepkg`, reboot an array, exercise physical disk temperatures, or run mover against storage. On November 4, 2026, the owner reported completing the discussed live Unraid acceptance checks for the tested runtime. No host/version/log details were supplied, and the development agent did not execute those host checks. The stable promotion leaves installed runtime source unchanged from the reviewed dev build; owner-reported acceptance does not establish every host/version/integration combination.

## Inherited areas needing focused qualification

- Restart attempts after array stop/start, shutdown, or reboot.
- Complex cron and active-window boundary behavior.
- DST/time-zone transitions.
- Native notification/lifecycle timing.
- Additional mover/backup variants and hook combinations.
- Spun-down disk temperature assumptions.

## Assistant timing

The assistant is a diagnostic workflow and stops through periodic monitoring rather than an exact endpoint interrupt. It does not replace a complete parity check after the underlying problem is addressed.

## Retired surfaces

The unfinished Docker/container controls, unimplemented CLI history command, inert button-refresh page, and nine event dispatchers without operational handlers were removed in `2026.11.04.01`. Existing retired preference values are preserved by a normal update but ignored. Native history dialogs and parser compatibility remain because they have active callers or host entry points. See [release notes](Release-Notes) and [architecture](Architecture).

## Localization

All 42 catalogs are bundled and checked, with three aliases. Machine-authored wording has not received native-speaker review. Coverage/browser success and wording quality are distinct.

## Channels

Stable release 2026.11.04.04 is published on `main`. Development updates publish on `dev`. Both update and archive URLs remain on the selected channel; future dev changes do not move stable installations to dev. A Community Applications listing is not implied by this release. See [installation and channel switching](Installation-and-Migration).

## Original-plugin comparison

The [original-plugin review](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/docs/UPSTREAM-COMPATIBILITY.md) compares the pinned 2026.04.24 distribution with current source. It documents retained behavior, independent configuration/migration, intentional bug fixes, and synthetic comparison limits. Version-branch fixtures do not establish installation on every physical Unraid release.
