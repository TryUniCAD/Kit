# Model-generated bare local cylinder

Task `B04-SW2026-IMPORTED-BODY`, owner `/root/release_path`, delivery PR #121. The [host preflight](../../tooling/sw2026/imported_body_source/BuildLocalCylinder.py) generates a bare `SCH_3701250_37102_13006` BODY from an explicit near-cap center, signed axis, radial basis, radius and height. The host exit is two deterministic, fully linked typed transmits with independently checked analytic geometry. Both pass SOLIDWORKS binary exchange. Embedded part loadability remains open. This tranche records zero complete native part outputs and zero held-out cases.

## Geometry and field ownership

The [cylinder carrier grammar](../../../src/convert/adapters/solidworks/Archive/Partition/Fields/AnalyticShapes.py) supplies CIRCLE 31 and CYLINDER 51. The [ordinary cylinder construction](CylinderPartitionConstruction2026.md) supplies modeled periodic rings and the shared allocator. The [stock local imports](ImportedBaseBody2026.md#analytic-topology-contrast) establish the local body role, outward cap arrangement and vertex-free periodic layout. The two new model inputs supply every length, center and frame. The builder assigns wire and persistent indices independently, connects the derived topology and recomputes lengths in the existing stream framing.

The generated BODY starts at wire index 1 with zero owner and zero outside references. Its void and solid regions point to two shell sides of three faces. The far and near faces each own one loop, and the mantle owns the far loop followed by the near loop. Each circle belongs to its edge. Each edge points to the positive side fin, whose negative cap mate points back to the same edge. Each fin has a self-loop in both directions and zero vertex and vertex-ring links. Cap planes use the outward normals and opposite radial frames of their circular carriers. The actual shape has 23 resident nodes, including two CIRCLEs, two PLANEs and one CYLINDER. Both owner lists and all attribute heads are empty.

The [existing research renderer](../../tooling/sw2026/imported_body_source/LocalBodyKernel.py) emits the records. A separate SDK cursor reads the entire declared stream into typed nodes and the SDK field writer re-emits it byte for byte. The existing [storage envelope](../../tooling/sw2026/imported_body_source/LocalBodyEnvelope.py) binds the group key and compressed count exactly. The preflight checks actual link ownership, shape inventory, resident reachability, signed cap extent and unit frame. A typed table projection uses the shared analytic carriers and neutral B-rep reconstruction. Both neutral solids have one closed shell, three faces, four loops and two full-turn edges. The two neutral seam vertices are synthesized from the circular carriers. Zero vertices appear in either transmitted graph.

## Deterministic host evidence

All lengths and coordinates here are in millimetres. The table lists the independent input dimensions and the measurements from the decoded neutral B-rep. A separate formula calculation from the original inputs matches all four measures. The limits are relative 2×10⁻¹² for area and volume, and a Euclidean distance of 2×10⁻¹⁰ mm for the centroid and each bounds corner.

| Case | Near center | Axis / radial | Radius / height | Area (mm²) | Volume (mm³) | Centroid | Bounds |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| TranslatedZ | (16.25, −8.5, 3.375) | +Z / +X | 6.75 / 17.125 | 1012.5745821601602 | 2451.252211656042 | (16.25, −8.5, 11.9375) | (9.5, −15.25, 3.375) to (23, −1.75, 20.5) |
| ReverseY | (−11.125, 28.5, −4.875) | −Y / −Z | 4.625 / 24.25 | 839.0997628197488 | 1629.6152861255837 | (−11.125, 16.375, −4.875) | (−15.75, 4.25, −9.5) to (−6.5, 28.5, −0.25) |

| Case | Raw bytes | Raw SHA-256 | LocalBodies bytes | LocalBodies SHA-256 |
| --- | ---: | --- | ---: | --- |
| TranslatedZ | 1414 | `20f764878d7ef568f01a9df61b276522f71a16aa7b13e2a2e121fd6ebf410b44` | 808 | `6b9ab8af329f1f1cca7208bbe0a60e2726d5ea72ce2b3f7b9caf23355521f818` |
| ReverseY | 1414 | `85c47d7beb3b2c4a9e01d98341197e62f345601fcc4e813afb976cccc2b79852` | 806 | `e6338d1d71f804f39b45783b131f80207d444e097e50cdb5f07753daa1944fd5` |

Two fresh processes produced identical 6,814-byte receipts with SHA-256 `92fcf0ba4589e92aa3967e9341aff655e7df442748f002d5e1c7dc6727ea7ff3`. The preflight program has SHA-256 `96152534166c77fa59cc927cba925db5a1432900e512ce62bb6f91d331ec96bf`. The receipt includes the owning schema, allocation, encoder and decoder source digests. Construction and verification made zero runtime reads. Eight preflight refusals cover zero radius, infinite height, nonorthogonal basis, unrepresentable extent, a trailing byte, a finite-vertex pointer in a periodic fin, the wrong rim basis and an inconsistent radius.

```sh
PYTHONPATH=src:.:re/tooling/sw2026:re/tooling/sw2026/serial \
  uv run --offline --no-project --python 3.13 python -B \
  re/tooling/sw2026/imported_body_source/BuildLocalCylinder.py
```

The command prints the receipt. Pass `--artifacts "$UNUSED_EXTERNAL_DIRECTORY"` to additionally create `TranslatedZ.x_b` and `ReverseY.x_b` in a new directory outside the checkout. Both outputs are created exclusively after the guarded preflight passes.

## Native exchange protocol for the oracle owner

1. Freeze the two binary hashes above, the explicit neutral dimensions, the case digest, and a fresh guest-local output directory. Use SOLIDWORKS 2026 SP05.2 x64 build 34.5.2.0604 under the root-owned Parallels COM oracle. Use the two [stock cylinder imports](../measurements/2026/ImportedBodyTopologyNative01.json) as exact disclosed controls and verify their local raw payload digests separately.
2. Reuse the guest process lifecycle, preference restoration and `LoadFile4` method in [the measured exchange observer](../../tooling/sw2026/imported_body_source/ObserveKernelExchange.py). The existing job schema and body comparator require planar line-edged solids with at least three vertices. Bind a separate cylinder observation branch and reuse the independently measured [native cylinder radius and axis observer](../../tooling/sw2026/imported_body_source/AuthorImportedBody.py) and [six-direction bounds observation](../../tooling/sw2026/InspectSdkCircleBodyTypes.py). Preserve the existing prism control path.
3. Run fresh application and binary export controls before and after the batch. Run the stock +Z payload, generated +Z payload, generated −Y payload and stock −Y payload in distinct application processes between those controls. For each cylinder require one solid, zero sheet bodies, zero native vertices, exactly two circular edges, two single-loop planar caps and one two-loop analytic mantle. Record the cap centers and outward directions, radius, axis line, volume, area, centroid and signed extrema before and after rebuilding. Set tolerances prospectively and bind them to the native job. Capture the exact payload digest, load error, rebuild diagnostics, process identity and preference restoration.
4. The measured exchange outcome would establish the raw body intake for this disclosed batch. The standalone local storage attachment, completed archive owner, repeated native save and fresh reopen, and independently locked variants remain separate steps. The generated geometry carries no stock body tags, saved face identities, active WORLD, or rollback history.

The [packet preparer](../../tooling/sw2026/imported_body_source/PrepareCylinderExchange.py)
stages the generated transmits, separate stock part and raw controls,
their exact provenance receipts, and ten Python tools. Its
`--stock-packet` points at the host's disclosed native topology packet.
The [guest observer](../../tooling/sw2026/imported_body_source/ObserveCylinderExchange.py)
accepts the frozen `Job.json` path and its `--job-sha256`. The flag
`--verify-only` performs the standalone custody check and starts no
application. Native execution requires an unused guest-local directory.

## Native exchange result

The [frozen trial](../measurements/2026/GeneratedLocalCylinderExchangeNative01.json)
passes all ten phases with eight healthy controls. The two 1,414-byte
transmits each pass 76 checks on their independent translated and signed
cylinders. Both load with error zero, restore the original import
preference and keep the complete measured geometry through rebuild.
Each body has three faces, two full-turn circular edges and zero native
vertices. Both caps and the periodic mantle retain their distinct loop
ownership. Signed extrema, area, volume and centroid agree with the
analytic model at the recorded tolerances. The result qualifies the
disclosed binary exchange step and leaves completed parts unmeasured.
