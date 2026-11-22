# Saved MATERIALTREE variation on SOLIDWORKS 2026

Task `B04-SW2026-NAMED-MATERIAL`, PR #121. The disclosed packet 03 saves and the earlier diagnostic are exact source controls from SOLIDWORKS 2026 SP05.2. This host observation reads those seven files and compares one stream. It uses the earlier typed binary owner receipt for the part density, active configuration density and `IdName` values. No CAD launch, protected original or writer is involved. [Native owner record](AssignedMaterialArchiveOwners2026.md) · [Metadata-only correlation receipt](../measurements/2026/AssignedMaterialTreeCorrelation01.json)

## Exact difference within material A

The D01 Author and D02 Swap files both store material A at 2700 kg/m³ in the two binary density owners. Their active binary `IdName`s agree. Both `swXmlContents/MATERIALTREE` streams are 6042 bytes, with BOM-marked UTF-16LE and 30 parsed elements.

The complete wire difference is the six hexadecimal characters at `/materials/classification[1]/material[1]/swatchcolor[1]/@RGB`. The `swatchcolor` element starts at byte 2908, and the attribute value occupies bytes [2944, 2956), or code units [1471, 1477) after the BOM. The six changed byte offsets are 2944, 2946, 2948, 2950, 2952 and 2954. These are the low bytes of the ASCII hex digits. The decoded 24-bit RGB values differ.

The probe independently obtains XML element and attribute order and offsets from the UTF-16LE byte stream and compares them against the typed XML tree. The element paths, element and attribute order, parser-visible text and tails, and all bytes outside that attribute value agree. The configuration association, material identities, physical-property rows, shaders and the `Optical` child of the same swatch remain exact. The changed field belongs to the classified material's stored presentation. These comparisons establish its location and values' inequality. The native state that selects the swatch remains unclassified.

## Assignment and shape controls

| Saved group | Stream bytes | All elements | Direct physical-property children | Curve points | Configuration rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| Both A variants | 6042 | 30 | 9 | 3 | 1 |
| B across both designs | 6572 | 44 | 12 | 3 | 1 |

All 30 shared XML elements and their data attributes have the same relative wire order in the A and B groups. B adds 14 elements below `physicalproperties`, comprising `RK`, `materialmodel`, `materialcurve` and eleven `data` children. The exact roles of the additional rows and their allowed variation are open.

The single `/materials/configurationslist[1]/configuration[1]` row names the observed active `Default` configuration. Its `@material` exactly equals the binary `IdName`. The `/materials/classification[1]/material[1]` row's `@name` is the catalog/name prefix and `@matid` is its decimal suffix, joined by a literal pipe in `IdName`. The matched IDs are 258 for A and 82 for B in every assigned save. Its `physicalproperties[1]/DENS[1]/@value` agrees with the two typed binary density owners in both groups. These joins establish the distinct configuration association, material row identity and physical density on the disclosed inputs. General catalog ID allocation remains open.

Both depth edits preserve the entire stream from their preceding swap. The B stream is also identical in D01 Swap, D01 Depth and D02 Author. The earlier diagnostic produces the original D01 A stream byte for byte, although its independent source run omits the pre-assignment appearance perturbation. D02's swapped-to-A swatch matches its preceding B swatch. D01's A-to-B swap changes the swatch to the same B value. The two transitions rule out a universal predecessor-retention rule. The two A sources vary assignment history as well as geometry, so the digest observation alone cannot identify the state that selects the swatch.

These are disclosed source measurements. The diagnostic is an independent native authoring run for the same disclosed corner design. It supplies a contrast for the pre-assignment appearance step and gives no held-out credit. The two designs and their depth edits are the already measured packet 03 fixtures. The unassigned control's stream absence comes from the previous owner receipt and is outside this seven-file replay.

## Reproduction and next generated comparison

```sh
python -I -B re/tooling/sw2026/materials/CorrelateMaterialTree.py /path/to/disclosed/SdkNamedMaterial01 --output /path/to/unused/MaterialTreeCorrelation.json
```

The [probe](../../tooling/sw2026/materials/CorrelateMaterialTree.py) binds the seven saves and their prior observations by hash, then audits the in-memory analysis for runtime input access or process launches. The report stores only structural paths, offsets, lengths, identities already observed in the binary owners, counts, digests and comparison outcomes. It stores no XML, catalog rows or swatch values.

For the next independently generated source controls, keep one authored geometry, active configuration, save workflow and physical material target fixed. Compare a direct A assignment with B then A. Repeat those two histories with and without an explicit appearance change. In a separate controlled pair vary only the configuration association. Measure the actual part assignment, selected-body SI density and presentation values before and after save and fresh read-only reopen. Compare the complete typed XML deltas with the same wire-position method. This discriminates history and appearance from geometry and configuration ownership. Optionality and the rule that supplies stored swatch values remain open. Any future writer comparison needs independently constructed streams, frozen inputs and the full native acceptance procedure.

## Typed material tree replay

All seven disclosed streams decoded into an ordered element tree with explicit namespace declarations, attribute values and child arrays. The emitter derives the UTF-16LE BOM and XML declaration, structural CRLF boundaries, rule-based indentation and compact empty tags from that tree. It escapes attribute values and preserves the literal line feeds in the supplied `appdata` field. Four material A saves have 30 elements and 60 attributes with ten literal line feeds. Three material B saves have 44 elements and 78 attributes with none.

Every byte matched on re-emission, followed by decoding to an equal typed tree. A separate XML parse matched the element and attribute inventory and joined the configuration and each material ID and density to its binary owners. The guarded process recorded zero external accesses during read and emission. Full neutral construction still needs explicit catalog or model values for the material attributes, curves, shader and swatch, plus native verification of the complete archive. [Typed model and emitter](../../tooling/sw2026/materials/ModelMaterialTree.py) · [Replay procedure](../../tooling/sw2026/materials/ProveMaterialTreeReplay.py) · [Seven-source receipt](../measurements/2026/AssignedMaterialTreeReplay01.json)
