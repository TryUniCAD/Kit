# The token family's numeric words are expression handles

## Behaviour

The `02 02 ?? 00 35 ?? c0 20 03 01 c0 41 04 00` records carry four byte numeric
words. They are the same sixteen bit expression handle the writer already emits for
expression values, padded with two zero bytes:

```text
50 79 00 00   handle 0x7950   value 100.0
50 69 00 00   handle 0x6950   value  50.0
50 54 00 00   handle 0x5450   value  20.0
50 34 00 00   handle 0x3450   value   5.0
50 74 00 00   handle 0x7450   value  80.0
```

`convert.adapters.nx.ObjectSection.ValueWord(Value)` builds such a word from the value,
and `ReadValueWord` returns the handle, so the family can be emitted from numbers rather
than copied once its other fields are derived.

## Verification

```text
ValueWord(100.0) == 50 79 00 00
ValueWord(50.0)  == 50 69 00 00
ValueWord(20.0)  == 50 54 00 00
ValueWord(5.0)   == 50 34 00 00
ValueWord(80.0)  == 50 74 00 00
```

Every one of those values was found by searching the encoder for the observed handle,
so the word is derived from the value rather than matched to a fixture.
`TestNxWord` checks the five words, the handle read and the encoder limit.

## Limits

- The helper only converts a value to a word. Which value each field should hold is not
  derived: the words differ per part, so they are model data (extents or display scale)
  rather than constants.
- Values below `0.75` still use the compact encoding the writer cannot emit.
- No writer pass yet uses `ValueWord`, so section 0's byte provenance is unchanged.
