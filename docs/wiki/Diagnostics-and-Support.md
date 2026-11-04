# Diagnostics and support

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

Use the [Unraid support thread](https://forums.unraid.net/topic/201158-plugin-parity-check-tuning-plus/) for discussion and troubleshooting. The plugin manager's **Support Thread** link opens that topic. Use the [Plus issue tracker](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/issues) for structured bug reports and feature requests. Support replies and host diagnostics are not uploaded automatically.

## Choose the right report

Open the [issue chooser](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/issues/new/choose).

| Form | Use it for | Automatic labels |
| --- | --- | --- |
| Bug report | Unexpected behavior; include exact versions, feature, operation type, expected/actual behavior, and the event sequence. | `bug`, `needs-triage` |
| Feature request | A use case, proposed behavior, and current workaround. | `enhancement`, `needs-triage` |
| Translation problem | Selected language, page/message, current wording, and an explanation or suggested correction. | `translation`, `needs-triage` |
| Documentation correction | A README/wiki/help location and incorrect or missing instructions. | `documentation`, `needs-triage` |
| Question / troubleshooting | Configuration questions or behavior that needs explanation; include what you already tried. | `question`, `needs-triage` |

The chooser also links to [Getting Started](Getting-Started), [Troubleshooting](Troubleshooting), and this guide. Blank issues are disabled for ordinary contributors; GitHub retains a maintainer-only blank option for users with write access or above.

Forms do not select priority or confirm a defect automatically. Logs/screenshots are optional, and the form does not request an email address or a full diagnostics archive. Preserve relevant evidence before applying Defaults or reinstalling. Do not interrupt an array operation merely to reproduce a report.

## Labels and triage

The reviewed [label catalog](https://github.com/alexphillips-dev/Parity-Check-Tuning-Plus/blob/main/.github/labels.json) defines 27 labels with descriptions and colors. All 10 original general-purpose label names are retained.

| Group | Labels and usage |
| --- | --- |
| Report type | `bug`, `enhancement`, `question`, `documentation`, `translation`; add `regression` when a previously working behavior broke. |
| Investigation status | `needs-triage` for new reports, `needs-info` when evidence is missing, `confirmed` for a verified defect, `needs-testing` for a proposed fix awaiting reporter/live Unraid confirmation. |
| Component | `area:scheduling`, `area:temperature`, `area:background-tasks`, `area:restart`, `area:notifications`, `area:history`, `area:assistant`, `area:installation`, `area:ui`. Apply relevant components during triage. |
| Priority | `priority:critical` and `priority:high` are maintainer-assigned after assessing impact. |
| Other retained labels | `duplicate`, `wontfix`, `accessibility`, `help wanted`, `good first issue`, `invalid`. |

Review new reports, apply relevant components, and remove `needs-triage` after classification. Request missing details with `needs-info`; incomplete information alone is not a reason to use `invalid`. Confirm defects using reproducible behavior or checked evidence. Replace obsolete status labels as investigation progresses. Link the original when closing a duplicate and explain decisions to close without a planned change.

Local synthetic success and physical host acceptance are separate evidence. A fix can remain `needs-testing` after local checks pass; link its development version/commit and record the reporter's actual result before closing it as resolved.

## Report contents

- Plus and Unraid versions.
- Mover/backup integration version when relevant.
- Selected language and entry route for UI/translation problems.
- Exact steps, expected result, and observed result.
- Operation category, relevant settings, and timestamps.
- Whether the operation was running, paused, completing, restarting, or idle.
- Relevant sanitized logs and state details.

## Logging levels

| Level | Intended use |
| --- | --- |
| Basic | Major operational events. |
| Debug | Additional activity/context useful during diagnosis. |
| Testing | Detailed internal observations for focused investigation. |

The UI restricts non-Testing modes to syslog. The raw default target is separate; inspect effective settings rather than assuming raw-file and UI-enforced values are identical. Testing logs can grow substantially. Do not leave flash logging enabled without a reason and file-size management.

## Preserve evidence

Capture state before refreshing, reinstalling, applying Defaults, or deleting markers. Those actions can discard the evidence needed to explain a mismatch. Success notifications alone do not establish correct persistence or native behavior.

## Sanitize before public sharing

Logs and disk snapshots can contain hostnames, serials, device identifiers, addresses, private paths, and unrelated application messages. Remove private/unrelated material while retaining relevant timestamps, error text, settings, and event order.

## Focused examples

- Pause/resume: window, mover/backup observations, heat state, and whether the pause was manual.
- Assistant: method, endpoints, reported size, correction choice, validation result.
- Installation: manifest version, checksum, preflight/post-install output, hook/backup ownership.
- Translation: locale code, route, exact phrase, suggested correction, and a sanitized screenshot.
