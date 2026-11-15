# CATIA OSMX feature graph

## What is decoded

The outer `CATPrtCont` and `CATProdCont` streams start with `OSMX`. The OSMX stream has a symbol
table at offset 100, a `|\x02` marker, a section length, and a symbol data section. The symbol table
contains class names, plane names, and part names.

The reader exposes the symbol table as `catia.native_symbols`, `catia.part_symbols`, and
`catia.product_symbols`. It also exposes the three principal planes as `SupportPlane` records.

## What is not decoded

The OSMX stream is a symbol table, not the complete feature graph. The feature records, sketch
records, dimensions, constraints, and relations are not decoded. The reader retains the exact OSMX
bytes as a `NativeFeatureDefinition` payload.

## The object graph before the symbol table

The OSMX stream is not only a symbol table. In `Bolt_M5x40` the `_310c_670c0c48_ae0` stream is 4098
bytes: the symbol table starts at 3418, so bytes 104..3410 are an object graph. The graph contains
16-byte GUID-shaped runs such as `09 dc 64 11 00 00 01 1e 35 dc 47 a1 00 00 00 01`, repeated at
offsets 112, 140, and 180. The u32 at offset 100 is 3410, which is the symbol table offset minus 8,
so the graph ends 8 bytes before the table.

The `_310c_670c0c48_ae2` stream (1968 bytes) is a second object graph. It is a sequence of 66-byte
records: the four records at 0, 66, 132, and 198 each carry the same little-endian timestamp
`0x670c0c48` (1728842824, 2024-10-13) at record offset 22. Each record has a small type at offset 0
(`0f 00`, `00 02`, `00 23`, `00 44`), a u16 id at offset 12 (11, 17, 23, increments of 6), a u16
size at offset 16 (56, 56, 124), a u32 offset at offset 28 (504, 505, 571), a u16 `4` at offset 32,
a u32 at offset 34 (11, 13, 19), a flag byte at offset 38, and a run of u32 child indices. The
record grammar is not fully resolved: the u32 at offset 34 does not equal the child count, and the
first record has a different prefix from the other three.

## The domain-byte scan is unreliable

`CATMathFunctionGeneral::UnStream` reads a domain byte (`0x41` 'A', `0x47` 'G', `0x46` 'F', `0x43`
'C') and a u16 type. Scanning `SurfacicReps` for that pair gives many hits, but they are false
positives: little-endian floats contain `0x41` and `0x43` bytes. In `4784` the domain-C hits at
8329, 8611, 8893, ... are spaced 282 bytes apart, and the bytes at 8329 are `43 41 00 42 e0 3d d8
62`, which is the tail of a float run, not a function header. The PCurve record therefore cannot be
located by a domain-byte scan.

## The corpus has no parametric history

Every one of the 27 corpus parts carries the `FromCATPart` symbol, which marks a shape imported
from a CATPart rather than a natively modelled feature tree. Scanning every OSMX symbol table for
`Sketch`, `Pad`, `Pocket`, `Constraint`, `Dimension`, `Revolution`, `Groove`, `Chamfer`, `Fillet`,
`Shaft`, `Hole`, `Pattern`, `Mirror`, `Extrude`, and `Revolve` returns no hits in any part. The only
`Body` symbols are the part-body names `Body.2` and `Body.3`. The symbol tables contain product and
part metadata (`ASMPRODUCT`, `PRDREP`, `MechanicalPart`, `_FtrList`, `_ReferencePlanes`, `GSMPlane`,
`xy-plane`) and nothing that names a modelling feature.

The corpus therefore cannot validate a parametric-history decoder: there is no sketch, dimension, or
constraint in it to decode. A parametric decoder needs a corpus of natively modelled parts, which
must be produced through the vendor API or supplied by the user.

## The vendor install supplies a parametric corpus

The CATIA V5-6R2022 install contains 6979 `CATPart` files under
`C:\Program Files\Dassault Systemes\B32\win_b64\startup\components` and
`...\win_b64\reffiles`. 78 of the 79 sampled files carry a modelling vocabulary. Five of them are
copied into `re/catia/examples/parametric/`:

| file | symbols | feature vocabulary |
| --- | --- | --- |
| `ISO_10642_HEXAGON_SOCKET_COUNTERSUNK_SCREW` | 328 | `2DCircle`, `2DLine`, `2DPoint`, `ConstraintDYS`, `Constraints`, `EdgeFillet`, `EdgeFillet_Radius` |
| `ISO_1207_GRADE_A_SLOTTED_CHEESE_HEAD_SCREW` | 309 | `2DLine`, `2DPoint`, `ConstraintDYS`, `Constraints`, `EdgeFillet`, `FilletType` |
| `ISO_2010_GRADE_A_COUNTERSUNK_SLOTTED_RAISED_HEAD_SCREW` | 320 | `2DCircle`, `2DLine`, `2DPoint`, `CircPattern_AngularNumber`, `CircPattern_AngularStep` |
| `ISO_2338_PARALLEL_PIN` | 234 | `2DCircle`, `Chamfer`, `Chamfer_Angle`, `Chamfer_Length1`, `Chamfer_Length2` |
| `ISO_7089_PLAIN_WASHER_GRADE_A_NORMAL_SERIES` | 238 | `2DCircle`, `Chamfer`, `Chamfer_Angle`, `Chamfer_Length1`, `Chamfer_Length2` |

`re/catia/tooling/Parametric.py` classifies a part as `parametric` when its largest OSMX symbol
table contains a feature word, and as `dumb` otherwise. It reports 27 dumb and 5 parametric parts
over `re/catia/examples`.

## The OSMX symbol table has an extended length

The symbol table is `|\x02`, a u32 section length, then a sequence of symbols. A symbol is a length
byte followed by `length - 1` ASCII bytes. A length of zero means the next four bytes are a
little-endian u32 length and the value is that many bytes. The extended form carries the design-table
text, which contains newlines, so the printable check must allow `\t`, `\n`, and `\r`. The
`ISO_10642` symbol table has 328 symbols and ends exactly at the section end; the earlier parser
rejected it because it treated the zero length as a terminator and rejected the newline.

## Evidence

- `src/convert/adapters/catia/Container.py` parses the OSMX symbol table.
- `src/convert/adapters/catia/Adapter.py` exposes the symbol table and principal planes.
- `CATObjectModelerBase.dll` SHA-256 `a522a0a040c74fc8f53aea707785e0d00e836d9eb8a113a25349fbd985905980`.
- `CATOmbPrivateSavePersistServices::StreamDocumentToPath` at `0x180119290`.
- `CATOmbPrivateLoadPersistServices::UnstreamDocument` at `0x180115620`.

## Open work

1. Locate the feature-record stream and its class table.
2. Decode sketch entities and constraints.
3. Decode dimensions and relations.
4. Emit a live feature tree and measure a dimension edit in CATIA.
