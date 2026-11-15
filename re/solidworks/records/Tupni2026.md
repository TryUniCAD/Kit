# Tupni usage in SOLIDWORKS 2026 recovery

Status: adopted during the active 2026 native-writer investigation on
2026-11-15 UTC. A native process-identity observation succeeded and detached.
The first loader/status capture succeeded. A subsequent loader-site observation
identified a rejected runtime class schema and led to two binary-backed schema
corrections. A later archive-context observation identified a constructor seed
that the native configuration store path replaces with its target version.
No completed instruction taint trace, corrected native acceptance
or measured speedup is claimed yet.

The user requested both use of Tupni and a record suitable for future reverse
engineering. The reusable procedure is in
[the playbook](../../Playbook/Tupni.md). This ledger records actual execution
and evidence as the investigation advances.

## Baseline before adoption

The branch already contained a shared object-archive codec, constructor-backed
model/profile/metadata/style/unit candidates, eight source-corpus critical-stream
round trips and linked archive-map verification. These were recovered using
static binary analysis and source-corpus inspection. They are not Tupni results.
The fresh composition entered remote CI at
`53c79e7394b8ec579cec799625575bf4d692c98d`; it had no generated-file vendor
acceptance. The production adapter remained read-only.

Open questions include general post-build sketch rules, transient persistent-id
allocation, final header counters, cache neutralization, unmodeled classes,
assemblies and the remaining feature families. A successful component codec
round trip does not resolve these questions.

## Adoption record

| Step                  | Actual observation                                                                                                                                                              | Evidence class and limit                                                        |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Read primary method   | Read field, loop, handler, constraint, aggregation and limitation sections of the CCS 2008 paper                                                                                | Literature source; no target execution                                          |
| Select trace boundary | 2026 archive cursor is at `su_CArchive+0x38`, end at `+0x40`, map counter at `+0x50`; target decompressed archive reads rather than treating compressed payloads as flat fields | Existing static binary evidence in [reverification](../v2026/Reverification.md) |
| Check host route      | REA exposed local/socket/barebone Frida device routes; this does not expose the Windows VM automatically                                                                        | Tool availability only                                                          |
| Check VM runtime      | `platform.machine()` reported ARM64, pointer size 64-bit; `frida` was absent from its module search                                                                             | Passive host report; executable architecture was not established by this string |
| Select dependency     | Official Frida release and PyPI metadata identify 17.26.3 Windows ARM64 builds                                                                                                  | Version-pinned acquisition metadata; attachment not yet proven                  |

The verified PyPI wheel candidate is
`frida-17.26.3-cp37-abi3-win_arm64.whl`, SHA-256
`9277d3562abc1131e67f128e042528972c30a58bb3b746918a81420789a5d228`.
Private research acquisition does not add a CAD or tracing dependency to Kit's
production writer.

The first attachment setup failed before Frida initialization: importing the
ARM64 extension into the installed Python returned Windows error 193, `%1 is not
a valid Win32 application`. A subsequent passive PE-header read established that
`Python312/python.exe` is machine `0x8664`, compiler `MSC v.1941 64 bit (AMD64)`.
The host architecture string did not identify the extension ABI. The original
attempt produced no native events and no capture JSON because import preceded
the runner's exception record; the runner was repaired to record initialization
failures and executable/extension image identities. This is a setup finding,
not a recovered CAD format rule.

The matching x64 wheel from the same official release is
`frida-17.26.3-cp37-abi3-win_amd64.whl`, SHA-256
`f91b80f3e5f72eaffb63ee5d0a5f49e63fdb91d35cc7dc2d6540b31c3a8f3833`.

## First native observation

The x64 Frida build loaded into the x64 Python interpreter. An attachment with
`realm=emulated` failed with `ProtocolError('emulated realm is not supported on
this OS')`; no events were collected. Changing the declared realm to `native`
successfully attached to the selected `SLDWORKS.exe` process, executed the
identity script and detached. The target reported `Process.arch=x64`, pointer
size 8 and Windows. The Frida realm is not an automatic translation of the host
OS's emulation label.

Private capture: `.rescratch/sw26/tupni/identity-x64-native.json`, SHA-256
`524874559f941ed27d4488eeb57b86ff3d9cb25c3efd24347fe234d5514dff7c`.
It contains one identity event, zero dropped messages, zero script errors,
`attached=true` and `detached=true`. Total runner time was 33.875 seconds for a
requested five-second observation window. Startup emitted the auxiliary warning
`Unable to start idund: Timed out waiting for idund to start`; the identity
event still arrived. No input-format inference follows from that success.

The observed model and archive module bases were `0x4b140000` and `0x31a30000`.
The kernel was relocated to `0x7ffb81ba0000`; preferred-image addresses must not
be used as live pointers. The runner recorded interpreter SHA-256
`ca60cf785b2314a6d6599eced15bdf094e6db171bec996b97a70b995942c3c37`
and x64 Frida extension SHA-256
`ff3ed36723b20f23167454d2cc883ad13fc4f978a26161c35d59549714c5ab10`.

`Solidworks2026.js` now selects exact 2026 model/archive functions for primitive
reads, sketch serialization, update status and stamps, feature version
provenance and owner dirty-state transitions. It activates only after the Python
runner verifies both selected loaded-module disk hashes. Buffer offsets and
refill epochs are reported; absolute logical stream offsets remain explicitly
unknown. It supplies no instruction taint or full symbolic dependency engine.

## First capture obligations

### First successful polygon authoring capture

Capture `.rescratch/sw26/tupni/polygon-api-authoring.json`, SHA-256
`1561ff585126fe22975aec7ecdcf8fe07c92059bbf214c6e46c83aaf3ee2928d`,
created and saved training `T3_free`, `T8_free` and `T11_free` on revision
34.5.2. The original control passed before and after in the retained instrumented
process. All three models rebuilt as one solid, had zero native feature/rebuild
issues and saved with success and error/warning outputs zero. The `sketch`
profile with exception interposition disabled collected 8,543 events over
95.219 seconds, zero producer or host drops, zero script errors, no dialogs or
cleanup diagnostics, and a clean detach.

The API reported respectively 3, 8 and 11 points and segments, zero relations,
and sketch-local endpoint identities forming shared closed rings. Positive
native point-slot counts agreed. Saved regular sketches retained saved/current
status 1/1, flags zero and stamps 4, 9 and 12. Origin snapshots retained 1/2 and
stamp 1. These are observed training values; the apparent point-count relation
must still be explained through native mutation dataflow before use as a writer
expression. The [sanitized capture](../v2026/evidence/TupniPolygonAuthoring.json)
retains helper/specification hashes, exact loaded-module identities, API
topology, geometry and save-state events. Initial zero-point snapshots did not
distinguish null arrays. Later line-index and array-identity probes were added
after this capture and are not claimed retroactively. No generated-file or
held-out acceptance follows from native authoring.

### Controlled loader profile and configuration version

The original training control opened and rebuilt correctly with the seven-hook
`loader` profile, exception interposition disabled and guest working directory
`C:\`. Capture `.rescratch/sw26/tupni/loader-original-control-api-only.json`,
SHA-256 `6f35d127bb555c47550b1790e7c189985abeef64a469558ed5c0746d635e798e`,
contains 3,106 events over 65.156 seconds, zero producer or host drops, zero
script errors and a clean detach. The original control digest is
`c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`.
Open errors, warnings, feature errors, feature warnings and dialogs were zero;
the rebuilt solid had volume `8.000000000000001e-6 m³`, area `0.0028 m²` and
center `(0,0,0.005) m`. Global and observed part archive-context versions were 19000. The earlier exception-enabled configuration made this same original
control fail. The experiment does not isolate which exception hook or exception
handler caused the interference; both are now opt-in.

The same seven-hook profile on fresh candidate
`edd138ebf4b9067ce106e947f4c1db988f49366eb697a8aa315af6df806f3b55`
recorded global version 19000 but part archive-context version 2045. Capture
`.rescratch/sw26/tupni/loader-candidate-H3-api-only.json`, SHA-256
`29633910052d689c2f249763447f7419710cc3e3c080a76a13c49fccb9420d08`,
contains 133 events over 59.796 seconds, zero host drops and zero script errors.
The target terminated, so producer completion statistics are unavailable. The
candidate remains rejected at native open with RPC error `-2147023170`.

Static dataflow explains the mismatch: the base-configuration constructor seeds
`f9a8=0x7fd`, while its store routine at `SLDMODU!0x4c217e30`, around
`0x4c21846c`, writes the current archive-helper version (global fallback) when
the configuration has an opened model. Part serialization at `0x4c229a60`
selects modern length-framed sections only for context versions above `0xc7c`.
The shared fresh configuration factory therefore takes the saved version from
the actual owning model's target `f2b0`, 19000. This is a lifecycle-derived
expression, not a value fitted to the control. See
[the model evidence](ModelConstruction2026.md) and
[the constructor/save gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Model/ConfigurationVersionChangesOnSave.md).
The [sanitized comparison](../v2026/evidence/TupniConfigurationVersion.json)
retains exact loaded-module identities and selected events. Remote generation
and corrected native inspection remain pending; no accepted output is claimed.

### Retained-controller control capture

The fresh goal-owned controller opened training `L1_boss.SLDPRT` read-only on
revision 34.5.2, rebuilt successfully and reported one solid, volume
`8.000000000000001e-6 m³`, area `0.0028 m²`, center `(0,0,0.005) m`, zero open
errors/warnings and zero feature/rebuild errors. No dialog or cleanup error was
recorded. This was instrumentation of a vendor-authored training control, not
acceptance of generated output.

Capture `.rescratch/sw26/tupni/ladder-L1-retained.json` has SHA-256
`cda33fba8a5c340f08f31ff96ff0faeea7f69d23ec1fce551baaff03ce06a1d0`,
2,693 events, zero dropped messages, zero script errors and a clean detach.
Total runner time was 74.218 seconds. The
[retained summary](../v2026/evidence/TupniFirstControl.json) records identities,
counts, loader state transitions and explicit interpretation gaps.

Observed event counts were 26 feature constructors, 24 model dirty-state calls,
two sketch serializer entries/leaves, 2,596 primitive calls, 17 count-reader
calls, 14 update-session calls, two solver-wrapper updates, nine status-map
calls and one hooks-ready event. Nested/forwarding primitives are calls, not
2,596 independent fields. Every observed feature constructor independently
corroborated date code 2026306 and kernel behavior 370108, previously recovered
by static dataflow. They are runtime corroboration, not new Tupni discoveries.

The origin sketch loaded current status 2, flags 0 and stamp 1; the constrained
training sketch loaded current status 1, flags 0 and stamp 10. Both retained
saved status 1. These are constructor-to-loaded-file transitions; none is a
general saved-state or stamp formula. The training sketch includes two authored
dimensions and is not a free polygon case.

Two interpretation defects were found and repaired: the solver wrapper's first
argument was misread as a sketch rather than following pointer `+0x8`, and raw
RAX from void `moModel.updateSessionStamp` was labeled a result. The affected
events must not establish sketch state or semantic stamp values. The original
capture also omitted the input hash and retained module runtime bases. Both
are collected in subsequent runner revisions; the missing original identities
are not retroactively claimed as captured. See the
[argument-type gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Tracing/TraceArgumentTypes.md).

### First generated-file inspection

Remote job `132715054038` on head
`8e44d0eb5129e8ddffce92c49e59740c342d3f3a` passed 138 checks with 158 existing
fixture-dependent skips and retained five candidate files in artifact
`14149211309`. A clean native inspection of generated `H3_scalene.SLDPRT`
failed at `OpenDoc6` with RPC error `-2147023170` between two healthy fresh
training-control processes. The candidate is rejected. The
[negative measurement](../measurements/2026/FreshPartFirst.json) records both
controls and the candidate hash. A fault-location capture is the next use of
the native observer; format or cache hypotheses remain unconfirmed.

The first instrumented candidate capture completed with seven events: hooks
ready, five system exceptions and one access violation in USER32 reading address
`0x8`. Frida reported `process-terminated`; no feature constructor or sketch
deserializer was reached. Capture
`.rescratch/sw26/tupni/candidate-H3-first.json` has SHA-256
`31ba472a3c00d8539f85a805bdf5c088df8c4f7aafbc148831d81fe677d6b625`.
It retains input hash and runtime module bases. The requested accurate unwind
produced non-code-looking entries around the C++ throws; these are not a proven
call chain. Native exceptions were forwarded unchanged. The final UI fault does
not identify the earlier file-format rejection. The next capture adds runtime
C++ throw boundaries and MFC file/archive throw exports where named exports are
available, records candidate MSVC exception types, and hashes those modules.

The typed-throw capture identified an MFC `CArchiveException` pointer, whose
native object prefix contains cause 7. Static inspection of the exact swccu
image corroborates the schema-rejection path: `0x31a3a2d0` compares the runtime
class's schema at `+0xc` (with the versionable bit removed) against the file
schema, then rejects a non-versionable mismatch through `0x31a3a536` and passes
cause 7 at `0x31a3a543`. The observed stack region contains its post-call address
`0x31a3a54d`. Capture `.rescratch/sw26/tupni/candidate-H3-throws.json` has digest
`3de7764a67a86a00f36e71369654c05e50416cc3ab1e9bd82e03af03e3691141`.
This narrows the question to the rejected class/schema pair; it does not yet
identify a correct emitted value. A read-only instruction-site probe at
`swccu+0xa3a7` will record that pair. It remains a selected native observation,
not full instruction-level input taint.

### First recovered rule: registered class schemas

The next actual instruction-site capture recorded the file schema and native
`CRuntimeClass` schema immediately before their comparison. Five prior classes
accepted wire schema one. `uoJournal_c` then presented file schema one against
runtime schema zero, followed by the archive exception. Capture
`.rescratch/sw26/tupni/candidate-H3-schema.json` has SHA-256
`78c581343341446555c9c02da5872ca3c6a08c665dcd9dc3eae2c9001f43e4dc`.
It contains 11 events over 65.25 seconds, no host message drops or script errors,
and a process-terminated detach. Producer completion statistics are unavailable
after target death, so complete event coverage is not claimed. The
[sanitized evidence](../v2026/evidence/TupniSchemaRejection.json) retains input,
script and module identities plus the observed class/schema pairs.

Static metadata from the exact `slduiu.dll` independently confirms the rule:
`uoJournal_c::classuoJournal_c` is at preferred address `0x4aef6660`, RVA
`0x2056660` from preferred image base `0x48ea0000`. Its schema member at `+0x0c`
is zero and is not versionable. Image SHA-256 is
`025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7`.
The constructor now explicitly supplies schema zero. This correction comes from
the registered class and loader comparison, without copying a saved-file value.

The trace invalidated the broader assumption that every generated class uses
schema one. A follow-up static audit found `su_CStringArray` also requires zero:
`swccu.dll` getter `0x31a3de90` returns descriptor `0x31a680c8`, whose member
`+0x0c` is zero. The header string-array constructor now supplies zero.
`suObList` requires one. Concrete model, profile, dimension, style and unit
classes audited so far require one; abstract `moCompRef_c` has schema `0xffff`
and a null factory, so the standalone factory refuses construction. Embedded
base fields remain separate from an emitted runtime-class header.

This is the first new reusable format correction obtained through the adopted
Tupni workflow: observe the failing parser boundary, identify a constraint,
explain it through native metadata, then apply the class-specific rule to every
new instance. It is selected native instruction-site observation plus static
dataflow, not the original paper's full instruction taint engine. Corrected
files must still pass clean native inspection and unrelated inputs before
writer acceptance. No speedup comparison has been measured.

Private licensed modules and decompiler inputs were subsequently moved outside
repository checkouts in accordance with the research artifact policy. Their
bytes and per-file digests are preserved in an external relocation manifest;
only format conclusions and input identities remain in maintained research.

### Corrected composition remains unaccepted

Remote run `43693152389`, job `132747827486`, passed the complete native-file
process suite on head `71f60bbfa5374ff7dae0cc87fb75eac62af6f821`. Artifact
`14153605978` contains the corrected schema-zero classes and complete base graph.
The constructor/process tree is identical to root head
`97a247bf3f5e8887570b2856da3bc4e47f4549de`. Fresh `H3_scalene.SLDPRT` is
6,960 bytes with SHA-256
`edd138ebf4b9067ce106e947f4c1db988f49366eb697a8aa315af6df806f3b55`.

Its clean native open still returned RPC failure `-2147023170`. The preceding
control was healthy. The trailing control rebuilt correct geometry but its
watchdog clicked native loading-progress windows, contaminating the batch.
The [negative record](../measurements/2026/FreshPartSchemaFixed.json) retains
this invalid-control outcome; it is not healthy-control acceptance evidence.
The watchdog was repaired to preserve those observed progress windows without
clicking and must be rechecked through actual native controls. A new fault-site
capture on the corrected candidate is needed to identify the remaining loader
failure. No corrected-file native acceptance is claimed.

The first loader attempt activated 20 hooks after both loaded-module hashes
matched. The action's running-object-table lookup failed with COM error
`-2147221021`, `Operation unavailable`. Only the hooks-ready event was captured;
there were zero parser, status, constructor or stamp observations. Capture
`.rescratch/sw26/tupni/ladder-L1-first.json`, SHA-256
`2782d6ad91ae7f37d6744a7864dfbde6488c85e0f2b3223169d44e353ba8af64`,
records a clean detach, zero script errors and 8.297 seconds elapsed.
This setup failure supports no format inference.

The next attempt uses the user's explicit restart authorization and retains the
new COM controller in the same Python process until native tracing detaches.
`Observe.py --prepare-script PrepareSolidworks.py` records preparation identity,
and `ExerciseSolidworks.py` uses that retained controller. The hook also reports
sketch `f128` saved status separately from `f12c` current status. A constructor
value or a live status transition must not be substituted for saved status.

Use the existing 2026 training controls, not the polygon held-out source streams.
Observe archive primitive calls and object dispatch with actual runtime module
bases and input cursor movement. Label that result a native API boundary trace.
If instruction-level provenance is later captured, publish its separate
supported-instruction and byte-source coverage. The API route alone cannot
claim full symbolic taint inference.

Capture one control, vary its point/feature count in the authored ladder, then
match handlers by module/RVA. Preserve loop nesting and reference-map evolution.
Resolve a named blocking field before expanding the hook set. Replay neither
the captured payload nor its field values in the writer.

Each subsequent result must append the capture path/digest, exact target hashes,
question, recovered expression, evidence authority, remote verification and
clean native acceptance result. Failed attachment, truncation, absent events or
an unhealthy control remains recorded. Counts and performance will be reported
only after measurement.

### Takeover: origin solve and post-origin continuation

Clean inspection of remotely generated head `f374f8319`, artifact
`14157729237` from run `43706398170`, still rejected `H3_scalene.SLDPRT`
between two healthy original controls. Its digest is
`3b68ad9e4d77c180b02cb59423aaa25be1d8b560d03b23470347055ffa03f03d`.
All three fresh processes recorded executable build `34.5.2.0604`, SHA-256
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.
The [measurement](../measurements/2026/FreshPartProfileOwnership.json) retains
the controlled rejection, source revision and exact oracle identity.

The unchanged full observation profile then preserved a healthy training control:
12,735 events, zero host/producer drops, zero script errors and a clean detach.
The candidate capture retained 2,826 events, zero host drops and no script errors.
Its process terminated, so producer completion statistics are unavailable.
All 72 observed class/schema comparisons matched, all 381 part archive contexts
were 19000, and 445 object entries/leaves balanced. The part serializer returned.
The [selected evidence](../v2026/evidence/TupniOriginSolved.json) retains both
capture hashes, loaded-module identities and relevant events.

The origin now has exactly one active point before and after its first solve.
The point's solver status changes 1 to 2 and color 5 to 4; sketch status changes
1 to 2, and whole-update returns 2. This closes the earlier observation gap.
The ordinary triangle loads three points and three correctly linked lines, but
its solve is not observed before the crash. That absence does not prove an
ordinary-profile field error or justify copying a saved state into the writer.

The last observed session update returns to `SLDMODU+0x10888bf`, preferred
address `0x4c1c88bf`. Saved 2026 native analysis and instruction inspection show
the immediate next call at `0x4c1c88c4` targets `moModel_c::setModifiedFlag` at
`0x4b79aaf0`. Subsequent body collection calls `moAtomManager_c::getBodies` at
`0x4bcf3170`. The full profile now observes entry/leave of those two methods and
their finalization owner `0x4c1c8320`, without changing native exception handling.
New measurements are pending. No additional serializer value has been inferred.

The [next controlled capture](../v2026/evidence/TupniFinalizationReturned.json)
shows that finalization, all seven modified-flag calls and all 25 body-collection
calls returned in the candidate before termination. The control remained
healthy. The candidate's last observed body-collection return is at caller
`SLDMODU+0x10604a0`. This refutes a failure inside the immediately selected
modified-state or finalization methods, but not an earlier corrupting operation.
Raw RAX zero is not an observed output-array count.
The retained controller now keeps a Windows process query handle and records its
exit code before cleanup, so subsequent captures can distinguish an NT failure
status from an application-controlled exit. Body collection now reads its actual
output array count at `suPtrArray+0x10`, the signed loop bound used in the native
finalization code. New results remain pending.

The exit-status capture reports native process exit code `1`, queried before
controller cleanup. All 25 candidate body-collection output arrays contain
zero items; the healthy control observes both zero and one according to the
collection filter and measures one final solid. No read errors occurred at the
array-count field. Exit code 1 is not an observed NT unhandled-exception code,
and does not identify the initiating native error.

Independent inspection identifies the last body-collection caller inside
`moPart` destruction: vtable slot 1 points to `0x4c1a1050`, which calls
`0x4c1a0280`. The return at `0x4c1a04a0` continues at `0x4c1a04ab` into a
constructor-owned map at model `+0x1430`. These cleanup observations do not
identify the earlier reason for closing or rejecting the model.

The old measurement helpers returned their records only after rebuild, queries
and document cleanup. A later failure discarded earlier `opened` results.
Earlier public-open attribution based only on an aggregate RPC exception is
therefore unresolved. The helpers now preserve every stage and the first
failure, with trace phases and partial records. The next native batch must
establish which public API call actually fails before further writer changes.

The separate model-feature-list hypothesis was refuted by 2026 code.
`loadResolvedFeatures` at `0x4b588c90` reads the resolved roots through
`suObList::Serialize` at `0x4b588f19`, inserts admitted features into model
`f60` at `0x4b588feb` through `moNodeList_c::addNode`, merges at `0x4b588ff5`,
and rebuilds its name map at `0x4b58904c`. Current feature `f2a8=0` does not
select its omission predicate. Native saving intentionally empties the model
child list while separately storing resolved features, then restores it.
An empty Config-0 list is not a proven composer defect; `f78` is visual
properties, not a missing parent link. No speculative linkage field was added.

The staged clean batch now supplies exact public API evidence: the same generated
candidate returns no document from `OpenDoc6`, error `4194304` (`0x400000`),
zero warnings and no RPC or cleanup error. It records only `open_start` and
`open_return`; no explicit rebuild or measurement query runs on the candidate.
Both healthy original controls complete fourteen stages and the expected one-body
geometry. The [new measurement](../measurements/2026/FreshPartStages.json)
does not retroactively establish the exact stage of older aggregate failures.

The [critical repair record](CriticalRepair2026.md) maps the returned bit through
the exact 2026 application DLL. One selected setter is confirmed; a second,
initially selected same-offset write belongs to an unrelated dialog and is
excluded. The repair profile records the confirmed setter and API comparison
without changing preferences or writer fields.

The [matching-mode capture](../v2026/evidence/TupniInitialFrame.json) confirms
clean original controls with the two-hook repair and one-hook frame profiles.
The same candidate bytes still fail during public open. The frame capture
localizes an access violation to a null source in the visual-properties copy
constructor; static instruction inspection corroborates its immediate callers.
Neither missing ordinary-sketch solve observations nor destructor-side body
collection identifies this earlier failure. The owning serialized field and
constructor state remain work for the shared builder.

A new REA pseudocode request for the origin initializer returned no analysis:
the Hopper bridge exceeded its startup timeout, and authenticated document
cleanup was unavailable. That attempt supplies no native format finding.
The existing hash-bound 2026 analysis remains the source for the continuation
addresses. No vendor listings or software are added to this PR.
