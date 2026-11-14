# Creo PSB data model

## Scope and confidence

This page describes the data layers found in Creo PSB part files.
The `confirmed` label means the layer is present in multiple unrelated files and its framing is validated.
The `partial` label means the layer exists but the field map is incomplete.
The `not found` label means the field was not located.

The production adapter currently reads the container and source replay path only.
This page records the model needed for the next implementation phase.

## Layer map

| Layer | Container | Contents | Status |
| --- | --- | --- | --- |
| Envelope | Text header and `#UGC_TOC` | Identity, version, section directory | Confirmed |
| Storage | Named sections | Plain, Unix-compress, binary | Confirmed |
| Record grammar | Tagged stream | Self-describing fields and arrays | Confirmed grammar, partial field map |
| Geometry | `VisibGeom`, `NovisGeom` | Surfaces, curves, contours, topology | Partial |
| Design | `AllFeatur`, `FeatDefs`, `FeatDefsDtm` | Features, dimensions, sketches, datums | Partial |
| Units | `UnitSystemDef` | Length, mass, angle systems | Partial |
| Display | `SolidPrimdata`, `ModelView#*`, `THMB_IMG_MAIN` | Annotation strips, views, JPEG | Partial |
| Bookkeeping | Header, `MdlStatus`, checksums | Session identity, counts, version | Partial |

## Tagged stream grammar

A section is a stream of typed values.
A field is introduced by a named-record header.

```text
e0 <type> <name> 00
```

The first use of a field stores its type and name.
Later uses refer to the field number and the remembered transition.
The field number is carried by `f7 <id>`.

| Token | Meaning |
| --- | --- |
| `e0 <type> <name> 00` | Field definition |
| `f1` to `f4 <n>` | Close one or more structures |
| `f7 <id>` | Select the next field |
| `e1` | Null |
| `e2`, `e3` | Structure begin or end |
| `f8 <n>` | Array of `n` elements |
| `f9 <rows> <cols>` | Count-bounded scalar body |
| `fa <rank> <dims>` | Array rank and extents |
| `fb` | Array close |
| `e4` to `e6` | Repeat the previous element once to three times |
| `e7 <n>` | Repeat the previous element `n` times |

The field transition cache is the reason a field can be absent from the byte stream and still exist in the model.
The cache is reset at document or section boundaries.

## Scalars

| Type | Meaning |
| --- | --- |
| `00` | Structure |
| `01`, `05`, `07`, `08`, `09`, `0b` | Integer |
| `02` | Double |
| `03`, `0a` | String or byte string |
| `04` | Byte |
| `06` | Float-precision number |

Compact integers use:

| Bytes | Value |
| --- | --- |
| `00` to `7f` | One-byte value |
| `80` to `bf XX` | Two-byte big-endian value |
| `c0` to `df XX YY` | Three-byte big-endian value |
| `e8` to `eb` | One to four explicit bytes |
| `f5 <int>` | Negated value |
| `f6` | Minus one |

Doubles are IEEE-754 big-endian values with a compressed high byte.
One-byte constants cover common values such as zero, one, minus one, pi, and pi fractions.
Group tokens and class tokens supply the high bytes, then the stream supplies the mantissa tail.
Escapes supply explicit bytes.

## Geometry section

`VisibGeom` carries the visible B-rep.
The section root is `Sld_VisGeom`, then `active_geom`.
The principal arrays are:

```text
srf_array[]
  geom_id
  geom_type
  feat_id
  boundary_type
  next_geom_ptr
  orient
  srf_prim_ptr
  frst_cntr_ptr
  next_cntr_ptr
  topol_ref_data

crv_array[]
  crv_id
  type
  crv_pnt_dir[2]
  crv_pnt_arr[n][4]
  crv_hdr_geom_ptr[2]
  next_crv_hdr_ptr[2]

body_array[]
  body_id
  outline
  first_geom_ptr
  material pointer
```

Observed `geom_type` families include plane (`0x22`), cylinder (`0x24`), cone (`0x25`), torus or sphere (`0x26`), spline (`0x28`), fillet (`0x29`), and linear extrusion (`0x2a` or `0x2c`).
The type selects the prototype field body.

A prototype carries a `local_sys` frame.
The frame is a `[4][3]` array in row-major order.
Columns zero to two are the two radial directions and the normal or axis.
Row three is the origin.

| Surface | Placement and parameters |
| --- | --- |
| Plane | `O + u X + v Y` |
| Cylinder | `O + r(cos u X + sin u Y) + v Z` |
| Cone | `O + v tan(half-angle) (cos u X + sin u Y) + v Z` |
| Torus | `O + (R1 + r cos v)(cos u X + sin u Y) + r sin v Z` |
| Sphere | `R1 = 0` torus with radius `r` |
| Spline | Interpolating bicubic grid with end tangents and corner twists |
| Fillet | Rolling-ball blend with a centre curve, radius vector, and tangent |
| Ruled | Linear interpolation between two curves |

`orient` is `1` or `-1`.
A face with `topol_ref_data.list_type = 98` belongs to the solid body whose id is `list_id`.
A face with `list_id = -1` is loose or cosmetic.

The contour table stores an outer or inner flag, a first curve pointer, and traversal data.
`crv_pnt_arr` stores the same edge sample in both neighbouring faces' parameter spaces.
The sample order and direction resolve trimming.

## Design section

`AllFeatur` carries feature rows, generated-entity tables, affected-geometry identifiers, and references.
`FeatDefs` carries feature definitions, placement records, outlines, dimensions, and saved section entities.
`FeatDefsDtm` carries datum feature definitions.

Feature identity is split across a native id, a user-visible name, a type, a parent feature, and references.
The data model needs all of these to rebuild a live tree.
Copying a feature row without its references is not a feature.

## Units

`UnitSystemDef` carries the active unit system.
Observed selectors include:

| Selector | System | Length scale |
| ---: | --- | --- |
| 50 | CGS | 10 mm per stored unit |
| 51 | mmNs | 1 mm per stored unit |
| 54 | inLbmS | 25.4 mm per stored unit |
| 55 | mmKs | 1 mm per stored unit |

The `string_xar` names can include `Offset` and a unit token.
The active selector is the authoritative value when present.

## Parameters and expressions

Dimensions are stored as parameter references.
A driving dimension needs:

- parameter identity;
- value and unit;
- expression or relation source;
- owner feature and sketch;
- referenced entities;
- configuration overrides.

The field map for relations and configurations is partial.
A writer that emits a number without its parameter identity would produce a dumb shape and fail the parametric criterion.

## Derived and bookkeeping data

B-rep caches, display strips, view state, timestamps, session ids, and checksums are derived or bookkeeping.
They must not be copied between documents.
The source-preserved replay path can keep them only because the output is the same document.

## Open questions

- The per-field transition cache is not fully mapped.
- The geometry prototype lanes have unresolved scalar prefixes.
- The feature definition schema is not closed for every family.
- The unit selector must be read from the section, not from a fixed default.
- The writer must reproduce every authored record and recompute every derived record from the neutral model.

## Sources

- [Cadmpeg Creo specification](https://github.com/cadmpeg/cadmpeg/blob/main/docs/formats/creo_prt.md), CC-BY-4.0
- [TeamCraft Creo research](https://github.com/rudalabs/TeamCraft/blob/main/docs/src/research/creo-brep-preview.md)
- [Container findings](Container.md)
- [Writer gap](../open-items/WriterGap.md)
