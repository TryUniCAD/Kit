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
atom to the native body and joins the header epoch to every stock face
identity. The recorded COM endpoints identify the physical edge. The
reciprocal fin carries the signed order and owning face roles.

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
The two new native derivatives are pending the oracle owner's run.
