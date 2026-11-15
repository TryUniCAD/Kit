# SOLIDWORKS drawing dimension parameter records

## Behavior

`convert.adapters.solidworks.drawing` decodes the `moAngleParameter_c` record
from the `Contents/Definition` stream into a typed `DimensionParameter` value.
The `Contents/Definition` stream stores a dimension as several sibling class
declarations rather than one record.

The angular dimension is `sgAnglDim`, then `moAngleParameter_c`, then
`sgLineHandle`. The offset dimension is `sgSkOffsetDim`. The
`moAngleParameter_c` record has a stable 76-byte layout: class reference, name
string, value double, flag int32, unit int32, text string, two zero bytes,
measured double, three zero bytes, one byte, twenty zero bytes, count int32,
and eight trailing bytes.

`ReadDrawing(..., IncludeDimensions=True)` exposes the decoded records as
`DrawingData.DimensionParameters`. The default `None` means the caller did not
request dimensions. `DefinitionDimensions.ParameterAt` decodes one record and
`EncodeParameter` re-encodes it byte-exactly.

## Usage

```python
from convert.adapters.solidworks.drawing import ReadDrawing

drawing = ReadDrawing("coincident.SLDDRW", IncludeDimensions=True)
for parameter in drawing.DimensionParameters or ():
    print(parameter.NameValue, parameter.Value, parameter.Measured)
```

## Limitations

- the `sgLineHandle` leader geometry is not decoded
- the `sgSkOffsetDim` payload is not decoded; it contains two `D1` records and
  a large binary payload
- the value and measured doubles are recovered but their exact semantics are
  not oracle-verified
- `WriteDrawing` does not rewrite dimension records
- a from-scratch drawing still needs the dimension records

## Verification

The `moAngleParameter_c` layout was checked against `coincident.SLDDRW`,
`large.SLDDRW`, and `multisheet.SLDDRW` under
`re/solidworks/examples/Drawings`. The measured double is identical in all
three, and the class reference differs only between `0x8065` and `0x8051`.
`EncodeParameter` round-trips each record byte-exactly.
