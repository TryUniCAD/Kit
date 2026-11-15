# Tupni usage in SOLIDWORKS 2026 recovery

Status: adopted during the active 2026 native-writer investigation on
2026-11-15 UTC. A native process-identity observation succeeded and detached.
The first loader/status capture also succeeded. No completed instruction taint trace, newly
generalized grammar or measured speedup is claimed yet.

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

Open questions include post-build sketch state, transient persistent-id
allocation, final header counters, cache neutralization, unmodeled classes,
assemblies and the remaining feature families. A successful component codec
round trip does not resolve these questions.

## Adoption record

| Step | Actual observation | Evidence class and limit |
| --- | --- | --- |
| Read primary method | Read field, loop, handler, constraint, aggregation and limitation sections of the CCS 2008 paper | Literature source; no target execution |
| Select trace boundary | 2026 archive cursor is at `su_CArchive+0x38`, end at `+0x40`, map counter at `+0x50`; target decompressed archive reads rather than treating compressed payloads as flat fields | Existing static binary evidence in [reverification](../v2026/Reverification.md) |
| Check host route | REA exposed local/socket/barebone Frida device routes; this does not expose the Windows VM automatically | Tool availability only |
| Check VM runtime | `platform.machine()` reported ARM64, pointer size 64-bit; `frida` was absent from its module search | Passive host report; executable architecture was not established by this string |
| Select dependency | Official Frida release and PyPI metadata identify 17.26.3 Windows ARM64 builds | Version-pinned acquisition metadata; attachment not yet proven |

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
