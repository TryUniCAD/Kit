# Generated sections read the document counter from the source

## Behaviour

Both generated section middles used to carry a constant document counter: `0x3d8`
in the construction section and `0x1e3` in the root section. They now take it from
the section being replaced.

- `Construction.ConstructMiddle(Base, Identity, Counter)` emits the counter at
  middle offset `0x2c` and derives the two values after it
- `RootSection` reads the counter at middle offset `0x08` of the source root middle
  and passes it to `RootMiddle`
- `RootMiddle` is now reproduced exactly for every fixture when given its own
  counter and identity

## Verification

```text
part             section 1 counter  RootMiddle identical
empty.prt                  0x3d8    True
multi.prt                  0x3d8    True
var_blank.prt              0x3dc    True
const_box60.prt            0x3d8    True
dim40.prt                  0x3d8    True

part             section 3 counter  RootMiddle identical
empty.prt                  0x1e3    True
multi.prt                  0x1e3    True
var_blank.prt              0x1e7    True
const_box60.prt            0x1e3    True
dim40.prt                  0x1e3    True
```

A part whose counter differs, `var_blank.prt`, was the case that exposed both bugs:
writing it with `nx.author_sections` produced a file NX refused until each counter
was read from the source. After the fix all five parts load:

```text
objB_empty.prt        bodies 0
objB_multi.prt        bodies 0
objB_var_blank.prt    bodies 0
objB_const_box60.prt  bodies 1  exprs 3
objB_dim40.prt        bodies 1  exprs 3
```

`TestNxRoot` and `TestNxConstr` now assert that a non default counter changes the
emitted fields.

## Limits

- The counter is read from the source rather than derived from the objects a writer
  emits, so a part still needs a source document.
