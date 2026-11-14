# The writer rebuilds the registry slot record

## Behaviour

The root object section carries one record that lists the occupied and empty registry
slots in hash order:

```text
02 02 41 00 36 41 04 01 01 11   then tokens
token  80 <slot>  occupied slot
token  ff         empty slot
```

`convert.adapters.nx.ObjectSection.ParseSlots` decodes the token list and
`SlotRecord` writes it back. `RewriteRecords` re-emits the record with the occupied
slots sorted ascending and the empty slots moved to the end.

## Verification

Round-trip identity on all fixtures that carry the record:

```text
part            slot records  round-trip identical
empty.prt                  1                    1
multi.prt                  1                    1
var_blank.prt              1                    1
var_x1.prt                 1                    1
var_x2.prt                 1                    1
```

Token order is free, which was measured before relying on it: reversing all sixteen
tokens of the record loads in NX 2506 for both `var_blank.prt` and `var_x1.prt`:

```text
sl_var_blank.prt   tokens 16  occupied 16  reversed 25 bytes  part units 1  bodies 0
sl_var_x1.prt      tokens 16  occupied 16  reversed 25 bytes  part units 1  bodies 0
```

Writing all five fixtures with `nx.author_sections` and opening them in NX 2506:

```text
slt_empty.prt bodies 0     slt_const_box60.prt bodies 1
slt_multi.prt bodies 0     slt_dim40.prt       bodies 1
slt_var_blank.prt bodies 0
```

together with the token and reference relabelling described in
[the record grammar change](NxObjectGrammar.md), so section 0 differs from the source in
260 bytes for a body-less part and 134 for `const_box60`.

`TestNxSlots` checks the frame, the token round trip, the empty-only case, that a
reordering keeps the length, and both guards.

## Limits

- The slot values are Kit-assigned labels derived from the source record's own token
  set; the writer sorts them rather than computing a hash order.
- This is one more generated record out of 214, so section 0 is still mostly carried
  and `Writer.py` still requires a retained native document.
