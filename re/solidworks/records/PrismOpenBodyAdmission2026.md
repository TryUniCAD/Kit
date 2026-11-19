# Ordinary prism body admission on SOLIDWORKS 2026

The generated prism still opens normally with warning 32 and zero exposed solids. A separate single-stop probe returns one body from the kernel during the same warning-producing open. The error publisher is the ordinary part configuration path. [Controlled native receipt](../measurements/2026/PrismOpenBodyAdmission01.json)

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
