# Paired SDK qualification for historical circle end conditions

| Delivery item | Scope |
| --- | --- |
| Task | `pr121-sdk-original-end-condition-heldouts` |
| Owners | Format proof lane for preparation, root for source custody and native execution |
| Delivery | PR #121 research only |
| Inputs | Historical `H03MidPlane` and `H04TwoDirections` |
| Dependencies | Current shared SDK circle constructor and reader, original pre-writer source locks, unchanged recursive circle observer and comparator |
| Exit | Immutable generated predictions, strict original SDK admission, clean paired native lifecycle and exact saved-output SDK readback |
| State | Both guarded predictions and strict source attachments pass. The corrected native packet passes. The separate centre ownership supplement passes all twelve SDK reads. |

## Independence and source identities

The [source specification](../../tooling/sw2026/EndConditionSpecs.json)
has SHA-256 `aaa4236ab265bef3ca5211b1cae9b558ad74bf2b4069e2568f51331bf74920a0`.
The [native source lock](../v2026/heldout/EndConditionSourceLock.json)
has SHA-256 `4df0938264f7761ada1f6fbc10f2335227459e6f03960ab1baa27a0395d395fe`.
The [source lock verification](../measurements/2026/EndConditionSourceLock02.json)
binds both exact digests and records that writer implementation was pending.
Its SHA-256 is `128134df5a77d52e84ca6e8bd2cd491b9a59ebd48c1f8458b79ca22b88e7573d`.
The older [writer freeze](../v2026/heldout/EndConditionWriterFreeze.json)
repeats both selected source identities. Its SHA-256 is
`fb208a5b8dd8cf9e033ad8450fd466e9754cf6374dc88bce68ee1bcd709a2918`.

| Input | Pre-writer native source SHA-256 | Paired semantics |
| --- | --- | --- |
| `H03MidPlane` | `5edfc5ccd7163fdcec4132e053a7dc0ee42603833af9028d8d8cc89cd4f373df` | Right Plane, diameter, symmetric mid-plane. Preserve the source primary-depth edit factor `0.91`. |
| `H04TwoDirections` | `0dd4ffe69b16248dda5ebd7e468563a45c4a8e5b80a8fe0bff5e12da02c584d0` | Reversed Top Plane, diameter, two active blind ends. Preserve the source secondary-depth edit factor `1.17`. |
| `ControlCircle` | `9bfb64f5570fdd7b23ea8118e2589d54d36b9c76f37a65633e33d9dc0daa58d0` | The same pristine pre-writer diameter-circle control for both brackets. Its Front blind profile matches circle and diameter. |

Each independent source lane is the same-mode native comparator.
Both pre-writer manifests are authenticated by digest before source attachment.
The native executable is `34.5.2.0604` with SHA-256
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.

The historical research writer already exercised generated geometry and driving
edits on this cohort. Its first tree walk was incompatible with the full native
reference walk. The later matched traversal documented 26 generated entries
and 25 source entries, including an additional generated notes-area folder.
That result remains a tree-parity failure for its own exact files. This trial
evaluates the independently frozen current SDK writer against the same
historical pre-writer cohort.
[Historical end-condition predictions](../../../Documentation/Changes/Solidworks/Inspection/Extrusions/SolidworksEndConditionHeldoutPrediction.md)
[Matched tree walk](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/FeatureTreeWalkDepth.md)

The working method used the tracked scalar specifications, source-lock
metadata and tool sources. The original payloads and older detailed
measurement data remain outside method preparation.

## Ordered custody and comparison

1. Run `freeze` in a new directory outside the checkout. Use the exact current
   shared SDK commit. The tool copies only tracked Git objects from `src` and
   its named host, observer and process dependencies.
2. Preserve `Method.json`, `SDK/FrozenSource.json` and the printed
   `GeneratedFreeze.json` digest before attachment. Each case uses two
   independent guarded builds, exact ten-stream typed preparation and a
   fourth isolated SDK read of the generated part.
3. Run `attach` with that freeze digest, the historical source root and the
   locked circle control. Attach runs a separate strict SDK source read
   for each original and records any unresolved input or owner in
   `Attachment.json`. A native packet requires both admissions.
4. Run the frozen observer wrapper in the owned SOLIDWORKS guest after
   verifying the packet digest. Use the same licensed build and normal
   before/after controls. Each source/generated lane uses open and save,
   fresh reopen with sequential edits, then edited fresh reopen. Both
   cases passing require 14 distinct native process identities.
5. Run `readback` with the original freeze, packet and native result digests.
   The strict SDK worker reads each original/generated input, first native
   save and edited fresh-reopen save in a separate process. Twelve successful
   reads include 24 exact linked Config/Resolved stream comparisons.

The [stage tool](../../tooling/sw2026/StageSdkEndConditionHeldouts.py)
accepts `freeze --workspace PATH --revision SHA`. Its four explicit metadata
options accept overrides with the same pinned digests. `attach` requires
`--workspace`, `--freeze-sha256`, `--originals`, `--control`,
`--shared-home` and `--checkout-guest`. The original root is the
parent of the locked `Heldout` and `Controls` role paths. The workspace
must be under the declared shared home at attachment time.

For native execution, use
`Packet/Tools/ObserveSdkEndConditionHeldouts.py PACKET --packet-sha256 SHA`
in the registered guest. Its result is `Packet/Inspection/Result.json`.
`readback` requires `--workspace`, `--freeze-sha256`,
`--packet-sha256` and `--native-sha256`.

## Measured roles and retained failures

The [circle rules](../../tooling/sw2026/SdkCircleHeldoutRules.py) compute
independent analytic axial intervals, volume, area, centre of mass and
six extrema from the locked neutral geometry at initial, radial, primary
and applicable secondary stages. The frozen part constructor receives
only the resulting neutral request. Each actual driving dimension remains
owned by its sketch or end. The SDK verifies `D1` at `f818.f18` and
active `D2` at `f818.f20`; H03 has no active second driver.

The [exact native observer](../../tooling/sw2026/InspectSdkCircleBodyTypes.py)
and [paired comparator](../../tooling/sw2026/CompareSdkCircleHeldouts.py)
check the complete ordered names, node types, parents, suppression and
diagnostics, all configuration names and active name, fixed-centre
relations, support transform, one visible solid, topology, paired mass
and density, analytic geometry and sequential editable dimensions.
Expected system rows come from the actual SDK recipe.

The [recording entry](../../tooling/sw2026/ObserveSdkEndConditionHeldouts.py)
saves returned recursive rows in the existing per-phase `Record.json`
before the exact observer compares them. An extra folder preserves the
original error and complete observed ordering even when it rejects the
phase. First failures and unsupported owners remain part of the result.
The observer stops at its first failure. Unreached states retain their
unmeasured status.
Both brackets and all paired states must pass before readback can attest
the bounded outcome.

The [initial packet receipt](../measurements/2026/SdkEndConditionObserverAttempt01.json)
records eight successful guarded generation/read processes and two strict
original attachments. Both native controls passed. The first original
reference reached its 25-row recursive tree, then attempted the absent
`IBody2.IsSolidBody` member. The three native processes opened no
generated file. The retry uses the existing corrected body observer
that reads `IBody2.GetType` and `GetVertexCount`. It retains the same
comparison predicates.
[Installed COM gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Parts/BodyTypeUsesGetType.md)

The corrected observer used the same two generated file hashes. All
14 distinct native processes passed, including both controls. Each
reference and generated lane kept its 25-row recursive native tree,
configuration, visible solid, analytic geometry and actual dimension
owners through edits, save and fresh reopen.

The frozen SDK replay passed ten of the twelve readbacks with 20 exact
linked Config and Resolved stream comparisons. Both generated mid-plane
saves stopped on an exact fixed-point versus circle-centre comparison.
The two-direction candidate and both original reference lanes passed
all three readbacks. The original partial readback receipt has SHA-256
`35fa6556f82f7312cceeb8ba689416ce8d36de7be185de795c54a1e1a67973a5`.
[Paired case measurements](../measurements/2026/SdkPairedEndConditionsNative01.json)

## Shared centre readback supplement

Both generated H03 saves store the same raw X and Y for one native centre.
The actual `sgArc.fdc` selector and the code-17 fixed relation's
`sgPointHandle.idx` target the same point row. The point marker's preceding
u32 matches that row's `f0c` identity. Its raw metre coordinates match the
typed row bit for bit. The separate diameter handle targets the sole arc.
The radial display handle refers to the same `sgSketch` object.

The public circle follows the typed centre in metres multiplied by 1000.
The saved point marker rounds to 12 places in millimetres and cleans
near-zero values. For H03's generated saves, the two X projections read
`4.971000000000001` and `4.971` mm. They differ by one binary64 step,
`8.881784197001252e-16` mm. Y agrees exactly. The H03 reference and
all H04 readback states give exact public coordinate equality.

The [separate reader](../../tooling/sw2026/ReadSdkEndConditionCentres.py)
checks each public projection against its exact rule and proves the common
native owner. It executes the frozen worker body with a separate binding
for that one predicate. The remaining SDK checks run through the original
worker. All ten previously successful states reproduce their reported
values. Twelve fresh processes re-emit 24 complete linked Config/Resolved
streams byte for byte.

H03's primary driver reads `33.971` and `30.91361` mm before and after
the actual edit. Its second driver is absent. H04 reads primary
`21.389` and `17.603147` mm and secondary `8.917` and `10.43289` mm
in both native lanes. The worker checks the actual active slots
`f818.f18` and `f818.f20` and preserves the bound centre and diameter.

The supplemental method and receipt bind the native result, prior failed
SDK readback and separately frozen 5,017-file SDK source. Both artifacts
carry the supplemental code SHA-256. The native observation remains
evidence for geometry. The host reader requests sketch and feature
semantics with B-rep and tessellation disabled.
[Supplemental method](../measurements/2026/SdkEndConditionCentreReadbackMethod01.json)
[Twelve-case readback](../measurements/2026/SdkEndConditionCentreReadback01.json)

Native appearance, drawing and assembly behavior and additional source
owners require separate evidence. Full document properties, assigned
material and public writer qualification remain open.
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
