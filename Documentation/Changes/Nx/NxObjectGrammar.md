# Two root object record families are decoded and re-emitted

## Behaviour

`convert.adapters.nx.ObjectSection` now has grammars for the two largest record
families in the root object section, so those records can be produced from fields
rather than copied:

```text
AttributeRecord(KeyText, ValueText, Ordinal, Marker)
  01 02 04 <len(key)+2> key 00  01 02 04 <len(value)+2> value 00  <ordinal> <marker>

PairRecord(First, Second)
  fixed 30 byte frame  <token First>  ff x 6  <token Second>  ff x 8
```

`ParseAttribute` and `ParsePair` read the same records back, and `RegToken` emits the
registry token encoding: values up to `0x7f` in one byte, larger values behind a
`0x80` prefix.

## Verification

Every record of both families round-trips byte for byte in all three body-less
fixtures:

```text
part            attributes  pairs  decoded of 214
empty.prt        77 / 77    15 / 15          92
multi.prt        77 / 77    15 / 15          92
var_blank.prt    77 / 77    15 / 15          92
```

So 92 of the 214 records, 43 percent, can now be re-emitted from their fields.

`TestNxGrammar` checks both grammars, the token encoding, the range guards and the
malformed-record rejections.

## Limits

- The remaining 122 records across the other families (for example `02 02 41 4d`
  and `02 02 41 00`) are not decoded.
- The ordinals and the paired ids are still taken from the source, because the
  allocator that assigns them is not derived; the grammars make the records
  re-emittable, not yet derivable.
- Section 0 is still carried from the source, so no part is written without a source
  document.
