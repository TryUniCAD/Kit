# Object model section bodies can be replaced at a new length

## Behaviour

`convert.adapters.nx.PayloadBuild.ResizePayload` rewrites a `UG_PART` payload
with replacement object-model section bodies and recomputes the segment index. It
accepts one body per section, preserves each section's original prefix width
(twelve bytes for the plain form, sixteen for the toolkit magic form), refreshes
the big-endian size, and remaps every index value that names a moved boundary,
including the payload end markers.

The module refuses a legacy payload, a body count that does not match the
section count, or a section whose prefix is not one of the two known widths.

## Usage

```python
from convert.adapters.nx.PayloadBuild import ResizePayload

Bodies = [
    Payload[Section.body_offset : Section.body_offset + Section.size]
    for Section in ReadPayload(Payload).sections
]
Bodies[Index] = AuthoredBody
Written = ResizePayload(Payload, Bodies)
```

## Verification

Replacing every section with its own body reproduces the payload byte for byte,
which proves the layout, prefix handling and index remapping are exact:

```text
dim40.prt        sections 5  identical True  48571 bytes
const_box60.prt  sections 5  identical True  46498 bytes
empty.prt        sections 4  identical True  36361 bytes
empty_expr.prt   sections 4  identical True  36682 bytes
```

A real length change also holds against NX 2506: a generated expression section
body (965 bytes replaced by 1263) spliced into `empty.prt` and resealed loads
with

```text
STATUS 0
EXPRESSION kit_len 12.5
```

`tests/convert/nx/NxTests.py::TestNxResize` checks the same contract on a
synthetic payload: identity when nothing changes, a shifted second section and a
rewritten index row when the first body grows, and refusal when the body count
disagrees.

## Limits

- Section bodies are not relocatable between different parts. Replacing
  `empty.prt`'s bodies with `empty_expr.prt`'s keeps the byte count but produces a
  part NX refuses to open, because a body stores payload-absolute references that
  only the generated body for that payload can carry. Authoring therefore means
  generating bodies for the target payload, not copying them from another file.
- The container, feature records and body object records still come from a
  retained native part; this change makes the payload half writable from
  parameters, it does not make a neutral document writable yet.
