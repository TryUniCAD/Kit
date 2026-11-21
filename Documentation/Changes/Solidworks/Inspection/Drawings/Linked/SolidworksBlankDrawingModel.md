# Fresh SDK blank drawing model

The internal SDK now constructs a fresh blank drawing's owning model, styles, units, canonical views, folders, sheet/support graph and empty managers from explicit neutral inputs. All self, relation, active-sheet and manager links refer to the actual constructed owners. Persistent IDs follow registration lifetime and the source-defined tree order.

Use `DrawBuild` and `MakeDrawRoot` under `Drawing.Construction.Model`. The bounded profile requires archive 19000/SP05.2, one unformatted ANSI A landscape sheet, matched units, qualified styles, explicit creation time and an independent block UUID4. Unsupported settings reject. The common model-owner guard now admits concrete schema-one drawings for the source-proved self/relation helpers. Part-only system admission remains unchanged.

Four blank designs and two linked-front designs each pass two isolated processes with exact complete stream/map parity, SDK read/write and real child/owner checks. Eighteen rejected construction jobs and the original four-process part-root regression pass. All 34 processes retain zero runtime input reads. Steering, Black, Mypy, Pyright and the donor scan pass. UI/metadata composition remains in research; this change enables no public writer and claims no new vendor or held-out acceptance.

See the [usage guide](../../../../../Reference/Research/Solidworks/DrawingModelConstruction.md), [source ledger](../../../../../../re/solidworks/records/DrawingModelConstruction2026.md) and [process receipt](../../../../../../re/solidworks/measurements/2026/SdkDrawingModel01.json).
