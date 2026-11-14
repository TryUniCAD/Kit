# Named view records are decoded and can be re-labelled

## Behaviour

`convert.adapters.nx.ObjectSection.ViewName` reads the name a named view record
carries. It matches a whitelist of view heads (`41 41`, `41 4b`, `41 06`, `42 0c`,
`3a 0c`, `ff 0c`, `42 06`, `3a 06`, `ff 06`) because a part with a body stores its views
under different class bytes than a part without one, and `RenameView` rewrites it in place:

```text
02 02 41 41 ...  03 <len> <text> 00 ...   head, name token, matrix and extents
```

`<len>` counts the text plus the terminating null, so a name has to keep its byte
length; a different length is refused by the writer and by NX.

## Verification

Ten named views are read from each body-less fixture and round-trip byte for byte:

```text
empty.prt       Front Right Back Bottom Left L1 L2 L3 L4 !DRAWING   10 of 10
multi.prt       same set                                            10 of 10
var_blank.prt   same set                                            10 of 10
```

Field mutation of a 184 byte view record, each loaded in NX 2506:

```text
name text changed, same length        loads
name length prefix raised by one      OPEN_FAILED
one matrix byte flipped               loads
one mask byte flipped                 loads
one tail byte flipped                 loads
```

So the name is a field the writer may set, the length prefix is structural, and the
matrix and extents after it are data that NX does not revalidate on load.

`TestNxView` checks the parse, the identity rename, an in-place rename, the
length guard and the missing-name guard.

## Where the extents come from

The Front view of three body-less parts decodes to identical values:

```text
empty.prt  multi.prt  var_blank.prt
-508.0  508.0  -2639.645431  2639.645431  -2688.083332  2688.083332  0.755929  0.013963
```

and a part with a body decodes to the same numbers, though its views sit under different
class bytes:

```text
dim40.prt      Top    -508.0  508.0  -508.0  508.0  -2639.6454  2639.6454
dim40.prt      Front  -508.0  508.0  -2639.6454  2639.6454  -2688.0833  2688.0833
const_box60    same, view for view
```

So the extents do **not** track the body: a 40 by 30 by 20 solid and an empty part store
identical view extents. They are fixed defaults, which means they can be emitted as
constants instead of measured — the opposite of what the bounding box hypothesis
predicted. The earlier candidate that looked body shaped (`0.08 0.06 0.04` in a 133 byte
record) turned out to be a parts list, not a view.

## Limits

- Only the name is decoded. The matrix, extents and masks that follow it are not
  derived, so the record is not yet emitted from fields.
- Body parts carry the same views with a different record head, which this change does
  not match; the decoder returns nothing for them.
- Section 0 is still mostly carried and `Writer.py` still requires a retained native
  document.
