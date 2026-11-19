# Linked concentric mate archive in SOLIDWORKS 2026

Task `B04-SW2026-MATES-CONCENTRIC`, PR #121. Three disclosed native
assemblies each supply an original save and an edited save. The
controlled source cohort also locks two guest-private input pairs.
The host verification reads the six disclosed assembly and child pairs.
[Source method](ConcentricMateConstructionSources2026.md)
[Source and archive receipt](../measurements/2026/ConcentricMateSourceArchive01.json)

## Linked map and endpoint owners

Config-0 and ResolvedFeatures provide the actual inherited model,
occurrences and external-feature objects. Their typed re-emission
matches in all six inputs. The mate list starts at inherited counter
168 and ends at 221. It adds fourteen class slots and thirty-nine
object slots. The two serializers use the same inherited identities,
and every read/write entry has the same slot and actual object or
class owner. The mate list lengths span 3,690 to 3,966 bytes.

The concrete `moMateConcentric` has two ordered support rows in
`f3c8` and two distinct active endpoint rows in `f410`. All four
members are `moCylinderRef_w` objects. These are separate sets.

- Each support wrapper points to `moCompRefCylinder_c`, with a real
  `moRefCylinder_c` in `ff8` and the related `moFacetedData_c` in
  the component-reference owner. The support and active cylinder
  point, axis and radius match in every measured state.
- Each active wrapper points to `moCompFace_c`. Its chain resolves
  through the actual inherited external-feature object and its
  reciprocal reference into the original occurrence list. Both
  persistent occurrence IDs match the independent COM observations.
  Its `f74` is the real owning mate ID.
- Each active face retains a `moFaceRef_c` and its ordered entity
  IDs. In the measured cohort those include the sketch-side surface
  identity and two end-face identities. The sketch-side identifier
  carries a `moFR_c` reference to the producing child extrusion
  and its first ModelHeader creation event. That extrusion's actual
  profile owns the circle. The surface field `f38` matches the arc's
  permanent marker `f08`. The circle's separate creation ID `f0c`
  has the same value in these controls. The active wrapper's optional
  vector is separately stored. Deriving that local vector and the
  full faceted snapshot from new feature topology remains open.

The archive's aligned and anti-aligned selectors are 1 and 2.
The two aligned cases isolate API rotation lock in the first
ordinary signed tail word `f4b8`, with 0 and 1 on both original
and edited files. The independently placed anti-aligned case retains
the same lock interpretation. Position value `f4c4=-1` omits the
misalignment payload in all six states.

## Concrete field order

The pinned 2026 module identity and function ranges are in the
receipt. REA verified the original x64 image and its section layout.
LLVM inspected the bounded serializer functions outside the
repository. The current wire profile is archive version 19000.

| Class | Reached field order and ownership | Native entry |
|---|---|---|
| `moMateConcentric` | Shared two-geometry base, signed lock and position words. The ordinary branch has no additional tail. | `0x4b669080` |
| `moCylinderRef_w` | Shared surface wrapper, `fd0` point, `fe8` direction, `f100` radius and unsigned-word presence for the `f108` vector. | `0x4c26f8f0` |
| `moCompRefCylinder_c` | Current component feature base plus its `ff8` reference geometry through the shared component reference-geometry serializer. | `0x4bba5890` → `0x4bba6c80` |
| `moRefCylinder_c` | Reference-geometry base, `f6f8` point, `f710` direction and `f728` radius. | `0x4c27cef0` |
| `moFacetedData_c` | Point presence and counted point array when present. The current tail has signed words `f40,f44,f48,f4c,f14,f50,f54`, followed by the signed emptiness word and optional CString. The measured objects have no points. | `0x4b7ec410` |
| `moCompFace_c` | Component-reference base, alias byte, alias text when present, `fe8` and `ff0` reference owners. The measured alias byte is zero. | `0x4bba46c0` |
| `moFaceRef_c` | Shared boundary-entity base and the ordinary additional-face record count. This cohort has an empty additional list. | `0x4bba9640` |

The research verifier compares the actual stored axes, points and
radii to COM, validates twelve endpoint occurrences and binds all
twelve face references to their hash-checked child extrusion and
profile. All three independent creation epochs remain stable after
edits. The verifier writes back all eighteen linked assembly
streams directly from typed objects and retains the exact
class and alias graph. The broader reader, generation of the
remaining face and facet identities, native candidate verification
and held-out writer acceptance remain open.
[Replay tool](../../tooling/sw2026/VerifyConcentricMateStreams.py)
