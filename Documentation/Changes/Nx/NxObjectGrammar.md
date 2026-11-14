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
- The ordinals and the paired ids do not have to be copied. Rewriting them across
  the whole family is accepted:

  ```text
  all 15 pair records with First and Second swapped        loads
  14 pair records with both ids incremented by one         loads
  all 77 attribute ordinals incremented by one             loads
  all 77 attribute ordinals set to the same value 0x40     loads
  ```

  so for these two families NX treats the values as labels and an emitter may assign
  its own. The `02 02 41 4d` family does not behave the same way: filling its id
  region with a constant is refused, so it still needs a decoded layout.

- The remaining 122 records across the other families are not decoded.
- Section 0 is still carried from the source, so no part is written without a source
  document.
