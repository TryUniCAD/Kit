# External corroboration of the Fusion data model

The [Fusion data model](../../Reference/Research/FusionDataModel.md) now explains in detail why the format was difficult to reverse engineer. It also records the T-spline, round body and external evidence that supports the model. This entry adds no production code.

## Data model additions

| Section | Content |
| --- | --- |
| Why the format is difficult | Eighteen difficulties in seven layers: container, object graph, identity, geometry, evaluation state, display members and tooling |
| Method that resolved the format | Corpus inventory, binary symbols, external inventories, controlled variants, byte-exact re-emission, independent authoring and native acceptance |
| T-spline control cages and orientation | TSM declaration profile, record fields, extension namespaces, orientation roots and acceptance values |
| Authored round bodies and trimmed round histories | Sphere and torus field order, loop-free closed faces and acceptance values |
| External corroboration | `reverse-engineer` binary inventories, REA evidence and the cadmpeg comparison |

The [acceptance matrix](../../Reference/Research/FusionAcceptanceEvidence.md) adds T-spline and round body rows. It also records the remote result for revision `55aeed29b` and the repairs for its failures.

## Binary inventories

The npm package [`reverse-engineer`](https://www.npmjs.com/package/reverse-engineer) `0.1.0-alpha.1` ran through `npx` with a pinned version. It is MIT licensed. It reads Mach-O headers, export tries and string tables, and it does not execute the target. The package was unpacked and its manifest and bundle were read before first use.

| Fusion 2706.1.17 library | SHA-256 | Corroborated model element |
| --- | --- | --- |
| `libtsplines.14.dylib` | `820d4a39767b6c92c7074cead1d2961a043eaa257e9fc2db2fd0ce5e832af9fc` | `Face_originLink`, `Edge_originLink`, `Vert_orientLink` and the TSM keyword table |
| `NsDataModel10.dylib` | `47ddbeca2f5c97c96e44989523ff969baa5d0d11b59d8ca35b934d48e2657af5` | Paired bulk and metadata streams and the XML persistence keys |
| `libASMkern232.dylib` | `816da13b49156e1750b9d3af17164f583920731b3374a900d98778b16773bc86` | `HISTORY_STREAM`, `DELTA_STATE` and `BULLETIN_BOARD` journal structure |

The [inventory folder](../../../re/Fusion/External/ReverseEngineer/README.md) records every command. Local application and cache paths are replaced with placeholders. The inventories give names and library ownership. They do not give field widths.

## cadmpeg comparison

The [comparison](../../../re/Fusion/External/CadmpegComparison.md) reads cadmpeg at commit `de2726870ff728352163f601ab4e60bbd54fbade`. cadmpeg code is Apache-2.0 and its specifications are CC-BY-4.0. Kit copies no cadmpeg code, and the local clone is ignored by Git.

The comparison finds that cadmpeg covers more feature families and package forms. Kit names more fields from native classes and has Fusion acceptance of independently written output. Kit evidence resolves cadmpeg items HS-01 and DR-80 and partly resolves four more. It contradicts eight cadmpeg statements, including four TSM field meanings.

## Verification

The orientation exports in the inventory agree with the native root-variant captures. Each cadmpeg statement in the contradiction table was checked against the cadmpeg specification text at the pinned commit. No local tests ran. This entry changes documentation and research files only.
