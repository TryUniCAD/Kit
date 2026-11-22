# Fusion cut review guards

The bounded cut reader now clips using the original source rectangle extrema. Contacts within the qualified 1e-9 mm tolerance use the stock edge as their canonical station. This accepts a native flush upper corner whose original maximum cannot be recovered exactly by adding its rounded width to its minimum. Source sketch coordinates remain unchanged.

Strict cut projection refuses populated `faceVisualMaterialByAttrTagID` maps until per-face appearances are projected. Every parsed planar face now checks that its boundary lies on its own saved plane, including open cache sheets; matching vertices and normal direction alone are insufficient.

## Explicit body history

`FeatureStep.OutputBodyIds` is an immutable tuple of persistent body identities produced or modified by a feature. Its JSON key is `output_body_ids`. Cut source projection fills this field for the stock and modifying steps. A distance cut must list the same target and output bodies and directly depend on one earlier producer for each target. Invalid body references, duplicate output IDs and reference features claiming body outputs refuse. Existing records without distance cuts retain their empty default. Earlier inspection JSON for the newly introduced cut type should be regenerated from its native source.

The converter recognizes the distance-cut feature kind, checks its active profile and generator inputs, and supplies body identities and full feature context to validation. This fixes the incomplete classification and context checks. It does not make a read-only or underconstrained source conversion-ready. The existing geometry contract and native writer barriers remain enabled. Full native conversion and round-trip acceptance remain unfinished.

## Native evidence and verification

The PC API authored a flush upper-edge control and a face-appearance control with healthy brackets. The flush control decoded strictly. The face-appearance archive refused at its unsupported native journal attribute family; the explicit semantic appearance-map guard also protects models that reach projection. Independent measurements and archive hashes are in `re/Fusion/Reconstruction/BoundaryCuts/ReviewGuardObservations.json`.

Public process-boundary integration replays cover the flush input, appearance refusal, an encoded displaced plane and a neutral cut detached from its prior producer. These tests are committed for remote execution and were not run locally. Actual CLI source decoding and static checks are recorded separately. No qualification guard was disabled and no native acceptance is claimed.

A separate public conversion replay requires a qualification refusal rather than an unknown-feature or missing-context failure, and verifies that no output is published. It is committed for remote CI and was not executed locally. Static checks passed for 53 changed Python files.
