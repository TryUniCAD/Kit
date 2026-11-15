# SOLIDWORKS drawing dimension record layout

## Behavior

`convert.adapters.solidworks.drawing` does not yet decode drawing dimensions
into typed values. The `Contents/Definition` stream stores a dimension as
several sibling class declarations rather than one record.

The angular dimension is `sgAnglDim`, then `moAngleParameter_c`, then
`sgLineHandle`. The offset dimension is `sgSkOffsetDim`. The
`moAngleParameter_c` record has a stable 76-byte layout: class reference, name
string, value double, flag int32, unit int32, text string, two zero bytes,
measured double, three zero bytes, one byte, twenty zero bytes, count int32,
and eight trailing bytes.

## Usage

A caller that needs dimension data must keep the source container. The
`ReadDrawing` surface does not expose dimensions, and `WriteDrawing` does not
rewrite them.

## Limitations

- the `sgLineHandle` leader geometry is not decoded
- the `sgSkOffsetDim` payload is not decoded; it contains two `D1` records and
  a large binary payload
- the value and measured doubles are recovered but their exact semantics are
  not oracle-verified
- a from-scratch drawing still needs the dimension records

## Verification

The `moAngleParameter_c` layout was checked against `coincident.SLDDRW`,
`large.SLDDRW`, and `multisheet.SLDDRW` under
`re/solidworks/examples/Drawings`. The measured double is identical in all
three, and the class reference differs only between `0x8065` and `0x8051`.
