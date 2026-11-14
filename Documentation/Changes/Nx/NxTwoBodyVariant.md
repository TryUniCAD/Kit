# A six expression two body part writes and loads

## Behaviour

No new code path. This records a verification the writer had not been run through: a part
with six block expressions and two bodies (`var_two.prt`) is read, written with
`nx.author_sections`, and opened in NX 2506 with both bodies intact.

Earlier this fixture could not be written because a strict read refuses it — it carries two
Parasolid streams and the reader projects only the first, reporting
`nx.multiple_parasolid_streams` as a warning in non-strict mode. The write path does not
rebuild geometry, so the part round-trips with its two bodies regardless.

## Verification

```text
var_two.prt      bodies 2   volume 48000.0
two_written.prt  bodies 2   volume 48000.0
```

Byte provenance of the written payload:

```text
section 0  37896 bytes  differing 346
section 1   3860 bytes  differing   0
section 2   2422 bytes  differing   6
section 3    609 bytes  differing   7
section 4      4 bytes  generated
payload    44791 bytes, identical 99.20%
```

Section 2 here carries 42 objects, the `6 + 6n` shape for `n = 6`, and is still copied
because the slot placement that a full emission needs is name-hash derived.

## Limits

- This is a verification entry, not a capability change.
- `ReadNx` in strict mode still refuses a part with several Parasolid streams; the writer
  works because it reuses the retained payload.
