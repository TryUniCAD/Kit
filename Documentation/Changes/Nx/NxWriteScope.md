# The writer states that it needs a retained native document

## Behaviour

`WriteNx` now refuses a document without a native container with a message that says
what is and is not supported:

```text
NX writing requires a retained native NX document; authoring a part from a neutral
document is not supported
```

The adapter reference gained a "Write scope" section listing exactly what is still
taken from the source part, so the guide no longer reads as though a part can be
authored from neutral data.

## Why

The repository's adapter reference described the authored sections without saying how
far they reach, and that reads as an implication that a from-scratch part is close.
It is not: 122 of 214 root object records, the head record of a part with a body, and
every expression and construction section shape except the smallest two are still
carried. Measured over `const_box60.prt`, 41930 of 41932 payload bytes are identical to
the source.

The class table is no longer in that list. Its second per-class field was recorded here
as a document-tracking identifier that could not be derived. It is the parent ordinal:
`0` is the root and any other value is the one-based index of the parent class in the
same region. Measured on `empty.prt` (129 classes), `dim40.prt` (154) and
`wave_modern.prt` (160), every base is in range and every base names a class whose name
is a prefix of the child or shares its schema. The field differs between parts only
because the class set differs, and the 47 length changes are bases crossing the direct
to compact token boundary. The first field is the class's registration id plus one, a
class constant. Both fields are therefore derivable, and the class table is authorable
from format knowledge.

## Verification

```text
pyright, mypy, ruff and steering clean on src/convert/adapters/nx
writer fixtures unchanged: empty, multi, var_blank, const_box60 and dim40 still write
and load in NX 2506 (bodies 0/0/0/1/1)
```

## Limits

- This is a documentation and message change; it adds no capability.
- The from-scratch path remains unimplemented, and no donor-free part exists.
