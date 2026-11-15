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
| Reset to the record start when a bare `e3` is followed by a compact-int byte | `VisibGeom` completes (553 nodes), but `AllFeatur` stops at `0x698`/`0x8ee`; a normal struct begin followed by `0x00` is indistinguishable |
| Reset when the next type-0 field is defined later than the current offset | `AllFeatur` stops at `0x1d8`/`0x1da` (30 nodes); forward definitions are common, so the test fires inside ordinary records |

The baseline parser keeps `AllFeatur`, `FeatDefsDtm`, `NovisGeom`, `BasicData`, and
`SolidPrimdata` complete on both controls, so none of these rules is a safe default.

## Confirmation from the open-source parser

Cadmpeg's Rust codec settles the intent. In
`crates/cadmpeg-codec-creo/src/psb.rs`, `COMPOUND_CLOSE` is `0xe3` and `COMPOUND_OPEN` is `0xe2`.
In `crates/cadmpeg-codec-creo/src/feature/rows.rs`, `row_spans` treats a row as starting at offset
zero, at the section header, or at any offset whose preceding byte is `COMPOUND_CLOSE`:

```rust
let starts_at_row_boundary = offset == 0
    || section_header_end == Some(offset)
    || (offset > 0 && payload[offset - 1] == psb::token::COMPOUND_CLOSE);
```

It also finds `e3 f6` inside the first 16 bytes of a row, reads the compact schema class after it,
and requires `e1` before accepting the class. Rows are then span-partitioned and decoded
independently. There is no global advancing field index across rows.

So the format is record scoped: `e3` terminates a row, and a row is decoded from its own span.
Our parser's global index is the mismatch. A faithful rewrite must split into `e3`-bounded spans,
then decode each span with its own schema rather than inheriting the previous row's cursor.

## Anchor inventory

`re/creo/tools/TaggedStream.py --rows` implements the cadmpeg boundary rule: a candidate row starts
at offset 0 or immediately after `0xe3`, and carries `e3 f6 <compact-class> e1` within the first
16 bytes after its identifier.

Measured spans:

| Section | Spans found |
| --- | --- |
| empty `AllFeatur` | 2 (`id 3` root 923, `id 11` root 979) |
| ladder `AllFeatur` | 8 (`id 3` 923, `11` 979, `67` 923, `66` 949, `0` 923, `75` 923, `2` 917, `74` 917) |
| ladder `FeatDefs` | 0 |
| ladder `VisibGeom` | 0 |

The anchors confirm the model for `AllFeatur`, including class `949` and the extrude class `917`.
They also show its limit: the first rows of a section start at the schema record, not at an
identifier, so they are not discovered. `FeatDefs` and `VisibGeom` do not carry the
`e3 f6 <class> e1` anchor at all; their boundaries are bare `e3` plus a compact identifier
(`… 62 e3 57 22 4a …` in `VisibGeom`). A second, anchor-free splitter is required for those
sections.

## Anchor-free element spans

`--elements` adds that splitter for geometry arrays. An element boundary is a bare `e3` followed
by a compact identifier, one byte, and the element's `feat_id` byte (`0x4a` here):

```text
plane: e3 52 22 4a 01 00 57   id 82, geom_type 34, feat_id 74
curve: e3 4f 00 4a 01 f6      id 79, type 0, feat_id 74
```

Recovered spans match the array headers the section declares:

| Array | Header count | Recovered |
| --- | ---: | --- |
| `srf_array` | 6 | 5 spans + inline `geom_id 77` = 6 (`82, 87, 89, 91, 93`) |
| `crv_array` | 12 | 11 spans + inline `crv_id 78` = 12 (`79, 80, 81, 83, 84, 85, 86, 88, 90, 92, 94`) |
| `lo_array` | 6 | 5 spans + inline `lo_id 95` = 6 (`96, 97, 98, 99, 100`) |

Feeding those 21 boundaries to the parser as per-element schema resets makes `VisibGeom` reach
section end: 502 nodes, reader position `0xb53`, which equals the section length. The decoded ids
are coherent: six `geom_type` 34 planes, twelve `crv_id` values, six `lo_id` values.

`body_array` declares a single element, so its inline definition is already covered.

`FeatDefs` is not row-spanned this way at all. Its `e3` bytes are followed by `e0` or `f7`
(definition closures and references), not by a geometry identifier. So `FeatDefs` needs a
definition-tree parser, not a span splitter.

## Correct direction

`e3` needs level tracking with per-level schema extents: a level records its element start, the
index at which its schema ends, and whether it repeats as an array element. A close resumes at the
element start when the level repeats and at the next sibling field otherwise. The current flat
global-index model has no place to store that state, which is why every local rule regresses some
other section.

Until that rewrite lands, the flat parser is a research approximation and must not be used to claim
feature or geometry coverage.
