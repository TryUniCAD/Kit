# Construct an ordinary rectangular revolve for research

The scoped SDK construction prototype generates one ordinary rectangular Front revolve from a neutral document. It keeps the selected construction axis separate from the closed contour and preserves the real positive radian driver and four contour relations.

The entry point is `make_candidate(document, settings)` in [ComposeRevolvePart01.py](../../../../re/tooling/sw2026/revolve/Construction/ComposeRevolvePart01.py). Supply a validated neutral `CadDocument` and explicit `PartBuildInput`. The result retains the actual generated system, profile, feature, axis, display/parameter, header, configuration and resolved graph objects, along with the ten generated streams and complete container bytes. It reads no native file and emits no geometry cache.

The narrow source input has one active configuration, one canonical Front support, one five-line sketch, one selected upward construction axis, one four-edge rectangular contour strictly to its right, four horizontal/vertical relations, one angular boss and one unexpressed `D1` parameter in radians. The sweep is one-sided and positive through at most a full turn. Reverse changes the normalized effective axis direction. Other owner families reject.

Use the frozen source snapshot and tool manifests for an independent process replay. From an independently checked-out copy with the pinned Python environment:

```sh
.venv/bin/python -B re/tooling/sw2026/revolve/Construction/RunBuildProof02.py --root /path/to/private/revolve-freeze --output /unused/revolve-proof
```

The private freeze must contain `Code01`, `Baseline01`, `Tools02`, `CodeSource01.json`, `Baseline01Source.json`, `ToolsSourceFinal02.json` and `Specs01.json`. The runner verifies complete membership and hashes before starting. It builds four designs in paired fresh processes, rejects 18 unsupported neutral inputs and compares two existing polygon outputs with the unchanged published base. It publishes `BuildProof.json`, generated files, individual stream receipts and independent source predictions. It performs no CAD automation and reads no original held-out input.

For semantic inspection, use the normal SDK reader with `source_format='solidworks.sldprt'`, `strict=True`, `include_brep=False` and `include_tessellation=False`. Default strict geometry reads still require a readable Parasolid payload for this family. The independent closed analytic B-rep used in validation is not a transmitted payload.

The separately frozen native packet passes ten processes with healthy controls. Its saved files retain the full tree, selected construction axis and edited angle across fresh reopens. The host lifecycle adjudicator verifies the exact packet, native phases and later idle inventory. The original-source comparison remains open. [Native receipt](../../../../re/solidworks/measurements/2026/SdkOrdinaryRevolveNative01.json)

[Field ledger and exact boundaries](../../../../re/solidworks/records/SdkRevolveConstruction2026.md) · [Source-only process receipt](../../../../re/solidworks/measurements/2026/SdkRevolveConstructionProcess01.json) · [Explicit geometry policy](../../../Gotchas/Conversion/Solidworks/Model/Revolve/CachelessRevolveNeedsExplicitReadPolicy.md)
