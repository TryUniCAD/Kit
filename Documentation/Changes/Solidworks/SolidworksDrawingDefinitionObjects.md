# SOLIDWORKS drawing definition object blocks

## Behavior

`convert.adapters.solidworks.drawing.DefinitionObjects` parses and serializes
the `Contents/Definition` object groups that follow the feature tree and model
reference:

- `moUnitsTable_c` through `moUnitComponent_c`
- `moDrSheet` through `moRefPlane_c`
- `moView_c` through `moSketchBlockMgr_c`
- `moLineStyle_c` through `uiLineFontMgr_c`

`ObjectBlocks(DataValue, StartClass, EndClass)` returns one `ObjectBlock` per
class declaration, with the class name and its raw value bytes.
`EncodeBlocks(Blocks)` writes the declarations and values back.

The value block has no length prefix, so the parser finds the next declaration
by its `ffff0100` marker and a printable class name. The group has no length
prefix either, so the caller supplies the end class.

## Usage

```python
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.drawing.DefinitionObjects import (
    EncodeBlocks,
    ObjectBlocks,
)

archive = SldprtArchive.open("standard.SLDDRW")
definition = archive.require("Contents/Definition")
blocks = ObjectBlocks(definition, "moUnitsTable_c", "moUnitComponent_c")
assert EncodeBlocks(blocks) == definition[
    definition.find(b"moUnitsTable_c") - 6 :
][: len(EncodeBlocks(blocks))]
```

## Limitations

- the object values are raw bytes; the units, sheet, view, and line style
  semantics are not decoded
- the units table is 1,510 bytes and constant across the tracked drawings except
  for one class reference index
- a from-scratch drawing still needs the value semantics for these objects

## Verification

`ObjectBlocks` and `EncodeBlocks` reproduce the source bytes for the units
table, sheet, view, and line style groups in all ten tracked drawings:
`orient-front`, `orient-top`, `standard`, `angled`, `minimal`, `projected`,
`multisheet`, `large`, `coincident`, and `scale3`.

The units table holds 18 records. The sheet, view, and line style groups each
hold one record in these fixtures.
