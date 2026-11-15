# SOLIDWORKS drawing units and line style values

## Behavior

`convert.adapters.solidworks.drawing.DefinitionUnits` decodes the
`Contents/Definition` units blocks into typed values.
`convert.adapters.solidworks.drawing.DefinitionStyles` decodes the line style
block.

`UnitTableAt(DataValue)` reads a units block and returns a `UnitTable` with
`Entries` and `Tail`. Each `UnitEntry` carries `Type`, `Value`, and `Unit`.
`EncodeUnitTable(Table)` writes the block back.

`LineStyles(DataValue)` reads the `moLineStyle_c` block and returns a tuple of
`LineStyle` values. Each `LineStyle` carries `Name`, `Description`, `Values`,
and `ClassRef`. `EncodeStyles(Styles)` writes the block back.

`ReadDrawing` exposes the decoded values as `DrawingData.Units` and
`DrawingData.LineStyles`.

The units block is a four-byte entry count followed by 16-byte entries of
`Type` (int32), `Value` (double), and `Unit` (int32), then a preserved tail.

The line style block is a sequence of records. Each record is a name string, a
description string, a two-byte pattern count, that many doubles, a one-byte
terminator, and a two-byte class reference when the terminator is zero. The
last record uses terminator one and has no class reference.

## Usage

```python
from convert.adapters.solidworks.drawing import ReadDrawing

data = ReadDrawing("orient-front.SLDDRW")
print(data.Units[0].Entries[0].Value)
print(data.LineStyles[0].Name, data.LineStyles[0].Values)
```

## Limitations

- the units tail is preserved but not interpreted; it carries the paper width
  and other constants
- the line style class reference is preserved but not resolved to a class
- a from-scratch drawing still needs the units tail and class reference
  semantics

## Verification

`UnitTableAt` and `EncodeUnitTable` reproduce every units block, and
`LineStyles` and `EncodeStyles` reproduce the `moLineStyle_c` block, for all
twelve tracked drawings: `angled`, `coincident`, `large`, `minimal`,
`multisheet`, `orient-front`, `orient-iso`, `orient-right`, `orient-top`,
`projected`, `scale3`, and `standard`.

`TestUnits` reads `orient-front.SLDDRW` through `ReadDrawing` and checks the
length unit entries, the units tail length, the seven line styles, the
`CONTINUOUS` and `CHAIN_THICK` values, and the class reference presence.
