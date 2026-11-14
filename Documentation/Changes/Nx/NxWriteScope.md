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
It is not: 122 of 214 root object records, all 129 per-document class identifiers, the
head record of a part with a body, and every expression and construction section shape
except the smallest two are still carried. Measured over `const_box60.prt`, 41930 of
41932 payload bytes are identical to the source.

The per-document class identifiers were tested and are not derivable from the class
names: 128 of 129 differ between `empty.prt` and `dim40.prt`, no constant offset
explains them, and 47 entries change length, so the entry packs two fields one of which
tracks the document.

## Verification

```text
pyright, mypy, ruff and steering clean on src/convert/adapters/nx
writer fixtures unchanged: empty, multi, var_blank, const_box60 and dim40 still write
and load in NX 2506 (bodies 0/0/0/1/1)
```

## Limits

- This is a documentation and message change; it adds no capability.
- The from-scratch path remains unimplemented, and no donor-free part exists.
