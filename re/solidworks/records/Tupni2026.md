# Tupni usage in SOLIDWORKS 2026 recovery

Status: adopted during the active 2026 native-writer investigation on
2026-11-15 UTC. Native tracing setup is in progress. No completed instruction
taint trace, newly generalized grammar or measured speedup is claimed yet.

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
| Check VM runtime | The installed Python reported ARM64, 64-bit; `frida` was absent from its module search | Passive VM environment observation, not a CAD trace |
| Select dependency | Official Frida release and PyPI metadata identify 17.26.3 Windows ARM64 builds | Version-pinned acquisition metadata; attachment not yet proven |

The verified PyPI wheel candidate is
`frida-17.26.3-cp37-abi3-win_arm64.whl`, SHA-256
`9277d3562abc1131e67f128e042528972c30a58bb3b746918a81420789a5d228`.
Private research acquisition does not add a CAD or tracing dependency to Kit's
production writer.

## First capture obligations

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
