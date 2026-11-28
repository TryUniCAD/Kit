# Native stock-only edge orientation acquisition

Task `B04-SW2026-EDGE-FILLET-SOURCES` in [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
The [construction boundary](EdgeFilletConstructionBoundary2026.md) establishes
the two distinct stock incidence observations and the remaining fillet
owner and option initialization gaps. This protocol isolates ordinary
rectangle stock construction from that unqualified fillet state.
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
and [oracle method](../../Playbook/WriterModel.md#6-oracle-acceptance).

## Freeze and check the packet

From the isolated checkout at the exact tool revision, verify that the
SDK and research scope is clean. Supply the previously measured
disclosed control, SHA-256
`28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0`.

```sh
python3.14 -B re/tooling/sw2026/edge_fillet_source/StageFilletStock.py \
  --revision "$(git rev-parse HEAD)" \
  --control /absolute/path/to/EdgeFilletSource03/Packet/Control.SLDPRT \
  --output /absolute/unused/EdgeFilletStock01/Packet \
  --guest-root 'C:\KitEdgeFilletStock01'
```

The stage command prints the complete job SHA-256 and both candidate
hashes. Each fresh worker receives only the four-line stock geometry,
name and modeled output location. It completes the shared blind boss
construction under an audit guard that rejects file, CAD, subprocess and
network access. The immutable control is read by the supervisor outside
the construction workers. The generated files are complete ordinary
blind part containers with ten logical streams each.

Copy the exact frozen `Packet` directory to `C:\KitEdgeFilletStock01\Packet`.
The native runner creates disjoint fresh `Candidates`, `NativeSaved` and
`Run01` directories beside it. Use `--verify-packet` first to verify the
exact guest transport without launching SOLIDWORKS.

```sh
prlctl exec --current-user 'Windows 11' \
  'C:\Users\odin\AppData\Local\Programs\Python\Python312\python.exe' -E -B \
  'C:\KitEdgeFilletStock01\Packet\Tool\RunFilletStock.py' \
  --job 'C:\KitEdgeFilletStock01\Packet\StockJob.json' \
  --job-sha256 EXACT_STOCK_JOB_SHA256
```

The oracle owner runs those commands on an idle guest. Each phase has a
fresh worker with one owned versioned COM process. The bracket verifies
the exact executable build and hash, first and last control, clean cold
and rebuilt stock, modeled D1, one solid, expected signed model points
and six-significant-figure body integrals. The stock tree must remain
the same after explicit rebuild. The selected edge must belong to two
plane faces with the actual boss as producer. Each native save uses a
new path under `NativeSaved`. The original candidate hash is rechecked
after close and again after the trailing control. The raw phase reports
stay in `Run01`. `Run01/Result.json` contains disclosed geometry,
process identities, hashes, counts and verdicts.

A child timeout or leak blocks further launches while SOLIDWORKS is
active. The runner never reuses an occupied lease. Keep any failed
result and use a different numbered root and newly generated packet for
another attempt. The previously measured fillet sources are untouched.

## Typed physical fin inspection

After a passing bracket, export only the two disclosed `NativeSaved`
files and the sanitized `Result.json` as separate immutable artifacts.
The reader checks the exact native result and source digests before
examining the actual active partition. It links the unique boss output
atom to the actual Config-0 manager entry. The complete closed active
body must carry the same `ATOM_ID_2001` and
`LAST_BODY_MODIFYING_FEATURE_ID`. Its implicit name must agree with the
boss, and its eight vertices must agree with the native measurement.
The header creation event must agree with all six `FACE_ID_2001`
identities. The measured endpoint set chooses one physical edge. The
reciprocal positive fin supplies its signed order and owning face roles.

```sh
python3.14 -I -B re/tooling/sw2026/edge_fillet_source/InspectFilletStock.py \
  --job /absolute/path/to/Packet/StockJob.json --job-sha256 EXACT_STOCK_JOB_SHA256 \
  --result /absolute/path/to/Run01/Result.json --result-sha256 EXACT_RESULT_SHA256 \
  --native-saved /absolute/path/to/NativeSaved \
  --report /absolute/unused/FilletStockFin.json
```

Failure here preserves the independent native observations. A missing or
unqualified typed partition yields an explicit offline refusal. A
passing typed stock result measures stock direction only, with zero
generated fillets and zero held-out evaluations.

Host preflight used the tracked ordinary `L1_boss.SLDPRT`, SHA-256
`55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6`,
with the independent 40 × 20 × 10 mm box vertices and the axial edge at
X −20 mm, Y −10 mm. The guarded inspector bound creator 34 and atom
101 to the active partition. Positive fin 46 traversed Z 10 to 0 mm
with roles side 1, side 4, end 1 and end 0. Moving one endpoint off the
box rejected the selection. Both workers reported zero external accesses.

## Native and linked outcomes

The [native bracket](../measurements/2026/EdgeFilletStockNative01.json)
passed on SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. Both controls and
both candidates ran in four distinct processes, with an idle oracle
afterward. Each candidate passed 24 numeric checks, retained clean
6-face, 12-edge, 8-vertex stock before and after explicit rebuild, and
saved to a distinct native derivative. Both original candidates retained
their frozen SHA-256 values. The raw sanitized result SHA-256 is
`129cf2155048db1188144dd2dd81d2fe860f5ed42bf810561c7770b39a111298`.

The [initial offline refusal](../measurements/2026/EdgeFilletStockFinRefusal01.json)
preserves both `BODY_MATCH` lookup failures. Each derivative has an
actual native atom and last modifier on its one closed partition body.
Each `moExtrusion_c.f528` aliases the real Config-0 atom. The body
attribute values agree with this object's `f140` and the extrusion's
`f08` and with the atom's `f12c` and `f130` creator references. The
archive cache words remain separately observed. Both atoms retain
`f180 = f1b0 = 1008` and neither active body has a `BODY_MATCH`
attribute. The recovered body retains the actual `Boss-Extrude1`
implicit name. The [saved-stock ownership gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/Owners/NativeStockSavesCanOmitBodyMatch.md)
records the boundary.

The [linked typed repeat](../measurements/2026/EdgeFilletStockFinRead01.json)
recovered the following from the exact native-saved bodies in two fresh
workers with zero external accesses. The marked `L1_boss.SLDPRT`
control still checks its actual `BODY_MATCH = 1656`. Separate guarded controls
rejected altered observed endpoints, another box's vertices, a
different typed physical atom or modifier value on the unmarked stock,
and a conflicting typed stamp on the marked stock. The scalar contrasts
changed only the in-memory typed projection of the pinned inputs.

| Stock | Physical edge node ID | Positive fin slot | Actual signed order | Typed stock roles |
| --- | ---: | ---: | --- | --- |
| Axial | 81 | 68 | Z 22.8 mm to 0 mm | Side 2, side 1, end 1, end 0 |
| Transverse | 17 | 48 | X 13.15 mm to −29.75 mm | End 1, side 3, side 2, side 4 |

Both physical edge node IDs, endpoint directions and role orders match
the two prior native-author fillet predecessors and their edited
derivatives. Against the purely modeled prism, the axial result is
reciprocal and the transverse result agrees. This isolates the signed
native stock wire and leaves the general direction-selection rule, live
fillet handle initialization, result keepers and `fc20` unresolved.
The bracket generated zero fillets and read zero held-out sources.
