# The single block construction graph is emitted with a generated identity

## Behaviour

`convert.adapters.nx.BlockSection.BlockMiddle` emits the 1247-byte construction
graph of a part with one block feature: forty four objects, their link chain, the
group byte and the document anchor, with the seven byte identity supplied by the
caller.

`nx.author_sections` now also patches section 1 for a part whose construction
section carries forty four objects, so the identity in the written part is the one
Kit generates rather than the source document's. Parts with any other object count
are left untouched.

## Verification

The generator reproduces the source middle exactly when given its identity, and
differs only inside the anchor when given another:

```text
BlockMiddle(dim40 identity)  len 1247  identical True
BlockMiddle()                identity ffffffffffffff
prefix and suffix identical for any identity
```

Writing through the adapter and opening in NX 2506:

```text
blk_const_box60.prt  authored 60 x 30 x 20 geometry
                     section 1 objects 44  identity ffffffffffffff  section 4 size 4
                     unloaded 0  bodies 1  volume 36000.0  area 7199.999999999999

blk_dim40.prt        unloaded 0  bodies 1  volume 23999.999999999996  area 5200.0
```

`TestNxBlock` checks the middle length, the anchor position, the generated
identity and the short-identity guard.

## Limits

- The object graph bytes are the canonical single block encoding. `dim40`,
  `dim50` and `dim60` share them; a block made through a different creation path
  differs in session ids, and a cylinder or sphere has a different graph
  altogether (18 and 9 objects).
- The parameter record still carries canonical internal ids rather than ids
  allocated for the written document.
- Sections 0 and 2 still come from the source part, so this does not yet make a
  part writable from a neutral document.
