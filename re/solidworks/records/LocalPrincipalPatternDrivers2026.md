# Principal linear pattern driver construction

Task `B04-SW2026-LOCAL-LINEAR-PATTERN` · owner `format_proofs` · delivery PR #121. The shared internal constructor extends the direction owner at `3171f5ac8ab0786de30d027665ee5bf184f6b412` with the active count and pitch displays for forward Right and reversed Top. Its surface is `PutPrincMut` with an actual generated Front stock/seed graph, the selected plane from that allocation, a positive count and pitch, explicit reversal, and all six presentation styles. [Direction owner](LocalPrincipalPatternDirection2026.md) · [Shared constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Patterns/Drivers/PutPrincMut.py)

## Native ownership

The six hash-checked disclosed saves are the two originals and each independent count and spacing edit. Their native source lock reports 14 distinct processes, two healthy controls, no writer output and build 34.5.2.0604. The independent input spec and both rectangle authoring tools are pinned by the original packet before any save. The verifier reproduces the actual centre and half-width computation in those tools, including the conversion through millimetres. Adding the nominal plate origin and seed offset alone gives a one-ULP difference for the Right seed's X coordinate. [Disclosed source lock](../measurements/2026/LocalLinearPatternDisclosedSourceLock01.json) · [Disclosure archive intake](LocalLinearPatternDisclosedArchive2026.md)

| Owner | Forward Right | Reversed Top |
| --- | --- | --- |
| Actual direction | Right Plane, +X | Top Plane, −Y |
| D1 `f1258` | `moDisplayDim_c` → its handle, number dimension and integer parameter | Same roles |
| D1 annotation | Actual `*Front` ID 201 | Actual `*Front` ID 202 |
| D3 `f1260` | `moDisplayDistanceDim_c` → its handle, parallel-plane dimension and length parameter | Same roles |
| D3 annotation | Actual `*Top` ID 200 | Actual `*Left` ID 201 |
| Model display IDs | D3 10, D1 11, next 12 | Same allocation |

The `f2b0` membership joins the actual annotations in the part's `fa48` catalogue. Its model-owned IDs are separate from the cameras in `f9f8`. The reserved state for the model's active and shown annotations is independently 199. The count and pitch retain different archive vertices, native dimension IDs and display IDs. Their live parameter and one-element display cache agree. D2 keeps its integer parameter 1 and display cache 0, and D4 through D6 retain zero parameters and caches. All four retain their own display, handle, dimension and parameter with no annotation membership. [Exact native annotation lookup and registration](LocalLinearPatternAngularDatumOwners2026.md#cross-stream-annotation-owner)

## Values computed from the model

- D3's first witness is the actual lower world corner from the joined seed's Front sketch. The second is one signed pitch away. The ordered signed travel and sketch normal give the third axis by cross product. That axis crossed with travel gives the dimension plane's second axis. The shared frame codec projects the negative first witness to obtain the translation. It reproduces all twelve binary64 transform words, including signed zeros, in all six saves.
- The pitch display projects the midpoint displacement onto travel and divides by the witness span. This matches the two pristine saves exactly. The separate source edits retain each pristine projection and count label even when pitch changes. Both edit histories set the same `0x02000000` bit in the `f8a4` style word of all four distance displays, including the dormant ones. Exact replay retains that bit and each owner. New model construction takes an explicit count label and uses the ordinary initial style. [Shared feature-dimension fields](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/DimensionFields.py) · [Linear placement rule](SdkRectangleDimensions2026.md)
- Independently authored styles and catalogue order choose the actual annotation IDs. Numeric view IDs, model display IDs, persistent dimension IDs and the absolute witness coordinates are absent from the constructor inputs as wire values. Existing oblique construction keeps its `*Back` count membership and unassigned pitch membership.

## Reproduction and remaining evidence

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePrincipalPatternDrivers.py \
  --packet-root /absolute/disclosed/LinearPatternSourcePacket03 > /tmp/PrincipalPatternDrivers.json
```

The outer process binds the supplied bytes to the existing source, packet and placement hashes. The workers check complete Config-0 and ResolvedFeatures byte and map replay for the six originals and derivatives. The generated workers consume only in-memory authored model parameters, build the complete linked pattern feature and earlier stock archive graph, and re-read both generated streams with the same codec. Two independent models exercise new count, pitch and catalogue ordering. Each first result is reproduced in a fresh process. Count-only and pitch-only inputs retain the other driver's fields and all dormant owners. Negative workers refuse a mismatched style, wrong frame, absent view, foreign seed, detached plane or unwitnessed sign before allocating driver IDs. [Verifier](../../tooling/sw2026/linear_pattern/ProvePrincipalPatternDrivers.py) · [Guarded receipt](../measurements/2026/LocalPrincipalPatternDrivers01.json)

The existing guarded oblique verification ran both disclosed cases on classic zlib 1.2.12. Whole output SHA-256 remained `f7e5290dfda2cd2aedfc281ea8ee6275fd1214fc011bcda51f88d43d8cc4356f` and `032c9c5696a4b97a9a5c5178147cb8443b90a6350588154dec693ff56d372754`. Each case passed six authored publications, fourteen strict-read publications and 48 refusals with zero runtime reads and no new vendor process. [Existing guarded verifier](../../tooling/sw2026/linear_pattern/neutral/VerifyMeasuredPattern.py)

The existing stock composer still requires its plate origin at world zero. The two disclosed native plates have nonzero signed XY origins. The new proof generates and decodes the scoped archive graphs without publishing a part. Complete principal neutral planning, translated stock preparation, the container and keyword path, native clean open/rebuild/edit, and independent output publication remain open. Existing oblique publication keeps its own exact authority. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
