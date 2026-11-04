# Parity assistant

> Stable release: **2026.11.04.05** · Stable channel: **main** · Development channel: **dev**

Find the assistant under **Tools > Parity Check Tuning Plus**. Use it to investigate a selected range after parity/read-check problems have been reported. It does not replace a complete parity check after the underlying problem is addressed.

## Controls

| Control | Purpose |
| --- | --- |
| Method | Sector numbers or percentages, saved independently of correction choice. |
| Start point | Beginning of the requested range. |
| End point | Must exceed the start and remain within the reported size. |
| Write corrections | Choose correcting or non-correcting operation. |
| Show Sector Numbers | Open matching kernel parity entries from syslog. |
| Check | Submit when client validation permits it. |

The array must be eligible and started, another array operation must not be active, and a usable size must be reported. Missing size is rejected rather than guessed.

## Sector mode

Endpoints are non-negative whole numbers within bounds. The starting offset aligns down to a multiple of eight 512-byte sectors. Starting at sector 9 therefore uses aligned sector 8.

## Percentage mode

Use valid numbers between 0 and 100, with end greater than start. The backend computes actual bounds from array size rather than trusting stale browser-converted sector fields.

## Backend checks

Validation is repeated before creating a running marker or invoking `mdcmd`. Invalid, injected, out-of-range, or incorrectly ordered values do not start a check.

The running `parity.check.tuning.plus.partial` JSON stores `startSector`, `endSector`, `correct`, `kernelStart`, and `size`. The marker is bound to the observed kernel run, size, operation type, and correction policy. The monitor uses that stored end bound; later settings edits cannot silently move it.

## Timing and interpretation

Partial monitoring defaults to once per minute. The operation can pass the requested endpoint before the next observation and stop request. The selected end is not an exact physical I/O cutoff.

A correcting check writes parity corrections. Choose deliberately and understand the array state. Logged sectors alone do not identify whether the cause is a disk, cable, power, memory, or another subsystem.

## Popup

Kernel messages are escaped literal text, with machine values kept LTR where appropriate. HTML-looking log text cannot execute as markup. A blocked popup should not crash the assistant.

## Failure and update behavior

A native command must succeed and become active before Plus announces a partial start. A failed stop keeps its marker for retry and emits no completion notice. Unknown, malformed, stale, and legacy markers without kernel identity are discarded without canceling an operation. An already-running partial check created by an older build can therefore continue as a normal native check after updating; cancel it deliberately through native controls if needed. Changing assistant fields does not change the running range or correction label. The UI retains the native grid on desktop/mobile and with translated help.
