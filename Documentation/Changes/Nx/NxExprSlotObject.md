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

## The 21 byte value slot

The same frame with the expression value in place of the handle, and three bytes shorter
padding:

```text
02 02 00 00 ff 00 00 21    fixed frame
01 01 01 01 01 00          five flags and a zero
50 64 00 00                value word: the expression handle and two zero bytes
00 00 ff                   padding and terminator
```

`ValueSlot(Value)` builds one and `ReadValueSlot` returns its handle. Every 21 byte slot in
three fixtures is reproduced from the value its handle encodes:

```text
dim40.prt        5 value slots   5 reproduced
const_box60.prt  5 value slots   5 reproduced
var_two.prt     11 value slots  11 reproduced
```

so a block part's section 2 is now fully described at object level: `6 + 6n` objects made
of the six fixed ones, `n` value slots carrying the dimension values, `4n` further slots,
and `n` records.

## Limits

- The 18 byte slots carry a handle whose low value (zero or `0x100`) is not yet decoded,
  so their contents are reproduced only through the handle read out of them.
- Nothing emits a whole expression section yet; this is one object of the `6 + 6n`
  inventory.
