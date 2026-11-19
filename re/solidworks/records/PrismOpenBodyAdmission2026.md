# Ordinary prism body admission on SOLIDWORKS 2026

The first cache-bearing generated prisms opened with warning 32 and zero exposed solids. The later disclosed authored-light and linked-output comparison reaches a clean first solid. A separate single-stop probe returns one body from the kernel during the same warning-producing open. The error publisher is the ordinary part configuration path. [Controlled native receipt](../measurements/2026/PrismOpenBodyAdmission01.json)

Task `B04-SW2026-DRAWING-DOWNSTREAM-ID`, [PR #121](https://github.com/TryUniCAD/Kit/pull/121). Root ran the disclosed diagnostic on SOLIDWORKS 2026 SP05.2 build 34.5.2.0604 in the reserved Windows 11 ARM64 guest. The generated input was the matching-clock prism, SHA-256 `3c6e2216c9ecaff27c8a5897b87653cffa5681df71940c9b7104d27a9eaddd03`. All three batches have separate healthy starting and trailing controls. No batch invokes rebuild or save. [Generated input and prior clock comparison](DownstreamPrismCacheNative2026.md#body-clock-and-ordinary-load-route)

## Open results

| Condition | Open error / warning | Body count immediately after open |
| --- | ---: | ---: |
| Ordinary open, cold/warmed and writable/read-only | 0 / 32 in all four modes | 0 |
| Warmed, 15-second delay | 0 / 32 | 0 |
| Warmed, debugger attached with no execution breakpoint | 0 / 32 | 0 |
| Warmed read-only or cold writable, detach at receive return `0x3305aeac` | 0 / 0 | 1 |
| Cold writable, resume at the same receive return before detaching | 0 / 32 | 0 |
| Cold writable, detach immediately before kernel receive or after the call-wrapper destructor | 0 / 0 | 1 |
| Cold writable, detach at kernel body enumeration return `0x3305af1c` | 0 / 32 | 0 |

The receive-return probe measured kernel status 0 and a positive partition tag in both the detach and resume cases. The body enumeration probe measured kernel status 0, count 1, and a returned tag array. Its open nevertheless exposed zero bodies through COM. The four warning-free instrumented opens match the control volume, area and centre of mass to six significant figures. Their clear warnings and live mass remain specific to the debugger intervention.

Two separately instrumented opens capture these additional values before an RPC failure ends their native observation:

- Ordinary `moPart_c::loadExternalBodies` reports inventory 1 at `sldmodu 0x4c23edeb`.
- At `sldappu 0x458a1760`, the internal API error is 128 and the verified caller return is `sldprtu+0xf21e9`, preferred address `0x333921e9`. This lands immediately after the matching part-module error publisher at `0x333921e3`. The API maps the internal status to warning 32.

The attempt to observe the instruction immediately after storing the receive status returned Parallels transport exit 255 without a guest receipt. It contributes zero measured processes. The recorded results total 20 fresh processes and six healthy controls. [Ordinary loader phases](OrdinaryPartPartitionLoad2026.md) · [Kernel wrapper sites](PartitionReceive2026.md)

## Replay and boundary

Run [the ordinary mode matrix](../../tooling/sw2026/InspectPrismAdmissionMatrix.py) in the configured guest with the hashed native bracket, hashed native warm-up file, matching-clock generated prism and an unused output path. It queries SOLIDWORKS before any rebuild. The same-shape bracket uses the separately native-saved derivative from the clock experiment.

[The scoped execution probe](../../tooling/sw2026/ProbePrismOpenBoundary.py) accepts the same warm-up and generated inputs plus the pinned DbgEng DLL. It verifies the selected loaded CAD image, takes a single AMD64 hardware execution stop, reads only the matching flag, counts or caller identity and detaches from the owned process. With `--continue-after-hit` it removes the breakpoint while stopped and continues the original open before detaching. Licensed executables and debugger binaries stay outside the repository.

REA independently verified the two original DLL identities used for the kernel and API sites with evidence `ev_3018c7fdee5f2a82046dcf45d138b7dc07856ad3ef61daae4c2c92936f663430` and `ev_8a3a9ec5f7b78577ec8cc321dc50cd2badf38139215b3628281a8c6bf8872842`. The normalization receipt hashes each measured phase and the two checked-in observation tools.

The exact `uiPartDoc_c::iiConfigureMAIN` source publishes error 128 after its part update predicate or update-error fallback, with a separate API/server condition. The remaining condition lies between successful kernel body enumeration and ordinary model exposure. Continue through actual regenerated feature/atom admission and the inputs to that result. Count uninstrumented held-out edit, save and reopen results for writer acceptance. [Part rebuild warning sources](PartRebuildWarning2026.md)

## Persisted body bookkeeping

The two generated matching-clock prisms store selected `CMgr.f360.f6f8` equal to 0 and part `f2c` equal to `0x100`. The same-shape native save, a native edited prism and the bracketing native control each store the count 1 and part `f2c` equal to `0x8120`. All five have one selected configuration, a partition stream, and zero stored part and configuration `f0c` flags.

The 2026 configuration serializer at `0x4c217e30` calls part virtual `+0x12b0` for the applicable current model. The actual part method forwards to `moAtomManager_c::getNumberSolidBodies` with no visibility or feature filtering. Store writes the signed result at `0x4c218400`; load reads it at `0x4c218f33`. The past count has a distinct slot at `+0x6fc`. The ordinary part loader compares its selected configuration count against the actual returned total at `0x4c23f589`. When the saved count exceeds that total, it requests an update and clears the body publication. A zero stored count and one returned body do not meet that condition.

The separate model flags are set by the native force-rebuild path and its ordinary model callback. The research composer can model these two changes independently while retaining the same geometry, atom relationships and body clock. The intended comparison uses the full typed writer and a normal, uninstrumented open, with the new body count derived from the actual generated solid atom. [Rebuild flags](PartitionReceive2026.md#other-observed-differences) · [Typed preparation](../../tooling/sw2026/downstream/PreparePrismCacheNative.py)

Eight freshly generated files cover all combinations of both changes across two ordinary prism shapes. The guarded constructor records zero runtime input reads, and a separate typed read confirms the intended count and flags for each file. Two additional guarded builds, using the earlier matching-clock recipe with downstream ID allocation omitted, reproduce its original files byte for byte.

Ten fresh native processes include two passing bracketing controls. All eight generated combinations still return warning 32 and zero bodies before rebuild, then rebuild to one correct solid with zero feature problems. The count and flags preserve their independent format rules. The missing condition remains in the ordinary body and feature publication path. [Controlled native comparison](../measurements/2026/PrismSavedBodyBookkeeping01.json) · [Count and update-state source](PartBodyAdmissionState2026.md)

## Live part update operands

Separate controlled opens of the same generated input establish three positive runtime facts. The ordinary `replaceBody` call receives a real body and feature map. Its internal `getAtomId` returns 101 with the actual feature list and map present. The later part update call reads live node `f0c=1` for the generated file and `f0c=0` for the same-shape native save. Both use mode 1 and have cached update mode, cached flags and part recovery flags equal to zero. Their persisted part `f0c` is zero.

The six measured processes include three clean controls. Every generated probe continues with the debugger attached after the capture and returns warning 32 and zero public bodies. The later gate-return trial received transport exit 255 with no guest receipt. The individual stops establish the native operands and one measured state difference. [Native operand receipt](../measurements/2026/PartBodyAdmissionOperandsNative01.json) · [Atom selection and getter source](PartBodyAtomBinding2026.md)

## Environment insertion and the first measured part dirty write

Two new single-site batches stop on the first relevant transition from clear to set at the real part node's dirty store `sldmodu 0x4c03ee0e`. The filters verify the actual `moPart_c` table and require the old and pending words to differ in bit 0. Both runs capture old word 0, pending word 1, requested state 11 and `moFeature::setNeedsUpdate` return `0x4bb516e5`. The actual feature receiver is environment folder ID 9. The caller is `moConcept::addFeature`, return `0x4bda6384`.

The expanded run reaches the same store through environment insertion return `0x4b493612`. Its actual dirty-enable and name-registration arguments are respectively 1 and 0. The inserted member has ID 27 and a vtable at preferred address `0x4cda45d0`. Original RTTI and the current serialize map identify that concrete table as `moAmbientLight_c`. These IDs belong to this observed file.

All four ordinary bracketing controls open cleanly with one body. Both generated cases continue the original open with the debugger attached until open returns and reproduce warning 32 and zero bodies. The two new batches measure six separate processes. These are separate processes from the replacement, atom ID and late gate probes. The initial dirty-stop attempt had no guest receipt and is excluded. [Native dirty-store receipt](../measurements/2026/PrismFirstPartUpdateNative01.json)

The next single-site run confirms the complete caller chain. The document post-load stage sees an environment list with no recognized lights and calls the session default-light builder. The actual ambient light reaches the environment wrapper through the feature insertion path. Both ordinary controls open cleanly. The generated part returns warning 32 and zero bodies. [Post-load condition and source](PartEnvironmentDirtyPropagation2026.md) [Extended native receipt](../measurements/2026/PrismEnvironmentPostLoadNative01.json)

Two pairs of generated prisms then isolate an independently authored ambient light. Each pair retains the same partition and complete downstream cache. In ordinary uninstrumented opens, the light clears warning 32 and leaves the save flag clear. Each variant still needs a rebuild to expose its one solid. Both healthy controls and all four subsequent rebuilds pass. [Controlled authored ambient comparison](../measurements/2026/PrismAuthoredAmbientNative01.json)

## First application solid query after open

Eight fresh processes, including four healthy ordinary brackets, observe the first SOLIDWORKS `GetBodies2(0, false)` after a clean cold open. The debugger arms after `OpenDoc6` returns. Both inputs return zero errors, zero warnings and a clear rebuild state.

The same-shape native part returns one solid and its backing native array contains one entry. The generated part returns an empty array without backing storage. Both calls use the ordinary `moPart` body getter and actual manager with visibility 0, body type 3, no feature filter, and ID filter 0. The part update word and separate ordered-cache switch are clear in both cases. One initial manager attempt ends at Parallels transport with no guest record. Its successor observes the same manager arguments in the generated lane. [Native query receipt](../measurements/2026/PrismPublicBodyInventoryNative01.json) · [Manager enumeration rules](AtomManagerBodyEnumeration2026.md)

### Manager owner and extrusion output identity

A second post-open comparison checks the live manager's part pointer, type and ordered tree. The runtime model flags are `0x0c` in both files. Both managers have the actual part owner and a nonempty tree, with two entries in the native control and one in the generated file. Two filtered lookup stops remain unobserved. The debugger detaches from both owned processes through the fallback after direct breakpoint removal reports an error. A third filtered attempt has no guest receipt. [Manager and typed file comparison](../measurements/2026/PrismPublicBodyInventoryDetailNative01.json)

Independently, the exact file graphs tie active body 102 to the native control's extrusion 21. Its other atom, 101, shares the generated file's atom ID and body-match tag. The generated active partition references its atom 101 through the manager. Its extrusion 21 lacks the output object array and corresponding ID list. The records show the actual owner IDs of these two files.

The prior source comparison binds the live output count and object membership checks that precede publication. The diagnostic writer now joins the existing generated atom to the creating extrusion. The same actual atom object appears in the config manager and the resolved output array. The signed output ID derives from that atom. Two pairs of same-locator builds change only ResolvedFeatures and retain the exact partition bytes. Six guarded generations read no data during model or stream construction. [Attachment and publication source](PartBodyAtomBinding2026.md) · [Preparation receipt](../measurements/2026/PrismExtrusionOutputPreparation01.json)

### Cold body admission through the resolved extrusion output

Both generated linked prisms expose one solid on their first ordinary open, before any rebuild. Both unlinked counterparts open with zero warnings and expose zero solids. Every part has a clear initial rebuild state and save flag. The six guarded source builds retain identical partition bytes for each shape, and the two same-locator comparisons differ only in ResolvedFeatures. The two normal native inputs for each shape use distinct self locators.

On clean cold open, both linked bodies match the independently calculated volume, surface area and centre of mass within the recorded tolerance. Depth changes from 8 to 10.31 mm and from 9.75 to 6.45 mm both rebuild, save and freshly reopen with the expected solid and retained driving dimension. Eight distinct SOLIDWORKS processes complete the comparison, including both clean native controls. The ordinary cases use no debugger and capture the first body count before rebuilding. [Controlled native receipt](../measurements/2026/PrismExtrusionOutputNative01.json)

This demonstrates source-saved body admission for the two disclosed no-cache, authored-light prisms. Full cache consumption, generalized neutral lowering and held-out qualification remain open.
