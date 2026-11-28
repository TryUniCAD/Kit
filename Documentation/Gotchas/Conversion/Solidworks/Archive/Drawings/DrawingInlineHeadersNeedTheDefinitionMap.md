# Inline drawing headers need the Definition map

## Expectation

The configuration model's direct header bindings can also serialize a drawing model header, or a standalone header writer can supply the inline bytes.

## Actual behavior

The drawing stores `moHeader_c` as an ordinary tagged object inside `Contents/Definition`. Its classes and child objects advance the same counter as the drawing model. Later model, unit-component and sheet references use that existing map. The ordinary configuration `Direct` action deliberately rejects this inline drawing path.

The canonical header codec also represents concrete object lists as tuples of actual nodes. Embedded model lists use the shared field executor's row mappings. These are two typed views of the same native count/object vocabulary. A second map or a copied header substream would lose their real aliases.

## Correct use

Replace the configuration-specific header-binding action at the drawing profile boundary with a tagged header node. Continue the active Definition map through the existing header codec and all later model fields. Preserve node identity when projecting a fresh generated graph into canonical header and body representations.

The complete SDK blank Definition codec checks this construction with exact whole-stream bytes, full SDK read/write, an independent complete read and the final map counter. It adds no public writer admission. See the [source ledger](../../../../../../re/solidworks/records/DrawingDefinitionWriter2026.md), [process evidence](../../../../../../re/solidworks/measurements/2026/SdkDrawingDefinition01.json) and [usage guide](../../../../../Reference/Research/Solidworks/DrawingDefinitionWriting.md).
