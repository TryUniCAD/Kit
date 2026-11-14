# The writer emits the construction section of a part without a body

## Behaviour

`convert.adapters.nx.Construction` builds the 356-byte construction section
middle (section 1) for a part that carries no body, from named fields: the names
lane, the eight `02` and nine `01` flag bytes, the `0x3d8` counter, sixty four
zero bytes, the three object offsets computed from the object sizes, the four
word order array, the version and `SYSTEM` anchor block, the head object, the
descriptor whose optional references are all absent, and the infrastructure
record with its two counts.

`ObjectCount` reads an object count from a section body, and the writer only
regenerates section 1 when that count is three, so a part with a body keeps its
construction graph untouched.

## Usage

```python
Changed = replace(
    Document, metadata={**Document.metadata, "nx.author_sections": True}
)
WriteNx(Changed, "part-authored.prt")
```

`nx.author_sections` now regenerates section 1 for a body-less part in addition
to the root section and the feature record.

## Verification

The generated middle reproduces two independent NX parts byte for byte:

```text
empty.prt  base 0x34c  len 356  identical True
multi.prt  base 0x34c  len 356  identical True
```

Writing through the adapter and opening in NX 2506:

```text
auth_empty.prt  unloaded 0  bodies 0
                section 1 objects 3  identity ffffffffffffff
empty.prt       section 1 objects 3  identity 3b17ffdb906210

auth_dim40.prt  unloaded 0  bodies 1  volume 23999.999999999996  area 5200.0
```

so the body-less part is written with a construction section whose saved pointer
we generated, and a part with a body still measures after its root section is
regenerated and its feature record emptied.

`TestNxConstr` checks the middle layout, the computed object table, the identity
guard, the record counts and the object count reader.

## Limits

- Only the three object shape is generated. A part with a body carries forty four
  objects, and the forty one construction objects are not emitted yet.
- Sections 0 and 2 still come from the source part, so no part is written without
  a source document yet.
