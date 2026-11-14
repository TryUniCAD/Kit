# The writer can emit its own root section

## Behaviour

A new document flag, `nx.author_sections`, makes the writer regenerate the root
object model section (section 3) from parameters and empty the feature record
(section 4) instead of carrying both from the source part.

The root middle is emitted by `convert.adapters.nx.RootSection.RootMiddle` from a
document counter and a seven byte anchor identity:

```text
0x00  seven flag bytes
0x08  u32 counter
0x0c  32 zero bytes
0x2c  u32 counter + 49
0x30  u32 counter + 76
0x34  u32 2   0x38  u32 1   0x3c  u32 3
0x40  03 01 <len+2> "NX 2506.9120 - External User Function" 00
      08 "SYSTEM" 00  41 00  03 05 01 00  04 05 02 00
      e0 6a f8 <7 byte identity>  fixed lanes  01 01
```

The section pointer is recomputed from the emitted middle, and the payload is
trimmed to the end of its last section body, because trailing bytes make NX
refuse the file.

`PatchAnchor` also replaces the seven byte identity that every section stores
after its `e0 6a f8` anchor marker, and the writer applies it to the expression
section. The identity may be the unset constant; NX refuses `00` and `01`
repeated seven times, so the constant is the portable choice.

## Usage

```python
from dataclasses import replace

Changed = replace(
    Document,
    metadata={**Document.metadata, "nx.author_sections": True},
)
WriteNx(Changed, "part-authored-sections.prt")
```

The write result reports `author_sections: true`.

## Verification

`dim40.prt` written through the adapter with the flag set, then opened in
NX 2506:

```text
auth_only.prt  unloaded 0  bodies 1  volume 23999.999999999996  area 5200.0

auth_60.prt    author sections plus nx.body_length 60
               unloaded 0  bodies 1  volume 36000.0  area 7200.0

s2a_const_box60.prt  sections 1, 2 and 3 all carry identity ffffffffffffff
                     unloaded 0  bodies 1  volume 36000.0  area 7199.999999999999
s2a_empty.prt        unloaded 0  bodies 0
s2a_dim40.prt        unloaded 0  bodies 1  volume 23999.999999999996  area 5200.0
```

Identity patched in place, with everything else untouched, shows the constant is
accepted and other values are not:

```text
identity ffffffffffffff   loads   bodies 1  volume 36000.0
identity 01010101010101   NX refuses the part
identity 00000000000000   NX refuses the part
```

The written payload shows the generated section reaching NX intact:

```text
sections 5, sizes [36694, 2807, 1820, 607, 4]
section 3  middle 176 bytes, counter 0x1e3, identity ffffffffffffff, pointer 0x253
section 4  b"OM\x01\x01"
```

`TestNxRoot` checks the middle layout and the counter guard, and `TestNxAuth`
checks that a payload without object model sections is refused.

## Limits

- Section 1 is regenerated only for a part without a body; a part with a body
  keeps its forty four object construction graph.
- Section 0 still comes from the source part. It carries the topology and object
  classes (129 to 154 classes, 63 to 79 references) and has no generator.
- The expression section keeps its object graph; only its anchor identity is
  generated. Replacing it with a part's body-less expression section makes NX
  refuse the part, because the sections reference each other by payload offset.
- The counter is taken from the source: `KRootCounter` is the value observed in
  every fixture. Deriving it from emitted objects is part of the remaining work.
