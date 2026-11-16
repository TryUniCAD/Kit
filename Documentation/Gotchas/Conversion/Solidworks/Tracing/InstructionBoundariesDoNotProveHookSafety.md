# An instruction boundary does not prove safe interception

## Expectation

A verified instruction boundary and matching original instruction hash are enough to install an inline observer.

## Actual behavior

An inline redirect can replace several complete instructions. Another branch may enter inside that span. The first proposed callback probe at `0x4c54c336` would overwrite bypass target `0x4c54c338`; the context tail at `0x4b7988c8` would overwrite null-branch target `0x4b7988cb`. These are static findings in the pinned model image, not observed application crashes.

## Workaround

Check five-/fourteen-byte minimum spans through complete instructions and record known incoming targets. The [identity metadata](../../../../../re/solidworks/records/RadialTrainingHooks2026.json) records rejected sites, revised sites and bounded incoming-target checks. Verify mapped instruction hashes before activation. Use checked interception; do not force relocation to fit an unsafe span. Preserve runtime rejection as a tool result. Whole-program indirect/exception target closure and actual relocator success remain separate evidence.
