# System-scale archive body on SOLIDWORKS 2026

The exact current-build `moScaleSysScale_c` serializer contributes zero body bytes. Its actual primary table, RTTI, runtime-class descriptor and complete entry-reachable instructions establish the rule independently of a source save.

Task `B04-SW2026-DRAWPROPS`, PR 121, ordinary version 19000 linked/named drawing Definition raw codec. Fresh construction, implicit model/style lookup and complete source admission remain outside this tranche.

## Original native identity

`sldmfcu.dll`, 8,274,520 bytes, SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`, preferred base `0x3c720000`, AMD64, fixed file version `34.5.2.0604`. The resource tree and fixed version structure were independently read from the original file. No vendor code was loaded or executed.

Actual vtable `0x3cc8c4e0` has complete-object locator `0x3ccda3c8`. Its RTTI chain is `moScaleSysScale_c`, `su_CObject`, `CObject`. Slot `+0x28` points directly to `0x3c74caa0`.

The complete entry-reachable serializer span is `[0x3c74caa0, 0x3c74caa3)`, three bytes, SHA-256 `b6cbececf1b07e74f37d57710c68c31f0b92cb08d51093252b321b07542e177b`. Apple LLVM 21 decodes a single immediate return with zero stack adjustment. There are no archive/receiver accesses, calls, base calls, conditionals or other reachable instructions. Alignment after the return is excluded. The exact x64 exception directory contains 18,542 records in 222,504 bytes and has no covering unwind row for this leaf. Raw section padding was not parsed as exception records.

Primary table slot zero reaches `GetThisClass` at `[0x3c90ca90, 0x3c90ca98)`, eight bytes, SHA-256 `e4eed782dbe12f87085316ad395fb71c5ad3740cca518793c06921142e78d8b4`. It returns descriptor `0x3ce6f760` directly. That descriptor names `moScaleSysScale_c`, reports object size 32 and versioned schema word `0x80000001`; the admitted wire schema is one. The factory pointer is recorded but its constructor was not analyzed here.

## Serialization rule

| Property                                                    | Rule                                                   |
| ----------------------------------------------------------- | ------------------------------------------------------ |
| Supported runtime class                                     | Concrete `moScaleSysScale_c`, schema 1                 |
| Supported SDK archive profile                               | Ordinary version 19000 linked/named drawing Definition |
| Ordered additional fields                                   | Empty sequence                                         |
| Additional body width                                       | Zero bytes                                             |
| Base serialization call                                     | None                                                   |
| Read/store, version or context branch inside this body      | None                                                   |
| Class tags, schema descriptors and object/class map entries | Existing shared archive rules, unchanged               |

Both schema admission and the empty layout are explicit. Unknown classes, other schema values and unsupported archive versions retain their existing failures. Runtime state is not inferred from the absence of wire fields. No neutral scale constructor or saved default is introduced.

The recorded map's nearest serializer symbol names an unrelated destructor; the current object dump also exposes an unrelated UI method alias at this shared return entry. Class identity comes from the actual RTTI/vtable binding, not either symbol label.

REA `binary_session` reported no open target and pending cleanup owned elsewhere. This lane opened or closed no shared target. Independent original-PE table reads and LLVM instruction decoding supply the native proof; no provider decompilation or runtime trace is claimed.

## SDK and actual source read

The separate current reader change adds one empty layout and one schema-one class admission in `FrontLayouts.py` and `FrontSchemas.py`. The generic field evaluator already represents an explicitly empty schema. The original frozen writer closure remains `645a423b76792abc04823cdf44a72c3df940847d1e4bd966dc07e6b57ea3d864` and is unchanged.

The separately frozen 4,347-file reader candidate differs at exactly those two files. Both already-disclosed original drawings now advance beyond the scale object and fail closed at `moCompProfile_c` schema 1. Neither full stream has been admitted, so no typed stream byte identity or complete public strict-read support is claimed. The next class is a separate knowledge tranche.

Static AST, Black and Ruff checks passed. The earlier disclosed 43-worker baseline is bound. Root independently replayed the new reader candidate: all 43 workers passed, source remained immutable, result SHA-256 `e475046e88482ef88dc14b3ea3cdf67ec2dc9eebd93a7d01dd3b2be15c518723`. No local test suite or native application ran in this implementation lane. The original held-out writer verdict remains false.

## Remaining boundaries

The empty wire body does not establish a fresh object's implicit scale source, document ownership, constructor state or consumer behavior. Those rules need independent native proof and newly authored disclosed controls. The notes-area/ink distinction and full source presentation remain unqualified. No public writer registration changed.

> The first is success under every criterion on this page.
> The second is the end of the available context.

The CAD stopping conditions remain in force; this is a raw archive primitive, not a completed drawing-family conversion.

Native proof: [exact metadata and hashes](ScaleSystemArchive2026.json). Actual source reads: [diagnostic receipt](../measurements/2026/ScaleSystemReaderDiagnostics01.json).
