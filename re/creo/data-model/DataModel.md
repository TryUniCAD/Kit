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

### Geometry prototypes

`VisibGeom` (`Sld_VisGeom`) carries the geometry prototype records. The ladder's first record is a
plane surface:

```text
geom_id = 77
geom_type = 34
feat_id = 74
orient = -1
boundary_type = 0
next_geom_ptr = 82
srf_prim_ptr(plane) = 48865
frst_cntr_ptr = 108
frst_cntr_crv_hdr_ptr = 105
trv = 110
next_cntr_ptr = 0
```

`geom_type = 34` is a plane surface, `feat_id = 74` is the owning feature, and `srf_prim_ptr(plane)`
is the surface primitive pointer. `frst_cntr_ptr` and `frst_cntr_crv_hdr_ptr` are the first contour
and curve header pointers. The prototype's `envlp` decodes to
`[184.50782059963194, 86.06680966899467, -154.4303300690026, -115.65227549271083]` and its
`outline` to
`[184.50782059963194, 1.0, 115.65227549271083, -154.4303300690026, 1.0, -86.06680966899467]`.
The parser then stops at `0x14a` in the `local_sys` cache index lane.

Feature identity is split across a native id, a user-visible name, a type, a parent feature, and references.
The data model needs all of these to rebuild a live tree.
Copying a feature row without its references is not a feature.

### Ladder field additions

The one-feature ladder at `re/creo/oracle/ladder/ladder1.prt.2` adds these `AllFeatur` field names
that are absent from the empty control:

```text
flags
first_hybrid_body_id
topo_parents
avail_feat_parents
dtm_id_tab
dtm_id
dim_id
comp_hist
owner_id
component_ids
sorted
revnums
owner_type
owner_ind
ref_id
hist_ref_info
coll_refs_info
ref_revnum
ref_plcm_revnum
ref_status
dma_update_revnum
flags_arr
upd_ctrl_data
upd_ref_revnum
upd_coll_refs_info
upd_aggr_rev_info
rev_info_arr
info(basic_geom_rev_info)
mdl_geom_rev
revision(mdl_g_rev_dtl_t_ft_regen)
rev_cnt
tstamp
version
versions
aggr_rev_info
aux_rev_data
edg_id_tab_ptr
ed_hist
lo_id_tab_ptr
lo_hist
```

The names confirm that the ladder carries feature-parent links, dimension ids, component ids, and
revision records.
They are the fields a writer must populate for a live tree, not just a shape.

### First feature record

The first `AllFeatur` record in both the empty control and the ladder decodes as the same datum
feature. The ladder's record is:

```text
id = 7
indep_attributes_arr = [4097, 0, 0, 0, 0, 0]
feat_type_ptr = empty
table_id = -1
type = 923
feattype_key = null
form = 0
attributes = [0, 0, 0, 0, 0, 0, 0, 0, 16, 0, 0, 0, 0, 0]
placement = 0
intersection = -1
internal_udf_type = -1
param_choice_ptr = empty
blend_choice = 0
depth_choice = 0
angle_choice = 0
pat_choice = -1
round_choice = -1
subsec_choice = -1
sweep_choice = 0
dome_choice = 0
draft_choice = 0
misc_choice = [0, 0, 0, 0, 0, 0]
sect_name = "FRONT"
```

The `sect_name` and the empty `feat_type_ptr` identify the default `FRONT` datum plane.
The record is a useful anchor because it is present in both files and its field order is stable.
The empty control's record has the same `id`, `type`, and `sect_name`, but its
`indep_attributes_arr` has four elements and its `attributes` array has eleven; the ladder's arrays
are longer. The array lengths are therefore document-dependent, not fixed.
The ladder's extrude and sketch records follow it, but their field boundaries are not yet closed.

### Decoded feature chain

`re/creo/tools/TaggedStream.py` now decodes the full `AllFeatur` feature chain of both controls.
The chain is a linked list: `first_feat_ptr` points at the first feature, and each feature's
`next_feat_ptr` points at the next one. A zero `next_feat_ptr` ends the list.

| File | Feature chain |
| --- | --- |
| `empty/solid_start_part_mmks.prt` | `FRONT` (id 7, type 923), `TOP` (5, 923), `RIGHT` (3, 923), `DEFAULT_CSYS` (11, 979) |
| `ladder/ladder1.prt.2` | the same four, plus `id 67` (type 923) |

The chain matches the model tree Creo shows for both files.
Type `923` is a datum plane and type `979` is a coordinate system.
The ladder's fifth feature is the sketch's datum plane; the sketch and extrude definitions live in
`FeatDefs` (`Sld_FeatDefs`), not in `AllFeatur`.

The grammar that makes the chain decode is recorded in
[the loader notes](../loader/Loader.md#tagged-stream-parser-status):

- the field table is global, and `f7 <id>` selects the id-th field;
- `f1`-`f4` close tokens may precede a value and pop structure levels first;
- `f8`/`f9` array counts are part of the first definition and are reused by later records;
- `next_feat_ptr` restarts the field index at the feature schema's first field.

### Datum placement records

`FeatDefsDtm` (`Sld_FeatDefsDtm`) carries the datum placement records. The first record is the
`FRONT` datum:

```text
id = 7
symbol_key = -1
model_type = 2
local_sys = [0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1]
own_ref_id = -1
orient = 1
place_instruction_ptrs = [ref 11]
type = 515
offset = 1.0
dim_id = -1
ref_id = -1
geometry1_id = -1
geometry2_id = 8
memb_num1 = 0
memb_num2 = 0
attr = [32768, 0, 0, 0, 0]
plin_info_arr = [ref 21]
```

`type = 515` is the placement type, `offset = 1.0` is the placement offset, and
`geometry2_id = 8` is the reference geometry. `attr` is the datum attribute array.
This is the parametric placement of the datum plane, not just a name.

The `ent_outl` bounding-box matrix uses the world-coordinate token lane, not the hex-string
encoding. The `ugc_ieee_unformat_double` function reads a hex string where each byte's low nibble
is a hex digit, and stores the bytes into the double buffer from the end backwards. The `0x0f`
(0.0) and `0x18` (1.0) one-byte constants are handled by the caller, not the function.

The hex-string hypothesis is disproved for `ent_outl`: `0x46` is a valid hex digit but `0x6f` is
not, so the reader consumes one digit and fails. The bytes are world-coordinate tokens. In the
positional-outline/world lane, `46 <tail7>` reconstructs `40 <tail7>` (positive) and `2d <tail7>`
reconstructs `C0 <tail7>` (negative). The seven-byte sub-unit forms `4f <tail6>` and `d5 <tail6>`
reconstruct `3F <tail6> 00` and `BF <tail6> 00`. The `0x18` byte is the one-byte 1.0 constant.

The empty control's `ent_outl` decodes to
`[254.33012701892218, 254.33012701892218, 1.0, -254.33012701892218, -254.33012701892218, 1.0]`,
a square in homogeneous coordinates. The ladder's `ent_outl` decodes to
`[186.8986780200836, -0.000125701882057086, 1.0, -156.82118748945425, -272.72085742045164, 1.0]`,
a rectangle in the sketch plane. The ladder's `outline` decodes to
`[186.8986780200836, 1.0, 118.04313291316248, -156.82118748945425, 1.0, -88.45766708944632]`.
The `VisibGeom` plane prototype's `envlp` decodes to
`[184.50782059963194, 86.06680966899467, -154.4303300690026, -115.65227549271083]` and its
`outline` to
`[184.50782059963194, 1.0, 115.65227549271083, -154.4303300690026, 1.0, -86.06680966899467]`.

### Feature definitions

`FeatDefs` (`Sld_FeatDefs`) carries the feature definitions. The ladder's first definition is the
extrude feature:

```text
id = 66
symbol_key = -1
model_type = 2
local_sys = [0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1]
own_ref_id = -1
orient = 0
trf_arr = [ref 11]
type = 1
key = -1
idx = 0
transf = [1.0, RawDouble(...)]
plcm_revnum = None
next_prop = None
cond_tbl_idx = -1
comment = None
merge_info_ptr = None
state_ind = -1
alumni_info = None
sub_feat_arr = [ref 23]
id = 0
type = 160
sub_type = -1
data(subft_indexnumber) = { index = 1, tool_type = 60001, sep_index = -1 }
expl_state_ref = None
feat_outl_info = { ent_outl = [...] }
max_text_len = 85
```

`type = 160` is the feature definition type and `tool_type = 60001` is the extrude tool type.
The parser stops at `0x3be` because the flat field-index approach does not handle the nested
structures in `FeatDefs`; the field table is global but each structure has its own schema.

### Loader-confirmed record schemas

The `metatoolsapi.dll` `CreoSerializer` exports give the authoritative field order and types for the
high-level records. The full field tables are in [the loader notes](../loader/Loader.md).

`CreoDesignatedItem` is the live feature-tree record:

```text
Id, Type, SubType, DsgnName, CreoName, OwnerId, OwnerType, ModelLikeAttr,
FeatureStatus, FeatureInStockAttr, Symbols, KeyPropsFlag
```

`Symbols` is a sequence of `CreoParameter`. `OwnerId` and `OwnerType` are the parent links.

`CreoParameter` is the dimension record:

```text
CreoParameterValue, CreoParameterDef, CreoModel, CreoName, IsReadOnlyInProE,
IsReadOnlyInDB, IsSystemParameter, DBName, ValueType, Default, Restriction,
AccessTbl, DefinitOwner, IsChanged, QuantType, Description, Class, Label
```

`CreoParameterValue` is the value record:

```text
Integer, Bool, Real, DoubleEpsilon, Unit, String, DateTime, Icon, Link, User,
CreoQuantType, Length, Time, Mass, Temperature, Current
```

`Real` is the numeric value, `Unit` is the unit token, and `CreoQuantType` selects the quantity
family. A writer that emits `Real` without `CreoParameter` identity and `CreoQuantType` would produce
a dumb number, not a driving dimension.

`CreoItem` is the model-level record. Its `CreoDesignatedItems` field is the feature sequence, its
`CreoModelParameters` field is the parameter table, and its `CreoDependencies` field is the
dependency table.

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
