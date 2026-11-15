# Creo adapter

## Purpose and scope

The `creo.prt` adapter reads PTC Creo Parametric and Pro/ENGINEER PSB part files.
It validates the container, lists sections, inflates compressed sections, extracts the native thumbnail, decodes `AllFeatur` feature identity rows, and retains the source bytes for exact replay.
It does not decode native geometry, sketches, or dimensions into neutral records.

## Container

A PSB file starts with an ASCII `#UGC:2` header.
The last hexadecimal token on the first line is the section base.
The header ends at `#-END_OF_UGC_HEADER`.
A product banner follows, then a fixed-width `#UGC_TOC` table.

| Field | Meaning |
| --- | --- |
| `#UGC:2 PART` | Part document |
| `#UGC:2 ASSEMBLY` | Assembly document |
| `#- CMNM` | Common model name |
| `#UGC_TOC` | Section directory |
| `NEXT_TOC_ENTRY` | Continuation table |
| `1f 9d` | Unix-compress section payload |

Section offsets are relative to the header base.
Stored lengths include the `#<name>\n` section header.
The reader validates each extent before exposing a section.

## Reading

The reader returns a `CadDocument` with:

- source identity, PSB container version, and product version;
- model kind, common name, header lines, and section inventory;
- the native JPEG thumbnail as an auxiliary payload;
- the retained source bytes and digest;
- `AllFeatur` feature identity rows as `FeatureStep` records, each with the Creo feature id, root
  schema class, class label, and a provenance span into the `AllFeatur` section;
- `FeatDefs` stored dimension values as `Parameter` records, linked to the single protrusion
  feature's `parameter_ids` when exactly one exists;
- `VisibGeom` plane and curve prototypes as one `DesignBody`, with face and edge counts, per-face
  records, shell closure proven from the curve half-edge graph, and volume and centre of mass
  computed from the decoded plane frames;
- warnings that sketches, curved trims, and open surfaces remain encoded.

Feature rows are discovered from the tag anchors documented in
[the compound-boundary gotcha](../../Gotchas/Conversion/CreoTaggedCompoundBoundary.md): a boundary
is offset zero or a byte after `0xe3`, and the row carries `e3 f6 <compact-class> e1` within the
next 16 bytes. Rows shorter than 16 bytes and rows whose class is not a known feature class are
rejected. The first feature is also taken from its `e0 01 id 00` definition when the anchor is
outside the window.

The reader does not report bodies, sketches, dimensions, or parameter values.
Do not treat a successful read as native geometry coverage.

Metadata reports `creo.feature_rows_decoded`, `creo.feature_row_count`, `creo.dimension_count`,
`creo.parameters_decoded`, `creo.feature_history_decoded` (still false: no sketch or definition
bodies), and `creo.geometry_decoded` (still false).

## Writing

Two paths exist.

`src/convert/adapters/creo/Author.py` generates sections from format knowledge and, on the retained
control's container, produces a part Creo 2027.2 accepts: a four-record `AllFeatur` with zero vendor bytes
(three datum planes and a coordinate system, all authored) and a `FeatDefs` row carrying one dimension. Two
candidates were opened in Creo with `-g:no_graphics`, each twice, and the trail records `End` and
`MT Part Solid`:

| Candidate | Authored | Creo |
| --- | --- | --- |
| `auth4` | 41 of 54 directory rows, fully generated `AllFeatur` | loads, 2 of 2 |
| `featdefs` | 42 rows, plus generated `FeatDefs` with one dimension read back as `100.0` | loads, 2 of 2 |
| `fd_two` | 42 rows, `FeatDefs` with two dimensions read back as `100.0` and `42.5` | loads, 2 of 2 |

`AuthorBox` produces a six-plane `VisibGeom` whose volume and centroid round-trip through the reader, but a
part carrying that `VisibGeom` is **not** accepted by Creo: six candidates exited with no `End` line. A
class-`917` protrusion is not authored either — a record built from its 37 declared fields with null values is
refused, as is a `917` replay carrying datum values.

So the authored part contains features and one dimension and **no body**. There is no Creo-measured body
count, volume, centre of mass or feature tree for authored output, and 13 of the 54 rows remain
vendor-sourced because they were measured required.

For an existing document the writer supports exact source replay only.
It requires the retained source bytes and verifies their digest before writing.
It refuses a document without retained Creo source bytes.

The result reports `mode="exact_native_roundtrip"`.
It keeps `vendor_loadable` and `application_usable` false because this path does not measure a newly authored model.

## Limits

- No body: authored output carries features and a dimension but no solid, and authored `VisibGeom` and `917`
  records are refused by Creo, so no body count, volume, centre of mass or rebuild is measured.
- Feature identity, stored dimension values, surface prototypes, compact `local_sys` frames, identifier-proven shell closure, and convex-polyhedron volume and centroid: no sketches, no curved trims, no non-convex shells.
- No native geometry or B-rep decoding.
- No assembly component resolution.
- No drawing, format, section, or layout support.
- No claim of lossless cross-format translation.

## Sources

- [Adapter](../../../src/convert/adapters/creo/Adapter.py)
- [Header](../../../src/convert/adapters/creo/Header.py)
- [Table of contents](../../../src/convert/adapters/creo/Toc.py)
- [Reader](../../../src/convert/adapters/creo/Reader.py)
- [Feature records](../../../src/convert/adapters/creo/Records.py)
- [Writer](../../../src/convert/adapters/creo/Writer.py)
- [Container findings](../../../re/creo/container/Container.md)
- [Writer gap](../../../re/creo/open-items/WriterGap.md)
- [ARM64 startup gotcha](../../Gotchas/Conversion/CreoArmStartup.md)
- [Legacy ASCII rejection gotcha](../../Gotchas/Conversion/CreoLegacyAsciiRejected.md)
- [Change entry](../../Changes/Creo/CreoPsbContainer.md)
- [Feature record change entry](../../Changes/Creo/CreoNeutralFeatureRecords.md)
