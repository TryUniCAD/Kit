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

- Sections 0, 1 and 2 still come from the source part. They carry the topology,
  construction and expression object graphs, which are model dependent: emptying
  a middle and keeping its class lanes makes NX refuse the part, and a 40 and a
  60 length box differ inside section 1.
- The counter is taken from the source: `KRootCounter` is the value observed in
  every fixture. Deriving it from emitted objects is part of the remaining work.
