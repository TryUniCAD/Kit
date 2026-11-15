# The `30 04 04 fd ff` records carry a stream length, not a fixed preamble

## Expectation

Every CATPart starts its `MainDataStream` with three `30 04 04 fd ff` records, so a writer can emit
the same three records as a constant preamble.

## Actual behavior

The records are not constant. Two of the three share one layout:

```
r0  at offset 54    span 47   marker | 00 00 00 01 | 00 | five f32 | kind u32 | 13-byte tail
r1  at offset 101   span 52   r0 followed by 95 ff <u16> 00 00 00
r2  at offset 153   span varies, different shape (ff ff 02 00 01 ...)
```

`kind` is `3` for `r0` and `19` for `r1` in every one of the 27 corpus parts, and the 13-byte tail is
the same `ff 03 01 00 00 ff 01 00 00 00 00 62 00`. The five floats vary per part and carry no metric
that could be derived from the model:

| part | five floats | bbox extent | extent/2 diagonal |
| --- | --- | --- | --- |
| `Reservoir` | `47.2094, 0.0, -6.75, 0.0448, 30.0` | `52.721, 40.976, 60.0` | `44.885` |
| `4784` | `71.415, 0.0, 0.688, 0.0, 25.3949` | `102.87, 54.61, 78.74` | `70.293` |
| `Copper_Washer` | `11.4708, 0.0, 0.5, 0.0, 0.0` | `1.0, 15.608, 13.0` | `10.169` |
| `Nut_M6` | `9.2931, 0.0, 0.0, 3.9695, 0.0` | `10.002, 8.0, 11.548` | `8.623` |

only the `Reservoir` and `Washer_8` fifth floats happen to equal the z half-extent, so there is no
consistent relation.

The `u16` inside `r1` is derivable: it equals `(MainDataStream length - 199) mod 65536` for 26 of the
27 corpus parts. `Pedal_Body` is the exception, off by `340` (`60606` where the rule predicts
`60946`). Decode it with `re/catia/tooling/FdRecords.py`.

## Workaround

Do not emit the records as a constant, and do not invent the floats. `FdRecords.py` dumps each part's
three records with their spans, kinds, floats, and the length check, so a vendor-saved pair can be
compared against the writer's output once a licensed CATIA is available. Until then the writer omits
these records, which is why its `MainDataStream` is not structurally identical to a vendor stream.

## Evidence

- `re/catia/tooling/FdRecords.py`
- `src/convert/adapters/catia/NativeWriter.py`
- `Documentation/Changes/Catia/CatiaNativeBrep.md`
