# Assigned material appearance projection on SOLIDWORKS 2026

Task `B04-SW2026-NAMED-MATERIAL` belongs to PR #121. Seven exact disclosed
files expose a portable read gap at aggregate
`d3a1134c18027fa8a75676cf3cc7a8b9418395b3`. The ordinary strict adapter
returns one neutral body per file with an empty material collection and
no body material link. Each result records unsupported typed semantics
and remains unqualified for the public writer. The original format-4
package survives as readback metadata. The portable assignment and
authored appearance remain absent.
[Guarded measurement](../measurements/2026/AssignedMaterialAppearanceRead01.json)

## Distinct archive owners

`ReadNamedMat` uses the version-19000 part and CMgr material layouts
explicitly. `ReadMatCfg` joins the actual active directory row in
`Contents/CMgrHdr2` to the one branch selected by both `CMgr.f360` and
`f368`. The part and configuration own distinct mapped `f78` visuals.
Their typed values agree in all seven files. The physical proof separately
binds the sole solid atom in `Config-0.fd88` to the configuration's
`fb00` row, requires empty body and custom override tables, and matches
the nested part density parameter against `fc50` and the assigned XML
density. It returns the assigned categorical identity and density while
retaining `appearance` and `material_tree` as pending.
[Physical record and scope](SdkAssignedMaterialRead2026.md)

The same inputs have a separately serialized `ThirdPtyStore/VisualStates`
holder. The actual configuration ID 0 selects state 1, and the holder's
unit component owns the detached part self. The mapped property attribute
for that state points to its own visual node. The display store reproduces
every byte in each of the seven files. Original and diagnostic holders
match the live visual values. The swapped and depth-edit holders differ
only at the low RealView appearance ID. Definition's independently typed
appearance manager is present with an empty reference list. Its next
appearance ID and catalog material ID have different owners.

| Native field | Authority and open scope |
| --- | --- |
| `moVisualProperties_c.f0c`, `f18` | Model main and hidden-line packed colors. The existing stock renderer names the bytes in COLORREF order and checks each independent owner. Unsigned RGB values in this retained record do not establish effective display precedence. |
| `f20.f90.f14`, `f20.f90.f68` | Classic RealView packed primary color and the separately observed resource filename. A selected-state native stock control binds the classic color. The installed locator is resource identity, with path spelling and publication rules tied to the owning record. |
| `f20.f58`, `f20.f90.f74` | Legacy transparency and classic roughness have their own getter and field evidence. The disclosed assigned files all store zero legacy transparency. The separate native roughness contrast changes the classic field without changing the PBR field. Effective alpha for an assigned display cannot be inferred from these constants. |
| `f88.f10_{0,1,2}`, `f88.f28`, `f88.f2c` | The bounded basic renderer names independent albedo, metallic and roughness values. The archive reads their binary32 fields. The classic roughness setter contrast does not authorize propagation to the DSPBR owner. The full shader's resource and effective display rules remain partial. |
| `f20.has80`, `f20.f80` | Current version wire authority binds presence and 19 fields, including thirteen initial doubles, a CString at the texture's own `f70`, signed values and trailing doubles. Four assigned saves exercise this branch in all three visual owners. Each CString is empty and the complete typed texture values have two distinct digests for the same assigned material. Resource and mapping semantics remain unqualified. The distinct RealView filename accessor supplies no authority for interpreting these texture fields. |
| `MATERIALTREE` swatch | The two same-assignment A files vary their six-hex-digit swatch while keeping the measured physical identity and XML density. The source that chooses this presentation value remains open. The proof records swatch hashes and avoids retaining catalog rows or texture locators. |

[Native model color ownership](VisualConstruction2026.md)
· [Bounded stock renderer inputs](SdkPlanarRendererComposition2026.md)
· [Classic roughness and independent DSPBR](ConcentricStockChildAppearanceCodec2026.md)
· [Texture wire authority](AssignedMaterialArchiveOwners2026.md#texture-layout-and-instance-boundaries)
· [Material swatch contrast](AssignedMaterialTreeCorrelation2026.md)

The D01 author save and D02 swap both bind material ID 258 and density
2700 kg/m³. D01 stores main RGB `(229, 234, 237)`, classic RGB
`(221, 232, 255)`, and DSPBR albedo approximately
`(0.937255, 0.937255, 0.949020)`. D02 stores main and classic RGB
`(166, 158, 150)` and DSPBR albedo approximately
`(0.650980, 0.619608, 0.588235)`. The two complete typed part/configuration
visuals therefore describe different saved appearance despite the same
catalog assignment. The same physical name and density cannot select a
unique portable color or reconstruct the other appearance values. The
prior native source observer captures the deliberately authored visual
contrast **before** material assignment. Its post-assignment and reopen
observations prove physical identity and mass, with effective color left
unmeasured.

The ordinary linked reader refuses at the texture restore class in four
cases and at the configuration hatch class in three. The public adapter
continues through its legacy part projection. Its neutral construction
does not consume `ReadNamedMat`; inferring capabilities after that
construction leaves material capability absent. This shows an omission
in the actual neutral read and a separately retained native diagnostic,
without a successful native write.

## Neutral boundary and next validation

`MaterialRecord` can carry a neutral ID, material name, density in kg/m³,
and one required normalized RGBA. `DesignBody.material_id` can reference
that record after an independently proven part atom-to-body join. There
is no typed neutral field for the SOLIDWORKS catalog and configuration
association, multiple classic and PBR color domains, texture resource
and mapping, display-state attachment, or independent material-tree
properties. The existing adapter-internal `PartLookInput` and
`BasicPbrInput` handle an explicitly modeled nontextured stock scope
and do not supply a portable representation for these named assignments.
[Neutral material type](../../../src/interchange/materials/MaterialRecord.py)
· [Neutral body link](../../../src/interchange/Features/FeatureBody.py)
· [Appearance ownership gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Materials/AssignedMaterialHasMultipleColors.md)

The smallest next oracle comparison can use the two disclosed A saves
with the same material ID and different stored colors. In separate fresh
read-only native opens, pin the exact source hashes, actual selected
configuration, display state and part-self or body owners. Compare the
document and actual sole-body legacy color and transparency getters,
then the independent selected-state render-material getters. Keep the
original saves immutable. The measured render-material enumeration can
add manager records before save, so collect that getter's result on a
fresh read-only copy after the original save is frozen.
[Getter lifetime evidence](AppearanceGetterPersistence2026.md)

If the legacy and renderer observations distinguish the respective
stored fields, a portable appearance type can retain each validated
domain and its actual configuration/display subject. A separate
same-owner, one-variable texture contrast needs a documented native
resource or mapping parameter and its readback before any texture
property gains a portable meaning. The legacy body link alone cannot
express those domains. Complete appearance, material-tree transfer and
the public adapter gate remain open.

## Reproduction

```sh
python3.14 -I -B re/tooling/sw2026/materials/InspectAssignedAppearance.py \
  --source /path/to/disclosed/SdkNamedMaterial01 \
  --output /tmp/AssignedMaterialAppearanceRead01.json
```

The [research tool](../../tooling/sw2026/materials/InspectAssignedAppearance.py)
checks the pinned SDK source tree, shared research readers and the
disclosed input hashes against prior native and typed receipts.
Seven fresh workers bind the actual archive owners and run the public
read with bytes supplied on stdin. Library and codec initialization
precedes the guard. The normal legacy fallback reads the exact hashed
packaged `Config/RootLayout.json` grammar under a read-only exception
counted separately. The named material, display and Definition probes
consume only supplied bytes after initialization. All other external
file and process accesses are denied. This receipt adds zero native
processes, zero generated CAD files and zero held-out credit.
