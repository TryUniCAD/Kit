# SOLIDWORKS drawing definition sheet and view values

## Behavior

`convert.adapters.solidworks.drawing.DefinitionValues` decodes the
`Contents/Definition` sheet and view object blocks into typed values.

`SheetRecordAt(DataValue)` reads the `moDrSheet` value block and returns a
`SheetRecord` with `Name`, `Scale`, and `Count`. `EncodeSheet(Record)` writes
the block back.

`ViewBlock(DataValue)` reads the `moView_c` value block and returns ten
`ViewRecord` values plus the 23-byte tail. Each `ViewRecord` carries `Name`,
`Prefix`, `Origin`, `ScaleOne`, `Normal`, `GapOne`, `ScaleTwo`, `GapTwo`,
`Flag`, `Value`, `Zero`, `Index`, `GapThree`, `Reserved`, and `ClassRef`.
`EncodeViewBlock(Records, Tail)` writes the block back.

The sheet record is a class reference, a name string, a `-2.0` scale, the
marker `4`, a zero, an empty string, six zero bytes, and a two-byte count.

The view record is a name string followed by a 124-byte payload:

```
prefix      1 byte
origin      3 doubles
scale one   1 double
normal      3 doubles
gap one     2 bytes
scale two   1 double
gap two     3 bytes
flag        1 int32
value       1 double
zero        1 int32
index       1 byte
gap three   3 bytes
reserved    4 doubles
class ref   2 bytes
```

The view block holds ten slots. The first slot is `*Full Sheet`; the remaining
nine are `Unused`. The `Index` field runs from 0 to 9.

## Usage

```python
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.drawing.DefinitionObjects import ObjectBlocks
from convert.adapters.solidworks.drawing.DefinitionValues import (
    EncodeSheet,
    SheetRecordAt,
)

archive = SldprtArchive.open("standard.SLDDRW")
definition = archive.require("Contents/Definition")
block = ObjectBlocks(definition, "moDrSheet", "moRefPlane_c")[0]
record = SheetRecordAt(block.Values)
print(record.Name, record.Scale, record.Count)
assert EncodeSheet(record)[2:] == block.Values[2:]
```

## Limitations

- the sheet `Count` field is not yet tied to a document-level meaning; it is
  `4`, `7`, `6`, `5`, `5`, `4`, `5`, `4`, and `4` across the tracked drawings
- the view payload gaps and reserved doubles are preserved but not interpreted
- the units table and line style blocks are still raw bytes
- a from-scratch drawing still needs the units table and line style semantics

## Verification

`SheetRecordAt` and `EncodeSheet` reproduce the `moDrSheet` bytes, and
`ViewBlock` and `EncodeViewBlock` reproduce the `moView_c` bytes, for all ten
tracked drawings: `orient-front`, `orient-top`, `standard`, `angled`,
`minimal`, `projected`, `multisheet`, `large`, `coincident`, and `scale3`.

`TestValues` checks the sheet name, scale, and count, the ten view slots, the
`*Full Sheet` and `Unused` names, the 0 to 9 indices, and the byte-exact
round-trip for `angled`, `minimal`, and `standard`.
