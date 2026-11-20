# SOLIDWORKS 2026 standalone header extraction

Task `B03-SW2026-ARCHIVE-HEADERS` takes the 16 files in `Archive/Header`
from [PR #121's pinned aggregate](https://github.com/TryUniCAD/Kit/commit/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f).
Their direct archive dependencies are available from
[the wire primitive and object graph prerequisite](https://github.com/TryUniCAD/Kit/commit/4ffbe3b111633e9bdd635e1d47082ce0aeb3ce6b).
The initial 16-file source manifest SHA-256 was
`9e9490aa277964b77deac7071b85bcbc7ae3f5b71a71287fdbbb642695ad57cf`.
The review revision retains 15 original files. `WriteHeaderBody.py`
dispatches the class bodies, `WriteHeaderFile.py` owns file bodies and
`WriteHeaderList.py` owns ordered object and text lists. The revised
18-file manifest SHA-256 is
`ac1a30b2f4dde04a61fbca5c64a6c5d60dd7388922e2d7139e6e8c1ede1c4f53`.
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
The independent [ConcaveOwned part](../v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT)
is an existing generated and native-observed control from PR #172. Its
[fixture receipt](../measurements/2026/LocalImportReadbackFixtures01.json)
pins source SHA-256 `fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33`.
A container-only inventory found format 4, archive version 19000 and
the following logical stream identities.

| Control | Stream | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| L1 | `Header2` | 2315 | `9e3d68bd031e4797a2f05504cf8962e5e3a337d2816ec963194165371d5b4659` |
| L1 | `Contents/Config-0-ModelHeader` | 2315 | `9e3d68bd031e4797a2f05504cf8962e5e3a337d2816ec963194165371d5b4659` |
| ConcaveOwned | `Header2` | 789 | `0d8551d418c050d4f3d737edac10225af00146037f6eefa2b60511b8db4ad53d` |
| ConcaveOwned | `Contents/Config-0-ModelHeader` | 789 | `f4cce850be7777c5f6aad10d0bc46bda2e60448fac1ca4cde309df56063516aa` |

The [standalone probe](../../tooling/sw2026/CheckStandaloneHeaders.py)
adapts the earlier
[header comparison command](https://github.com/TryUniCAD/Kit/blob/a0c36cb8f525b8d5283b1182dbeb2ea84ffc820f/re/tooling/sw2026/serial/CheckSdkHeaders.py).
Each control runs in a fresh process. The probe requires complete
typed reads, identical re-emission and an immutable input. The tests
pin each reported role digest and require the ConcaveOwned pair to
differ. The two-part, four-stream replay awaits remote CI.
[Identical header roles](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/StandaloneHeaderRolesCanMatch.md)

Source comparison resolved the same 19 prerequisite dependencies.
AST comparison confirmed the moved serializer bodies and dispatch
preserve their operations. Scoped Black, Ruff, Mypy, Pyright and
steering checks passed. The donor scan found no recorded payloads
across 3,243 production sources.

Separate work covers linked Config and Resolved streams, CMgr headers
and inline Definition headers. Native document construction and
application acceptance have their own evidence requirements.
