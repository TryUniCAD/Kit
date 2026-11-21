# SOLIDWORKS 2026 single-edge fillet cold-load discriminator

Task `B04-SW2026-EDGE-FILLET-SOURCES` continues under [PR #121](https://github.com/TryUniCAD/Kit/pull/121). The fillet research lane owns offline interpretation and packaging. The root agent owns native measurement. Inputs are the already disclosed SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` controls and the existing typed archive and retained transaction proof. The exit criterion for this trial is an interpretable paired native result at the one measured locator. A generating rule and independent held-out acceptance have separate gates. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Reverse-engineering playbook](../../Playbook/README.md) · [Writer modeling](../../Playbook/WriterModel.md)

## Model owners and unresolved construction

The neutral intent must identify one bounded convex stock edge and a positive uniform radius. The edge is joint incidence of the two actual stock faces and its endpoints. In the disclosed retained stock, the leading two `Fillet_c.f848` supports each contain both endpoints; the last two each contain one endpoint. Their native surface keys resolve into the stock's actual creation event. The `f848` chosen edge, `f868` radial item's edge and `f820.ff0` share one reference. The D1 chain is `edgeRadiusObject_c.f08` → `moDisplayRadialDim_c.f850` → `moFeatureDimHandle_c.ff0` → `ThreeDRadiusDim_c.f28` → `moLengthParameter_c.f58`. The actual stock `f528`, fillet `f538` and Config-0 `fd88` name one atom. Its creator and modifier identity agree with the previous and active body. The one circular section and uniform radius are proved at the source API. General edge orientation and continuity/transition modes remain outside the measured shape. [Source definition proof](EdgeFilletSourceAuthoring2026.md) · [Typed owners](EdgeFilletArchive2026.md#measured-feature-and-body-owners) · [Production radius chain](../../../src/convert/adapters/solidworks/Core/TypedResolved/Fillets/ReadFilletRad.py) · [Retained body and four incidences](EdgeFilletRollback2026.md#physical-stock-and-selected-edge)

The exact `owners.edge_owners` rows from the [archive receipt](../measurements/2026/EdgeFilletArchiveRead01.json) joined by source SHA-256 to `body_integrity` in the [rollback receipt](../measurements/2026/EdgeFilletRollbackRead01.json) give these measured operands. `f70` and the transmit slot belong to different owners.

| Disclosed state | Atom / BODY_MATCH stamp | Actual prior edge transmit slot | Chosen edge f70 | f70 minus stamp | Result face f70 | Face f70 minus stamp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Axial original | 1816 | 227 | 1912 | 96 | 2146 | 330 |
| Axial edited | 1409 | 226 | 1505 | 96 | 1739 | 330 |
| Transverse original | 1816 | 228 | 1838 | 22 | 2146 | 330 |
| Transverse edited | 1412 | 227 | 1434 | 22 | 1742 | 330 |

All four primary selected references have `fe8=0x200`. The nearby ordinary downstream edge constructor explicitly leaves `f70=0` only for its measured mode-1 result with `fe8=0x300`. That is a different shape and call path. The offsets above are arithmetic observations, with no evidence yet that a fillet loader reconstructs a zero handle or that the offsets generalize. [Exact mode-1 constructor](DownstreamPrismEdgeConstructors2026.md#constructor-and-retention) · [Handle-mode gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Resolved/FilletEdgeHandlesUseDifferentMode.md)

The saved `f9b8` map owns a result face and a separate edge wrapper. The saved `fbf0` row has its own edge reference and matching D1 value. Shared incidence does not merge those slots or make them nullable. The visited `fc20` field has six physical words and lacks a source-derived initialization rule. The empty `f828` keeper is measured only for this profile. The populated `f820` keeper binds the actual selected edge and two concrete representations. A cold constructor must establish any proposed absence, initialization, carrier generation and controller allocation from independent evidence. None of these fields are neutralized by the probe. [Existing fillet layout](../../tooling/sw2026/serial/defs/ResolvedFillet.py) · [Exact transaction receipt](../measurements/2026/EdgeFilletTxnRead01.json)

## One causal trial

The existing L1 boss deletion study showed that one ordinary boss can open after omission of `Contents/Config-0-Partition`. This trial compares two external repacks of the **same** disclosed solved axial fillet. The intact arm retains all 40 logical streams. The omission arm retains the other 39, byte-for-byte and in the same order, with the same file ID, version, signatures and retained type IDs. The packager checks those properties and stores the exact input, omitted payload, output, operator and custody hashes. It uses only the low-level container framing helper and never invokes an SDK document or writer constructor. The repacks and all raw receipts remain disposable oracle artifacts outside the checkout. [Earlier boss deletion study](../v2026/Deletion2026.md) · [Offline staging tool](../../tooling/sw2026/edge_fillet_source/StageFilletCold.py)

Offline staging at `cc9c297d64d10dd44163a11ac9140b8e275cd116` produced job SHA-256 `45bf3dbb19fee75d5aa9d595be12a2f0beac64b987434aad0009e5bc2af231c0`. A separate packet process verified all 17 bound files. The staging receipt also records the four hash-pinned typed `fc20` reads. Native outcome is pending. [Digest-only host receipt](../measurements/2026/EdgeFilletColdDiagnosticStage01.json)

After the healthy leading control, the supervisor uses the one task-owned disclosed axial source's exact guest locator. It atomically renames the SHA-256-verified original to the exclusive adjacent `EdgeFilletAxial.SLDPRT.fillet-cold-probe01.bak`. On Windows that rename fails if a backup already exists. Each unmodified, fully staged arm occupies the locator only during its own fresh native process. The supervisor closes and verifies the oracle is idle, checks the arm's SHA-256, then vacates the locator. A finally block restores and verifies the original before the trailing control. Existing backups, active processes, changed files or paths, and unknown occupants stop the trial. No user native document or sealed source is read or moved. [Native supervisor](../../tooling/sw2026/edge_fillet_source/ProbeFilletCold.py)

The runner verifies the registered type library, executable digest and four distinct native process identities. For each arm it records open errors and warnings, cold body count, cold mass and diagnostics before explicit rebuild, then verifies the original recursive tree, actual chosen stock edge, D1 owner, six-significant geometry and live D1 edit with the established fillet observer. The original arm must complete cleanly. The trial does not save the edited arm or measure a fresh edited reopen. A native failure with an unhealthy control, misplaced or changed file, timeout, dialog or forced cleanup is inconclusive.

A clean result on the omission arm would establish that this disclosed saved history can open, explicitly rebuild and edit D1 with that one stream omitted. A result with clean rebuild/edit only would retain the cold-open deficit. Failure with valid controls would preserve the first observed failing stage for this particular omission. None of these can establish a missing Keeper, zero `f70`, inferred alias, generated configuration, independent generalization, or a public writer.

## Operator commands and recovery

Run the host packager from the isolated checkout at the commit that owns the three tool files. Keep output and source on disclosed research paths outside the checkout.

```sh
python3.14 -B re/tooling/sw2026/edge_fillet_source/StageFilletCold.py \
  --source-root /Users/odin/Documents/UniCAD/Oracle121Takeover/EdgeFilletSource03 \
  --output /Users/odin/Documents/UniCAD/Oracle121Takeover/EdgeFilletColdProbe01/Packet \
  --revision EXACT_TOOL_COMMIT
```

Copy just the frozen external `Packet` directory to `C:\KitEdgeFilletColdProbe01\Packet`. The oracle owner runs from an idle guest. `Run01` must be unused. Use the SHA-256 printed by the packager.

```sh
prlctl exec --current-user 'Windows 11' py -3.12 -B \
  'C:\KitEdgeFilletColdProbe01\Packet\Tool\ProbeFilletCold.py' \
  --job 'C:\KitEdgeFilletColdProbe01\Packet\ColdJob.json' \
  --job-sha256 EXACT_COLD_JOB_SHA256
```

Add `--verify-packet` for a no-oracle packet check. If interrupted, keep dependent oracle work stopped. Confirm no SOLIDWORKS process is running and rerun the pinned command with `--recover`. That operation checks the exact adjacent backup and file hash before it restores. It moves a known trial occupant aside in the original run folder and refuses any unrecognized bytes. If the locator or backup is unrecognized, preserve both and investigate custody without overwriting either. Verify the original SHA-256 `528e0415421149b750a223d3aebdc8e9600f75da8381d9452a22255cd9d993e6`, confirm the backup is absent, and only then start any dependent work. An interrupted run is invalid. Do not reuse its output folder. Only sanitized outcomes and digests may leave the research store.
