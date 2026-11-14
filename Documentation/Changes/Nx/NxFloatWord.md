# Float words are single precision values in a shifted double

## Behaviour

The `30 ??` and `2f ??` words in the `02 02 ?? 00 35 ??` records are doubles whose top
byte has `0x10` subtracted, holding a value rounded to single precision:

```text
30 76 80 00 00 00 00 00   0x4076 8000 ..   360.0
2f c9 99 99 a0 00 00 00   0x3fc9 9999 a0   0.20000000298023224
2f e8                    0x3fe8         0.75, trailing zeros dropped
```

`ObjectSection.FloatWord(Value)` builds one and `ReadFloatWord(Word)` reads one back,
padding a short word with zero bytes.

## Verification

```text
FloatWord(360.0) == 30 76 80 00 00 00 00 00
FloatWord(0.2)   == 2f c9 99 99 a0 00 00 00
ReadFloatWord(30 76 80 00 00 00 00 00) == 360.0
ReadFloatWord(2f e8)                  == 0.75
```

Every float word found in the `35` family of `empty.prt`, `const_box60.prt` and
`dim40.prt` is reproduced exactly by `FloatWord(ReadFloatWord(word))`: six words per
part, zero mismatches.

`TestNxFloat` checks both conversions, the short word, and the empty-word guard.

## Limits

- The helper converts values; which value each field holds is model data and is not
  derived, so no writer pass uses it yet and section 0's provenance is unchanged.
- Short words are padded with zeros on read, which matches every short word measured so
  far; a short word with meaningful trailing bytes would not round-trip.
