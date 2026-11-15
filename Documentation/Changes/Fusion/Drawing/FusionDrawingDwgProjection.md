# Drawing database is projected, not retained

## Problem

`ReadDrawing` kept the embedded DWG as bytes in `DrawingDatabase.Content`, and `EmitDrawing` wrote
those bytes back. A drawing therefore round-tripped by replay, not by conversion, and the acceptance
record could not claim C3 for drawings.

## Change

`DrawingDatabase` now holds the typed model:

| Before                        | After                                  |
| ----------------------------- | -------------------------------------- |
| `DrawingDatabase(FileName, Content: bytes)` | `DrawingDatabase(FileName, Model: DwgFile)` |
| `ReadDrawing` stored the payload | `ReadDrawing` calls `ReadDwgFile` on the payload |
| `EmitDrawing` wrote `Content` | `EmitDrawing` calls `EmitDwgFile` on `Model` |
| `Content` was a field         | `Content` is a property that emits the model |

`CheckJoins` now checks the model type instead of the byte type.

A caller that edits the drawing edits `Database.Model`, and the emitted drawing is rebuilt from that
model. Nothing carries a second copy of the DWG bytes.

## Verification

| Check                                                        | Result   |
| ------------------------------------------------------------ | -------- |
| Fusion-saved F2D read and re-emitted byte-exactly through the typed model | 247 of 248 |
| Fusion-saved DWG read and re-emitted byte-exactly             | 60 of 60 |
| Typed objects projected from one drawing                      | 1993     |

The one F2D that does not round-trip is `Z1EmptyDwg`, a research control whose embedded database is
empty. `ReadDwgFile` rejects it with `DWG file header lies outside the available data`, so the reader
now refuses an invalid database instead of passing its bytes through.

A native run edits the `LAYOUT` object inside `Database.Model` from A3 to A1 and emits the drawing
from the model. Fusion 2706.1.17 opened it in 4.7 s and reported `841.0 x 594.0` with views
`[5, 4, 4]` and one dimension, so the projection and the rebuild are lossless for that edit.

## Authoring gate

`EmitDrawing` now refuses a drawing whose database carries Kit's own product entry in its `AppInfo`.
That entry is what `AuthorDwg` writes, and a database Kit authored cannot be made loadable because the
header tail is a placeholder.

```
EmitDrawing(BuildDrawing(MakeSpec(), authored_database))
ValueError: Authored drawing databases cannot be made loadable, so the drawing is refused
```

The gate is at emission, so every path that writes a drawing is covered, including a bundle.
`BuildBundle` still builds the model, so a caller can inspect an authored drawing; it cannot emit one.

The match is the product entry, `name ="Kit"`, not any text that contains `Kit`, so a Fusion database
whose metadata mentions Kit elsewhere still emits. A database with no application entry at all is
refused too, because every Fusion save carries one.

A caller who rewrites the product entry to another name gets past the gate. That is a deliberate
forgery of the metadata, not a path the authoring code takes, and the tail is still a placeholder.

| Corpus                                   | Emitted | Refused |
| ---------------------------------------- | ------- | ------- |
| Fusion-saved drawings, product `Fusion Drawings` | 192 | 0 |
| Research variants carrying Kit's product entry | 0 | 56 |

## Behavior

| Case                                  | Before                    | After                          |
| ------------------------------------- | ------------------------- | ------------------------------ |
| Read a Fusion drawing                 | DWG kept as bytes         | DWG projected to 1993 objects  |
| Re-emit an unedited drawing           | bytes copied              | model rebuilt, byte-identical  |
| Edit a DWG object and re-emit         | not possible at this level | model edited, drawing rebuilt |
| Read a drawing with an empty database | accepted                  | rejected                       |
| Package an authored drawing as a bundle | emitted                 | refused                        |

## Limits

The projection is the DWG model that `ReadDwgFile` already produced. It is not a neutral interchange
model, so a drawing still carries DWG-specific objects rather than a format-independent feature tree.

The one rejected file is a research control, not a Fusion save. A Fusion save with a database that
`ReadDwgFile` cannot parse would now fail to read, where before it would have passed through.
