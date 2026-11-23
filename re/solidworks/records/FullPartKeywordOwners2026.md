# Saved part Keywords reconstruction from binary owners

Task `B03-SW2026-KEYWORDS-MODEL/part-index`, owner `/root`, delivery
[PR #121](https://github.com/TryUniCAD/Kit/pull/121). The comparison
combines the 92 tracked version-19000 parts and 111 manifest-pinned
recovered cuboids. Its construction input contains Config-0, its
linked model header and ResolvedFeatures, CMgr, and the version marker.
The original keyword stream and every other stream are absent from the
input of the projection.
[Reproduction and artifact](../measurements/2026/FullPartKeywordOwners01.json)
· [Editor-owner and dimension evidence](KeywordOwnerProjection2026.md)

| Row or field | Classification | Scoped construction rule |
| --- | --- | --- |
| Document title and event | Authored title and event | The part node supplies the title. The linked header self-file supplies its event at `f38.shared.f28`. |
| Configuration identity | Derived active selection | The single CMgr list entry, active `f360`, and `f368` alias the same actual configuration. Its node supplies its ID and name. |
| Configuration material caption | Derived display | The active configuration's `f78` visual node contains the optional `f20` material properties. The material's IdName is their `f20` CString. An empty IdName leaves the native attribute absent. An assigned compound identity names the material between its database delimiter and optional integer identifier. The measured unassigned `Steel` identity uses the actual material folder's unassigned caption. |
| System rows and nested presentation rows | Derived containment and vocabulary | Start from actual resolved feature owners. The resolved environment aliases Config-0 `f1e0`. Its typed children and the cabinet's typed notes enter through their `f60` lists. The nameless exploded helper enters from `f13f8`. |
| Empty sheet-metal marker | Reserved helper identity | The 31 measured direct `f1018` objects have ID `-1`, no title, and an empty auxiliary list. |
| Sketch and extrusion dissection | Derived owner relationships | The measured ordinary sketches are type-less and dissectable. Each of the eight ordinary cut rows reaches the real resolved profile in its typed feature parents and emits a single child link, its dissectable flag, and its root flag. |
| Operation role | Format vocabulary | The disclosed ordinary bosses, cuts, revolves, sweeps, and imports use the respective typed archive classes and role text. The two earlier constructed local imports use their classified class-labelled role projection, an explicit empty material attribute, no ambient child keyword, and spaced framing. |
| Sibling dimension order | Volatile in vendor saves; computed during construction | All 309 visible dimensions have an actual parameter node ID of `-1`. The measured native exporter gives these rows address-based discriminators. The generator follows the typed display and active driver sequence, while an exact source replay keeps its typed sequence. |

The configuration keyword serializer entry at `0x4c2389a0` is shared by
the base and part configuration tables in the pinned 2026 model DLL. At
`0x4c238a07` slot `+0x1040` returns `+0x78` via `0x4b289be0`.
The writer obtains material properties and their IdName, checks for an
empty IdName, parses the material identity, and calls the XML extractor
at `0x4c238aca` when the extracted caption is nonempty. The pinned
[assigned material record](AssignedMaterialOwners2026.md#database-and-material-identity)
binds the same native property getters. In this cohort, 169 native saves
use the legacy unassigned identity, 31 have an empty IdName, and one
contains the disclosed assigned material. The two generated local-import
controls have no visual material owner.

The common feature serializer uses slot `+0x410` for the dissectable
gate, `+0x400` for its actual child list, and `+0x1af8` for the root
decision. The child callback `0x4bdaa0a0` filters through the child's
dissectable predicate and serializes its node ID. The archive cohort
independently verifies all eight IDs against their actual scoped cut
profile. Other feature classes and unsupported dissection conditions
retain their own qualification boundaries.

All 5,330 feature rows and 309 parameter displays come from the four
binary owners. The projection matches 196 complete keyword streams byte
for byte. The other seven match after comparing dimension sibling
membership, with the saved and generated orders separately recorded.
Four controls each refuse a missing binary owner. After loading the
standard library codecs, the process audit blocks all filesystem opens
during projection. This disclosed archive measurement adds zero native
process launches or held-out qualifications.

```sh
python3.14 -I -B re/tooling/sw2026/key_index/AuditAllPartKeywordOwners.py /tmp/UnusedPartKeywordOwners.json
```
