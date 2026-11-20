# SOLIDWORKS 2026 standalone header extraction

Task `B03-SW2026-ARCHIVE-HEADERS` takes the 16 files in `Archive/Header`
from [PR #121's pinned aggregate](https://github.com/TryUniCAD/Kit/commit/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f).
Their direct archive dependencies are available from
[the wire primitive and object graph prerequisite](https://github.com/TryUniCAD/Kit/commit/4ffbe3b111633e9bdd635e1d47082ce0aeb3ce6b).
The source manifest SHA-256 is
`9e9490aa277964b77deac7071b85bcbc7ae3f5b71a71287fdbbb642695ad57cf`.
The manifest concatenates sorted repository-relative paths, each followed
by a NUL, the lowercase file SHA-256 and a newline.

## Scope

On SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`, each measured standalone
header stream has a fresh map at one and a `moHeader_c` root of schema
one. File handles, their shared names, revision lists and typed bounds
use the recovered owner fields. Input text frames retain their encoding.
The codec supports the ordinary version-19000 archive. A nonnull
configuration object, unsupported schema or trailing input fails.
[Recovered fields and owners](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/records/SharedSdkHeaderGraph2026.md)

The historical [standalone receipt](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/solidworks/measurements/2026/SharedSdkHeaderGraph01.json)
has SHA-256 `aa91e38b2a44c9a17ac8b1ad248ffffd9ec76c3542a2f4f57484ee76e9780f91`.
It recorded 31 exact streams, 17 `Header2` and 14
`Contents/Config-0-ModelHeader`, in seven assemblies, seven parts and
three drawings. It recorded zero native runs, held-out checks and output
documents. The source comparison retained 12 of the receipt's 15 named
file hashes. `HeaderFields.py`, `ReadHeaderWire.py` and `WriteHeaderWire.py`
later adopted shared scalar operations. The 17 document hashes were
absent from the tracked CAD files under `re/solidworks` at the aggregate
and prerequisite revisions.

## Process exit

The existing [L1 native part](../v2026/corpus/ladder/L1_boss.SLDPRT) has
SHA-256 `55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6`.
The [exact-build receipt](../measurements/2026/ReverificationCountOwners01.json)
records container format 4 and archive version 19000 for that identity.
The [standalone probe](../../tooling/sw2026/CheckStandaloneHeaders.py)
adapts the earlier
[header comparison command](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/tooling/sw2026/serial/CheckSdkHeaders.py).
It reads both named streams in a fresh process, requires each complete
typed graph to re-emit identical bytes and returns a JSON receipt with
the stream sizes and hashes. It verifies the source stays identical.
Remote CI will supply the new one-part, two-stream result.

Source comparison retained all 16 extracted paths and resolved 19 direct
dependencies from the prerequisite. Scoped Black, Ruff, Mypy, Pyright
and steering checks passed. The donor scan found no recorded payloads
across 3,199 production sources.

Separate work covers linked Config and Resolved streams, CMgr headers
and inline Definition headers. Native document construction and
application acceptance have their own evidence requirements.
