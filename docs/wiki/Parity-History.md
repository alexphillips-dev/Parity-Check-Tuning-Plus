# Parity history

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

Plus works with `/boot/config/parity-checks.log` and can add incremented-operation information. The renderer exposes operation, date, size, runtime, speed, status, and errors, with elapsed-time/increment columns when extended layouts are handled.

## Runtime and elapsed time

Runtime is time actually running. Elapsed time includes pauses between increments. Thirty hours of work spread across days should not be interpreted as continuous running for the full calendar duration.

## Stable storage

Machine action tokens such as `check P`, trigger names, and stored extended descriptions remain English. Presentation translates separately, allowing history written under one GUI language to be read after switching languages.

The completed-history regression creates actual synthetic progress under Japanese, runs analysis, and checks that stored fields remain parseable English protocol values.

## Older layouts

Several historical Unraid/plugin field layouts are accepted. Missing extended values can show blank extra fields. Very old unsupported or malformed layouts may be skipped rather than guessed.

The renderer is integrated through a native hook with a Plus-owned backup. See [installation hooks](Installation-Hooks-and-Removal).

## Diagnose unexpected rows

Preserve relevant shared history rows and Plus progress information before refreshing, reinstalling, or removing files. Include starts, pauses, resumes, completion/cancellation, reboots, disk-assignment changes, and language changes.

Analysis reconciles state and can update shared history or interact with completion policy. The `analyze` CLI command is not a read-only viewer.

## Input and accounting safeguards

Supported five- through ten-field rows remain readable together. Very old four-field rows are ignored. Malformed duration/size/date rows are skipped, and displayed text is escaped. Duplicate pause/stop/restart observations count each kernel segment only once; duplicate resume observations do not add increments. The initial correction policy is retained if terminal metadata clears its flag. Corrupt progress is preserved for diagnosis and cannot take ownership of native finish notifications.

Valid older progress annotations remain compatible. Partial-check diagnostic records are kept separate from full-check history even if a running marker has been lost: analysis saves those records for diagnosis without claiming a full-array completion or invoking completion shutdown.
