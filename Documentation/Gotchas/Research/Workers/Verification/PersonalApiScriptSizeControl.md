# Native verification scripts must stay within the existing API size limit

## Expectation

Embedding two known control archives in a native verification script appears suitable for repeated before/after measurements.

## Actual behavior

The independent two-sided draft campaign produced control archives of about 200 kB each.
Their base64 payloads exceeded the private API's 256 KiB script limit.
All eleven initial verification preparations were refused with HTTP 400 before a native request was admitted.
The refusal was retained rather than counted as a native feature failure.

## Workaround

Carry one unchanged known control, using lossless transport compression, and measure that same archive before and after each source.
Bind its original SHA-256 in the verification report.
Check the fully rendered UTF-8 script size before submission.
Retain the original refusals and update queued template hashes through the controller before dispatch.
Do not raise the API limit or silently resubmit an unknown native request.

The [campaign package](../../../../../re/Fusion/TwoSidedDraft20261127/README.md) retains the corrected request worker and verification template.
This transport correction changes neither native model bytes nor decoder qualification.
