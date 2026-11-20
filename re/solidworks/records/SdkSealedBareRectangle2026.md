# Paired bare rectangular import regression

**Status: method prepared. Native execution pending.**

B04-SW2026 imported-body research in [PR #121](https://github.com/TryUniCAD/Kit/pull/121) pairs the normal SDK writer with two previously evaluated, pre-writer locked SOLIDWORKS box originals. The takeover agent owns the Windows oracle. The exit condition for this protocol is a clean pair of bare geometry lifecycles and strict SDK readbacks with unchanged inputs and healthy controls.

## Bindings and prior use

The guest author specification was locked at 2026-11-19 22:43:51 UTC, and the two native originals were locked at 22:49:46 UTC under author revision `b74c248bc20e11cf72d1905b2ef696c267a90a26`. The exact tracked custody receipt is SHA-256 `d2568776891dec3f5671dc89d9696ae3d4d4005fb22f4dedf500347939f6de2a`. Its original opaque lock digest is `1a5a4993881c967682496c90924c262c7954fddd67dd9d1ee3e105186deed281`. The specification digest is `1f145836a8db6fe13893546c83957b8e82b5b80771546f3ae39724a9a716d2bf`. The evaluator rechecks the original and specification bytes inside Windows. [Authoring and source custody](../measurements/2026/ImportedBaseBodySourcesNative01.json)

| Original alias | Source SHA-256 |
| --- | --- |
| Slot01 | `27de26139590fe292ae420212af7515660fdb48d8f4f1830fae739cb3799b93a` |
| Slot02 | `db9a9dc8cdaec057421ad7934ab8a55680d6e50b1e966e61887c56a43bbe755d` |

The earlier attributed research writer at `a2a8125d136a43f750dafee4f0f4d93d04255301` used these same originals, preserved the original feature labels and passed 232 candidate checks. Later scene, text, file property and annotation trials reused the pair. The separate bare SDK native trial used one disclosed translated box. This protocol records zero new independent cases, zero original FCStd conversions and zero whole-source conversions. [Prior attributed lifecycle](../measurements/2026/SealedImportedLocalGeometryNative01.json) · [Prior strict readback](../measurements/2026/SealedImportedLocalGeometryReadback01.json) · [Disclosed bare native lifecycle](../measurements/2026/SdkPublicRectangularNative01.json)

## Method

The host freezes the observers and the committed SDK file inventory with the opaque source receipt and the pristine rectangle control. The method commit must postdate the source lock and carry the same `src` tree as `05e3fceb6ad43593435d39cffe309b1cb044fc57`. The guest verifies the full inventory and packet digests before accessing the originals. The independent authoring specification provides native comparison values, and the strict SDK reader supplies the separate typed input geometry.

The projector binds the sole `moBaseBody_c` feature, its actual design body and the selected root configuration. It checks one outward closed box, all eight signed Cartesian corners, twelve line edges and six plane faces with complete trim incidence. It projects the boundary and active configuration name into a fresh neutral document. The current exact plane-station check runs on that neutral model. [Source projection](ImportedBodySourceGeometry2026.md) · [Exact station check](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/LocalBodies/BoxFacesNeedExactPlaneStations.md)

The model-only construction guard wraps actual native preparation, refusing runtime data reads, native process starts, sockets and dynamic library access there. The ordinary call is `write_document(document, target)`. The build must pass real staging, the real final locator in both headers, a generated local-body stream and exactly the native B-rep and configuration transfers. It captures the real creation event and hashes both candidate files before the separate measurement command.

The measurement checks the candidate and its native save with the default strict SDK reader. Both must bind the fresh `Imported geometry` feature and body to the expected configuration and preserve the signed box. The unsaved comparison uses the exact millimetre-to-wire-to-SDK position conversion. The saved comparison uses the previous readback's absolute \(10^{-9}\) mm bound alongside the full typed box incidence check.

Each native original, candidate and fresh reopen runs in a distinct SOLIDWORKS 2026 SP05.2 `34.5.2.0604` process from executable SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`. Both pristine controls must pass, giving eight distinct processes. The observers check zero open/rebuild/save errors or warnings, independently specified signed corners and face-edge incidence, one actual owned solid, volume, area and each centre-of-mass coordinate. Original and generated mass properties must also agree to six significant figures outside the established near-zero tolerances. The candidate retains its own feature tree and persistent BaseBody identity through rebuild and fresh reopen.

The fresh neutral model transfers geometry and the active configuration name. Source labels, native owner identities, carrier parameterization, other configuration state, presentation, properties, provenance and archive payloads stay outside the comparison. The public result contains slot aliases, hashes, narrowed checks, counts and omission categories. Native records, logs, original geometry and specifications, generated files and native saves stay under the guest-local root.

## Run in the owned oracle

Use the existing pristine rectangle control with SHA-256
`c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57`.
Set `method_revision` to the commit that tracks these tools and `control`
to the disclosed control path. The host packet and the guest root must both be unused.

```sh
packet='/Users/odin/Documents/UniCAD/Oracle121Takeover/SdkSealedBareRectangle01'
python3.14 -B re/tooling/sw2026/imported_body_source/RunSealedPublicBox.py freeze \
  "$packet" "$method_revision" "$control" 'C:\KitSdkSealedBox01'

guest_packet='\\Mac\Home\Documents\UniCAD\Oracle121Takeover\SdkSealedBareRectangle01'
tool="$guest_packet"'\Kit\re\tooling\sw2026\imported_body_source\RunSealedPublicBox.py'
job="$guest_packet"'\Job.json'
prlctl exec 'Windows 11' --current-user "$guest_python" -B "$tool" verify "$job" "$job_sha256"
prlctl exec 'Windows 11' --current-user "$guest_python" -B "$tool" build "$job" "$job_sha256"
prlctl exec 'Windows 11' --current-user "$guest_python" -B "$tool" measure "$job" "$job_sha256" "$build_sha256"
```

Use the verified guest Python executable. Copy `job_sha256` from successful host freeze output and `build_sha256` from successful guest build output. Only `Result.json` in the host packet is the publishable native result. Keep the private guest root on failures and use fresh numbered paths for a new run.

[Freeze and guest entry point](../../tooling/sw2026/imported_body_source/RunSealedPublicBox.py) · [Guarded writer and paired checks](../../tooling/sw2026/imported_body_source/CheckSealedPublicBox.py)

The first build stopped before any native launch. Its guard compared the
fresh document's empty declared capability cache with the two inferred
capabilities. A fresh packet uses the registry's shared inference for
this assertion. The writer and the original locks are identical.
