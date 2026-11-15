# Creo requires the whole model section set

## Expectation

A PSB part is a container plus a directory. If the container and directory are
correct, a part should be constructible from the sections a caller provides, and
sections that only carry display data should be optional.

## Actual behaviour

Creo 2027.2 validates every model section. Removing one directory row, or
corrupting one section body, fails the load even when the container is a
byte-identical reconstruction of a vendor part.

Measured with `re/creo/tools/Subset.py`, which rebuilds a vendor container from
its own directory and rewrites every row, every `NEXT_TOC_ENTRY` link, and every
section offset. The no-op rebuild is byte-identical to the control (`81539`
bytes), so the container itself is not in question.

| Change to the vendor control | Creo result |
| --- | --- |
| none (byte-identical rebuild) | loads: `End`, `MT Part Solid` |
| drop `IndentTag`, `FeatRefData` (table 3) | loads: `End`, `MT Part Solid` |
| drop `Notes` (21-byte section) | `'dropn.prt' cannot be retrieved` |
| drop `PipeInfos` (43-byte section) | `'droppipe.prt' cannot be retrieved` |
| drop the 21 display/thumbnail/view sections | `'dropdisp.prt' cannot be retrieved` |
| drop `Notes`, keep its byte extent as filler, offsets unchanged | `'resnote.prt' cannot be retrieved` |
| keep every row, blank the bodies of 8 text/display sections | `Could not retrieve part` |

So the failure is not caused by offset drift: preserving every absolute offset
and removing only the `Notes` row still fails. It is not caused by a missing
family of display data either: a single small section is enough to fail.

Two conclusions follow.

1. The container and directory format is settled. A byte-identical no-op
   rebuild loads, and directory-row edits are legal.
2. The section **set** is load-bearing. A generative author cannot emit a
   subset of the 52 section extents; it must emit all of them with readable
   bodies.

The only rows proven optional are the two trailing `IndentTag` and
`FeatRefData` sections in the third table.

## Workaround

Emit every section. For a generative author that means the model payload
(`BasicData`, `MdlStatus`, `SolidPersistTable`, `FeatDefs`, `FeatDefsDtm`,
`DEPDB`-family, and the rest) must be authored, not skipped. There is no
"minimal part" shortcut.

Until then, treat any authored container that omits a section as non-loadable
regardless of how clean the header, directory, and remaining sections are.

## Evidence

- `re/creo/tools/Subset.py` — rebuild with drop, replace, blank, and
  keep-space modes.
- `Documentation/Changes/Creo/CreoGenerativeAuthor.md` — isolation matrix,
  including the authored-container and authored-geometry swaps.
