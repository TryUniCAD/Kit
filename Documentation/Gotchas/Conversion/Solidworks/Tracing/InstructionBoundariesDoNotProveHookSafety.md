# An instruction boundary does not prove safe interception

## Expectation

A verified instruction boundary and matching original instruction hash are enough to install an inline observer.

## Actual behavior

An inline redirect can replace several complete instructions. Another branch may enter inside that span. The first proposed callback probe at `0x4c54c336` would overwrite bypass target `0x4c54c338`; the context tail at `0x4b7988c8` would overwrite null-branch target `0x4b7988cb`. These are static findings in the pinned model image, not observed application crashes.

## Workaround

Check five-/fourteen-byte minimum spans through complete instructions and record known incoming targets. The [identity metadata](../../../../../re/solidworks/records/RadialTrainingHooks2026.json) records rejected sites, revised sites and bounded incoming-target checks. Verify mapped instruction hashes before activation. Use checked interception; do not force relocation to fit an unsafe span. Preserve runtime rejection as a tool result. Whole-program indirect/exception target closure and actual relocator success remain separate evidence.

## A matching window can still fail checked relocation

The first root-owned training activation, frozen label `3a8`, verified all eleven mapped instruction windows, then Frida rejected UI site `0x492b031a` before any action or control. No model acceptance or native format-crash attribution follows. The old window spans an indirect call and its return boundary; that is a concrete online-interception concern, but the generic error does not prove the exact rejection cause.

The [actual attempt receipt](../../../../../re/solidworks/measurements/2026/RadialTrainingAuthor01.json) binds the failed capture and completed cleanup.
It records Frida 17.26.3, zero native events and confirmed host transport exit with code one.

The replacement `0x492b02fa` observes acquisition target/argument selection earlier. Its five-/fourteen-byte spans contain only loads and no known interior direct incoming target within the owning function. Mapped instruction verification and standard checked relocation remain required. Do not switch to forced, unchecked or offline behavior to obtain a pass. New runtime acceptance is pending; preserve the rejected capture unchanged. The [focused change](../../../../Changes/Solidworks/Inspection/Sketches/SolidworksListenerAcquisitionProbe.md) gives exact hashes and the deliberately weaker call-execution semantics.

## Public circle forwarding call

The first public-circle probe, source `dfc8071f9`, also matched all twelve pinned mapped windows before Frida rejected the indirect-call instruction at `0x456e06da`. No action, case or control ran; no crash is counted. The independently bound replacement is the earlier target-load instruction at `0x456e06ad`. Its complete wrapper has no intervening call, branch or target-register reassignment before the indirect call. It observes target selection with deliberately weaker callee-execution claims; checked relocation and fresh controls remain mandatory. The [failed receipt](../../../../../re/solidworks/measurements/2026/RadialTrainingAuthor05.json) preserves the original result.
