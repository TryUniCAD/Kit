# Typed inspection of a saved assigned part material on SOLIDWORKS 2026

Task `B04-SW2026-NAMED-MATERIAL` belongs to PR #121. This archive-only prerequisite can be reproduced with the seven named disclosed saves and one pristine control from `SdkNamedMaterial01`. The [native archive owner record](AssignedMaterialArchiveOwners2026.md), [material definition field evidence](AssignedMaterialOwners2026.md) and [XML correlation](AssignedMaterialTreeCorrelation2026.md) bind SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. Data comes from the previously measured native sources. This run starts no new native process.

## Typed ownership

| Lane | Required agreement |
| --- | --- |
| `Contents/CMgrHdr2` | Its sole active configuration row names the actual selected ID 0 and has the same update stamp, flags and part geometry stamp as the ordinary binary owners. |
| `Contents/CMgr` | The actual sole directory object `f370.items[0].o` is both `f360` and `f368`. The selected configuration, its own name and its `moVisualProperties_c` and hatch records belong to this stream's map. `fc50` is positive and matches the physical part parameter. |
| `Contents/Config-0-ModelHeader` and `Contents/Config-0` | The ordinary decoder preserves real header aliases. The part's `f1420` material owns a nested schema-one `moDensityParameter_c` at `f08`. The part hatch ends where the material begins. The density and material end together where model data begins. Explicit density links and the alternate `f60`/nonzero `f68` form are outside scope. |
| Active `f78.f20.f20` and part `f78.f20.f20` | Each ordinary owner stores the same printable `catalog\|material\|nonnegative decimal ID`. Their qualified texture-presence selectors agree, and the independently persisted `fc48` and `f1418` hatch records agree. |
| Part body and override owners | The sole mapped solid atom appears in the actual manager `fd88` and supplies the key for the single observed `fb00` row with value 0. The `n420`, `n430` and manager `n600` maps and part body visualization tables are empty. The value-0 row constrains this profile. General atom assignment and inheritance require separate evidence. |
| `swXmlContents/MATERIALTREE` | BOM-marked UTF-16LE is decoded before the shared untrusted XML parser. The material row's catalog/name and numeric ID, the sole configuration association and the sole `physicalproperties/DENS` value corroborate the binary observation. |

The read-local texture/hatch grammar uses the exact previous SP05.2 restore range and the shared schema-one hatch format. The opt-in mutates only the fresh archive context's dispatch maps. Ordinary part and manager reads retain their previous boundaries, and no writer exercises this profile. The result carries the physical assignment fields and two pending domains, appearance and full material XML semantics. Stored curve, shader, hatch style, swatch, catalog properties and an arbitrary ID allocator receive no transfer qualification.

## Process evidence

Run the [proof command](../../tooling/sw2026/materials/ProveAssignedMaterialRead.py) with Python 3.14 and a new receipt path.

```sh
python3.14 -I -B re/tooling/sw2026/materials/ProveAssignedMaterialRead.py \
  --source /path/to/SdkNamedMaterial01 \
  --output /tmp/AssignedMaterialRead.json
```

The parent verifies the exact prior native lifecycle receipts and source hashes before stdin transport into eight fresh isolated workers. An audit hook denies file and directory access, dynamic native-library loading, process launch and socket connection during parsing and checks. The seven assigned saves agree with the independently observed native part material names and modern selected-body SI densities. The unassigned control retains its old structural read and fails the named assignment gate even though its visual label says `Steel`. The proof has 23 targeted refusals including detached graph owners, an alternate density flag, conflicting XML, wrong container version and an unresolved texture selector.

The [receipt](../measurements/2026/SdkAssignedMaterialRead01.json) records source hashes, actual map slots and spans, observed IDs and densities, and the existing strict read boundaries. No proprietary binary or XML payload belongs in the implementation or receipt. Held-out transfer, material generation, public admission and complete native conversion remain pending.
