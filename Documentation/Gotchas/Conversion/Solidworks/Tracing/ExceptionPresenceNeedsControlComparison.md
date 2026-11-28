# Compare native exceptions against a healthy control

## Expected

An exception observed while opening a generated file identifies its defect, and
an accurate-backtrace request supplies a usable native call chain.

## Observed

The 2026 frame observer recorded 79 handled system exceptions in a healthy
control that opened and rebuilt with zero feature errors or warnings. Several
provider backtraces contained only non-code values. The generated candidate
also raised system exceptions before a distinct null-pointer access violation.
Only its immediate copy-constructor chain was independently corroborated.

The [selected evidence](../../../../../re/solidworks/v2026/evidence/TupniInitialFrame.json)
records the input hashes, exact application build, profiles, counts and fault.

## Workaround

Run a healthy control in the same mode with the same observation profile.
Keep exception presence separate from document failure and validate relevant
frames against the exact binary before deriving a field rule.
Forward exceptions unchanged. A passing control does not establish that an
observer is neutral for every invalid input.
