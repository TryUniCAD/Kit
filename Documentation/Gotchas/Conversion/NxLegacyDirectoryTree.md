# NX legacy part containers need a real directory tree

## Expectation

An OLE2 compound file stores its directory as a set of 128 byte entries linked by
left, right and child pointers. Any chain a reader can walk should be readable, so
building the entries in creation order and linking each one to the next as a
right sibling is enough, and `olefile` confirms it: every stream of every rebuilt
part reads back byte identical.

## Observed behavior

NX rejects those files. The same container with the same stream bytes opens or
fails depending only on how the directory entries are linked:

```text
wave_parent.prt, only UG_PART/UG_PART, three entries, linear chain    bodies 1 volume 1000000.0000000002
same payload plus part/attrs, five entries, linear chain              OPEN_FAILED
same payload plus part/attrs, five entries, balanced tree             bodies 1 volume 1000000.0000000002
all eight wave_parent streams, balanced tree                          bodies 1 volume 1000000.0000000002
```

so the failure is not the stream set, not the mini stream, and not the root CLSID:
a five entry directory linked as a chain is refused, and the identical five
entries linked as a balanced tree load with the correct geometry.

## Workaround

Build each storage's children as a binary tree: sort by name length and then by
uppercased name, take the middle element as the node, and recurse. All entries
stay black, which a perfectly balanced tree satisfies. `re/nx/tools/OleWrite.py`
does this and is the writer used for the legacy container.

## Evidence

```text
flange.prt       rebuilt with OleWrite    bodies 1 volume 75385.625261497
vise_screw.prt   rebuilt with OleWrite    bodies 1 volume 1.7805678853189086
wave_parent.prt  rebuilt with OleWrite    bodies 1 volume 1000000.0000000002
all three        streams round trip byte identical through olefile
```

The source volumes are identical, so the rebuild preserves the part and only the
container was rewritten.
