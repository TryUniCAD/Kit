# Creo tagged-stream compound boundaries are context dependent

## Expectation

`e3` looked like a single structural token. Two readings were plausible:

- `e3` begins a compound body, and `f1`-`f4` close it;
- `e3` closes a compound body or terminates a row, as cadmpeg documents.

A record in `VisibGeom` should therefore be delimited by one consistent boundary rule.

## Actual behaviour

`VisibGeom` uses two different boundaries for elements of the same array.

The `srf_array` header is `f8 06 f7 03 fb`, six elements of class 3.
The first element defines the schema inline:

```text
e0 00 srf_array 00 f8 06 f7 03 fb e3
e0 01 geom_id 00 4d
...
e0 01 list_type 00 62
```

The second element is introduced by an explicit selection:

```text
f2 f7 03 e3 52 22 4a ...
```

The third element has no selection. At the byte where the flat field table would enter the next
type-0 sibling (`crv_array`, field 24), the stream contains a bare `e3` followed directly by the
next element's values:

```text
... 62 e3 57 22 4a 01 00 59 ...
```

`52 22 4a` decodes as `geom_id 82`, `geom_type 34`, `feat_id 74`; `57 22 4a` decodes the same way
for the next element. So the bare `e3` is an element boundary, not the start of `crv_array`.

The same byte appears as a compound opener after an explicit `f7` selection. Its meaning depends on
whether the preceding token selected an array class and on how far the flat field index has
advanced.

## Workarounds attempted and rejected

Each was measured against the retained controls. None was adopted.

| Rule | Result |
| --- | --- |
| Treat `e2` as an array row separator and continue the array | `AllFeatur` ladder stops at `0x1d66`, `FeatDefs` at `0x4ba`, `BasicData` at `0xc6` (6 nodes) |
| Treat every `e3` as a close with a level stack | `AllFeatur` stops at `0x688`/`0x7c5`, `FeatDefsDtm` ladder at `0x691`, `VisibGeom` at `0x23c`, `BasicData` at `0x53` |
| On a bare `e3` at a new type-0 sibling, reset to the enclosing array class | `AllFeatur` ladder stops at `0x100d`, `FeatDefs` at `0x7f5`, `VisibGeom` at `0x2f7` (97 nodes), `BasicData` empty at `0x1cfd` |

The baseline parser keeps `AllFeatur`, `FeatDefsDtm`, `NovisGeom`, `BasicData`, and
`SolidPrimdata` complete on both controls, so none of these rules is a safe default.

## Correct direction

`e3` needs level tracking with per-level schema extents: a level records its element start, the
index at which its schema ends, and whether it repeats as an array element. A close resumes at the
element start when the level repeats and at the next sibling field otherwise. The current flat
global-index model has no place to store that state, which is why every local rule regresses some
other section.

Until that rewrite lands, the flat parser is a research approximation and must not be used to claim
feature or geometry coverage.
