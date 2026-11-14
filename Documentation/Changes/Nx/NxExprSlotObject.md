# The expression property slot is emitted from its handle

## Behaviour

The 18 byte objects in an expression section are the property slots behind a block
dimension. `convert.adapters.nx.ExprSection.SlotObject(Handle)` builds one and
`ReadSlotHandle` reads its handle:

```text
02 02 00 00 ff 00 00 21    fixed frame
01 01 01 01 01 00          five flags and a zero
<handle, three bytes>      the value handle
ff                         terminator
```

## Verification

Every 18 byte slot in three fixtures is reproduced exactly from the handle read out of
it:

```text
dim40.prt        10 slots  10 reproduced
const_box60.prt  10 slots  10 reproduced
var_two.prt      19 slots  19 reproduced
```

Per byte mutation of one slot in `dim40.prt`'s section 2, each loaded in NX 2506:

```text
byte 4, 7, 8, 9, 10, 11, 12, 13, 14, 15 flipped   loads
byte 5 and 6 flipped                              OPEN_FAILED
```

so the frame, the two zeros after the `ff` and the terminator are structural, while the
five flags and the handle are free.

`TestNxSlotObject` checks the layout, the handle read, both handle guards and the short
object guard.

## Limits

- The 21 byte slots in the same section are not handled: `ReadSlotHandle` accepts only the
  18 byte form, so those five objects per block part are still source-carried.
- Nothing emits a whole expression section yet; this is one object of the `6 + 6n`
  inventory.
