# The writer rebuilds the lane records and relabels their slots

## Behaviour

Thirty of the 214 root object records share one grammar, which
`convert.adapters.nx.ObjectSection.LaneParts` decodes and `LaneRecord` writes back:

```text
<n> 11 <n> 01 11          count repeated, framing the lane
<flags>                   n dependent run of 01 and small counts
02 e0 <4 byte mask> 01 11 marker and mask
<tokens>                  slot list
```

A token is one of

```text
ff              empty slot
80 <label>      occupied slot, two byte form
10..7f          occupied slot, one byte form
03 <len> <text> labelled text token, len counts the terminating null
```

`RelabelLanes` assigns every distinct occupied token a new label counting from `0x10`,
preserving each token's width, and rewrites all 30 records so shared labels stay shared.
`nx.author_sections` runs it after the attribute, pair, slot and reference passes.

## Verification

Round-trip identity on every fixture:

```text
part             lane records  round-trip identical
empty.prt                  30                   30
multi.prt                  30                   30
var_blank.prt              30                   30
const_box60.prt            30                   30
dim40.prt                  30                   30
```

Writing all five through the adapter and opening them in NX 2506:

```text
lan_empty.prt        bodies 0   exprs 0      lan_const_box60.prt  bodies 1  exprs 3
lan_multi.prt        bodies 0   exprs 8      lan_dim40.prt        bodies 1  exprs 3
lan_var_blank.prt    bodies 0   exprs 0
```

Section 0 now differs from the source in 340 bytes for a body-less part and 214 for
`const_box60`, against 260 and 134 before this change; payload identity is 99.00 and
99.46 percent.

`TestNxLane` checks the count, the flag run, the mask, the slot list, a text token, the
malformed-record guards and the short-mask guard.

## Limits

- The flag run and the mask are parsed and preserved, not derived. They encode the
  record's nesting and are carried from the source.
- 30 of 214 records is one more family; section 0 is still mostly carried and
  `Writer.py` still requires a retained native document.
