# Frequently asked questions

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

## Does Plus start the monthly check?

Normally no. Configure regular starts in Unraid Scheduler. Plus manages selected execution behavior afterward. Explicit CLI and assistant requests can start operations.

## Why does a check take more days?

Work is spread over permitted windows. Pauses increase elapsed calendar time. Runtime and elapsed time are different history values.

## Why is a paused check active?

It still exists and can resume. Coordination distinguishes that from an idle array.

## Can I disable mover messages without losing pause handling?

Yes. Informational background messages are separate and default off on fresh installs. Pause preferences remain independent.

## Does finishing mover resume a manual pause?

Background handling records ownership and does not acquire a pre-existing manual pause. Other blocking conditions still apply.

## Can both tuning plugins coexist?

No. Their native hooks conflict. Remove the prior integration and recreate intended settings in Plus.

## Are old settings migrated?

No. Configuration keys and active state are not imported automatically into the new namespace.

## Does changing language alter history identity?

Stored protocol values stay stable; presentation translates separately.

## Does translation contact an online service on the server?

No. Runtime uses bundled files. Only maintainer authoring contacts a translation service.

## Is the partial endpoint exact?

No. The default monitor checks once per minute. The bound is retained, but the operation can advance beyond it before stopping.

## Does uninstall keep settings?

No. Removal deletes Plus configuration/state. Save desired settings first.

## Is dev stable-qualified?

Stable version `2026.11.04.05` is available on main. The dev channel can advance independently; future dev pushes do not automatically inherit stable qualification or change stable installations. See [compatibility and limitations](Compatibility-and-Limitations) for the boundary between local evidence and owner-reported host acceptance.
