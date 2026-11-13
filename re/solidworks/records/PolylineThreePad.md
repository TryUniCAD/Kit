# Three-line blind-boss native research

## Scope and boundary

This record covers a closed, simple three-line sketch on the Front Plane followed by one forward blind boss extrusion. Native identities are sketch 26/`Sketch1`, pad 32/`Boss-Extrude1`, plane 2, and end codes `(0,0)`. There are no sketch dimensions, authored solver relations, construction entities, fixed entities, or additional loops in the controlled inputs.

The bounded three-line blind-boss family is now implemented and vendor-accepted as detailed below. Other sketch families, histories, assemblies, drawings, and broad B-rep coverage remain outside that claim. The captured source files are research inputs only; they are never read by production or embedded as donor streams.

## Vendor-authored inputs

SOLIDWORKS 34.5.2 created every source from an explicit ordered coordinate list through `re/tooling/harness/AuthorTriangles.vbs`. Each has three sketch segments, a native `Sketch1`, a native `Boss-Extrude1`, one solid body, and a successful rebuild.

| Input         | Vertices, millimetres        | Depth, mm | Area, mm² | Volume, mm³ |   Surface area, mm² |
| ------------- | ---------------------------- | --------: | --------: | ----------: | ------------------: |
| `tri3a`       | `(0,0), (42,0), (12,31)`     |         9 |       651 |       5,859 |  2,367.427645476918 |
| `tri3b`       | `(-7,-11), (39,-4), (17,38)` |        17 |     1,043 |      17,731 |  4,610.577015505639 |
| `tri3deep`    | `(0,0), (42,0), (12,31)`     |        21 |       651 |      13,671 | 3,787.9978394461414 |
| `tri3reverse` | `(12,31), (42,0), (0,0)`     |         9 |       651 |       5,859 |  2,367.427645476918 |
| `tri3tie`     | `(0,0), (36,0), (36,24)`     |        11 |       432 |       4,752 | 1,999.9327683612466 |

The areas are independently `abs(shoelace)/2`. Each measured volume is `area × depth`. Each measured surface area is `2 × area + perimeter × depth`. This is vendor evidence for the authored sources, not acceptance of a generated native file.

The author harness takes the host research root explicitly. It does not delete prior files; an existing target is reported as `PREEXISTING_SKIP`. The separate seeded branch permits up to 512 monotone-angle, nonzero-radius triangles with independent depths. A future corpus run still needs independent vendor acceptance, not just successful source creation.

## Native stream identity

All five source documents contain 40 streams and the 2026 envelope:

- `_MO_VERSION_19000/Biography` and `_MO_VERSION_19000/History`;
- `Contents/Definition`: 3,816 bytes;
- `Contents/CMgr`: 2,159 bytes;
- `Contents/Config-0`: 25,476 bytes;
- `Contents/Config-0-ResolvedFeatures`: 10,601 bytes.

The resolved-feature stream begins `6d 00 00 00 13 00 ff ff`, so the initial object-map continuation is `0x6d` (109). The five-line family has 11,205 bytes, so count substitution and direct reuse of its offsets are invalid.

The principal triangle's same-profile depth variant changes only requested depth. The reversed/source-start-shifted variant tests closure references independently of geometry. The right-angle case has two rightmost vertices; it prevents importing the five-line unique-rightmost attachment rule without evidence.

## Capture status

The attached object trace completed with `ORACLE_EXIT=0` and 300 reads of each object/class kind. Segmentation tiled all 10,601 bytes with 300 objects, 40 class definitions, base map 109, and zero counter mismatches.

The correct primitive capture uses direct `cdb` attachment and stream-span filtering, not the failing wrapper/lazy-symbol path. It records 2,946 events, all against the 10,601-byte stream. The generated program has 2,518 operations over 495 serializer owners and zero uncovered bytes. Independent re-emission yields `5088c5c909bc432b12ee2f50f8aaa7934f3232e62ef30bb0a6d1563ac340ced0`.

The dynamic field map contains 51 values: six coordinates, four positive-depth fields at 9408/9480/9968/9992, two negative-depth fields at 9806/9830, eight bbox fields at 8201–8225 and 8423–8451, 24 display-plane fields, four attachment witnesses at 9440/9448 and 9464/9472, two transformed attachment witnesses at 9637 and 9653, and the scaled attachment at 9726.

`range * 1.1 / 2000` is the measured expansion order for range values and expanded z. The scaled attachment is `x / 5000`. These are not arbitrary reassociations of the assessed geometry-preserving formulas.

The attachment tie uses the first rightmost coordinate, verified by the two-rightmost right-angle control. It is not discovered through the five-line uniqueness heuristic.

## Accepted production path

`re/tooling/ProgramDecomposition/AddProgram.py` adds the three-line facade, registry, and typed methods without replacing unrelated owner catalogs or streams. Complete verification now reports 45 programs, 77 streams, 215 catalogs, 2,461 owners, 3,995 methods, and 190,316 operations.

Fresh public neutral-document writes produce one three-line `Sketch1` and one forward `Boss-Extrude1`. Late-bound SOLIDWORKS 34.5.2 inspection confirms the native profile feature and extrusion, and `D1@Boss-Extrude1` remains live and editable. All four fresh files have zero load errors and warnings, one body, and a successful rebuild.

| Public input family          | Depth, mm | Volume, mm³ |           Area, mm² |
| ---------------------------- | --------: | ----------: | ------------------: |
| `(0,0), (42,0), (12,31)`     |         9 |       5,859 |  2,367.427645476918 |
| `(-7,-11), (39,-4), (17,38)` |        17 |      17,731 |  4,610.577015505639 |
| `(0,0), (42,0), (12,31)`     |        21 |      13,671 | 3,787.9978394461414 |
| `(0,0), (36,0), (36,24)`     |        11 |       4,752 | 1,999.9327683612466 |

Changing the shifted public part to 5 mm rebuilds to 5,215 mm³ and 2,828.5226516193 mm² before closing without saving. The measured values match `area × depth` and `2 × area + perimeter × depth`.

The capture digest is not expected to match arbitrary new documents' author metadata or all view-state floating-point values. Native open, feature-tree identity, body geometry, and live-edit acceptance are independently measured instead of using that digest as application acceptance.

This completion is scoped to this family. There is no accepted randomized oracle corpus, arbitrary SLDPRT history support, complete B-rep grammar, SLDASM, or SLDDRW claim.
