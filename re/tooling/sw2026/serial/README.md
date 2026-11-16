# SOLIDWORKS 2026 archive serializer (research)

Research model of the `su_CArchive` object streams written by SOLIDWORKS 2026 SP05.2
(`sldworks.exe` 34.5.2.0604, file version 19000). Every class schema here is translated
from the 2026 binaries' `Serialize` / `restore` load paths. Byte identity is a schema
instrument, not evidence of a generated part. The schemas remain incomplete, including
assembly configuration roots. Their fields are not yet all classified for production.
No writer is registered by this tooling.

## Run

```
cd re/tooling/sw2026/serial
uv run --no-sync python RoundTrip.py '<glob of .SLDPRT>' [Stream/Name,Other/Stream] --report report.json [-v] [--link-config] [--require-proven]
```

Run checks in PR CI, never locally. The process exits 1 for an empty corpus, an unreadable
file, a missing requested stream, an unsupported document version, an unmodelled class,
an unread tail, or any byte difference. The default requires all seven individually
load-critical streams and checks optional modelled streams present in the document.
Explicit stream lists require every named stream. `Config-0` expands across configurations;
each configuration reads its own ModelHeader. JSON reports bind each file and stream to
SHA-256 and disclose provisional schemas.

Each stream records separate load and store schema usage, call routes, source-buffer
candidates and reached `Raw` operations with their length rules and observed byte counts.
Callable rules identify their in-memory module, source path and line without opening
the source file. Their source-text field stays null; inspect the named schema separately.
Started phases record whether they completed; failed or unstarted operations cannot
claim proven schema admission. File and invocation summaries include dependency reads.
`provisional_schemas` retains the whole registry inventory; `used_provisional_schemas`
contains only declarations reached during this invocation.

`--require-proven` also rejects used provisional or missing schemas and incomplete
operations. Unused provisional declarations do not fail it. The default retains its
existing byte-identity and unread-tail conditions. `byte_identity_passed` and
`proven_schemas` remain separate report fields. Nonprovisional declarations and
bounded raw arrays still need semantic classification and fresh construction rules.
See the [report contract](../../../../Documentation/Changes/Solidworks/Model/SolidworksArchiveSchemaUsage.md)
and [closure limitation](../../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ProvisionalSchemasDoNotProveClosure.md).

`--link-config` additionally requires each selected resolved stream to inherit
the configuration's class/object map and computed counter. Fresh builders use
`ConfigPart.store_config_state` and seed `ResolvedCore.store_resolved` with its
returned map. See the [2026 map finding](../../../solidworks/records/ArchiveMapConstruction2026.md).
The seed load has its own `schema_usage.dependencies` snapshot, source hash, byte count
and unread-tail length. Its admission contributes to the selected stream's strict result,
without claiming an additional seed-stream byte comparison.

`tests/convert/solidworks/research/` invokes the CLI at a process boundary in remote CI.
Its eight fixtures in `re/solidworks/v2026/corpus/ladder/` are privacy-redacted controls,
not held-out cases and not generated writer output. `Manifest.json` records original
and redacted hashes, authoring specifications, vendor revision and source measurements.
`re/tooling/sw2026/PrepareCorpus.py` prepares those research inputs from the original
ladder directory. It preserves encoded string widths while removing personal metadata,
then rebuilds the source container. Production must never import it or load its output.

`re/tooling/sw2026/PrepareCurveCorpus.py` separately prepares the locked curve
discovery/control family, preserving source hashes and framed metadata redactions.
It never selects the six held-out native payloads or executes archive schemas.
Its [preparation guide](../../../../Documentation/Changes/Solidworks/Model/SolidworksCurveDiscoveryCorpus.md)
describes the exact input lock, privacy ledger and fixture limits.
Remote schema checks of the prepared copies remain distinct from source-corpus
acceptance and from any future Kit-written curve output.

Corpora (2026-saved):

- `.rescratch/sw26/corpus/ladder/*.SLDPRT` (worktree root): empty part, plain, boss ladder L1-L4, controls.
- `.rescratch/sw26/corpus/kdp26/*.SLDPRT` and `.SLDASM`: 56 real parts and 7 assemblies resaved by 2026 (when present).

## Files

- `Core.py`: `Load` / `Store` archive (MFC tag grammar, class/object map, CString forms, counts,
  `ExtRef` for object refs below the stream's map base).
- `Schema.py`: ops. `P` primitive, `S` CString, `O` object (tagged ReadObject/WriteObject),
  `C` class tag only (ReadClass/WriteClass), `Cnt` MFC ReadCount/WriteCount, `Raw` fixed bytes,
  `Base(cls)` run another schema in the same field scope (base-class `Serialize`), `Emb(name, cls)`
  run a schema in a nested scope (member object's `Serialize`/`restore` called directly),
  `If`, `Rep`, `Until`, `Fn(load, store)` escape hatch.
- `Dsl.py`: helpers. `Vgt(n, ...)` = `if (fileVersion > n)`, `Vge`, `Vlt`, `Fnz(field)`,
  `Feq`, `Fbit`, `i32 u32 i16 u16 u8 i8 f64 f32 i64 u64 time32 cstr obj cls count emb base rep`.
  `CURRENT = 19000` is the version every 2026 load sees.
- `Classes.py`: container classes and auto-load of every module in `defs/`. Plans belong to
  each fresh registry, so constructing a registry repeatedly does not retain global state.
  A module defines
  `define(reg)` and may export `PLANS = {"Stream/Name": ("rooted", base) | ("resolved", None) |
("custom", load_fn, store_fn)}`.
- `Streams.py`: stream framings (`rooted`: objects until end with map base; `resolved`: u32 base then
  count then objects).
- `defs/*.py`: class schemas.

## Translation rules

1. Translate the load branch (`IsStoring() == 0`) of the 2026 decompile, in order, with every
   version gate. Evaluate gates with version 19000 but keep them in the schema.
2. Field names are the `this` offset of the destination (`f48` for `this + 0x48`). Locals that are
   read and discarded get a descriptive name.
3. `su_CArchive::AR_get_long` = `i32`, `AR_get_ulong` = `u32`, `AR_get_int` = `i32`,
   `AR_get_uint` = `u32`, `AR_get_ushort` = `u16`, `AR_get_short` = `i16`, `AR_get_uchar` = `u8`,
   `AR_get_double` = `f64`, `AR_get_float` = `f32`; `operator>>(ar, CString&)` = `cstr`;
   `operator>>(ar, CObject*&)` / `ReadObject` = `obj`; `ReadClass` = `cls`; `ReadCount` = `count`;
   `operator>>(ar, su_CTime&)` = `time32`. The `??5su_CArchive@@...` mangled forms in sldmfcu are
   the same reads (`M` float, `N` double, `H` int, `K` ulong, `G` ushort, `J` long, `I` uint,
   `F` short, `E` uchar, `D` char).
4. `su_CObject::Serialize` is a no-op. `IsDBStream()` is false for every stream modelled here,
   so `IsDBStream` branches (DBKey, msgpack) are skipped.
5. Base-class calls (`moFeature_c::Serialize(this, ar)`) become `base("moFeature_c")` with the base
   defined once as its own schema. Direct member calls (`(this+0x18)->Serialize(ar)`, `mgPoint_c::restore`)
   become `emb("name", "Class.method")`.
6. Preserve wire values separately from loader fixups. Byte identity must not silently normalize
   discarded or boolean-coerced scalars. A synthesized object still needs a field classification
   and its own derived values; wire preservation is not a source for builder defaults.
7. Never capture unexplained bytes. `Raw` only where the binary reads a byte block (`su_CArchive::Read`).
   No `Until` loops guessing ends. No schema shaped by the corpus rather than by the decompile.
8. No vendor bytes, no saved spans, no recorded programs. Schemas are code.
9. Python here is research code (`re/` is exempt from `src` style rules) but keep it plain:
   no comments, no docstrings.

## Decompile sources

Ghidra 12.1.3 projects, headless:

- A local `sw26gh/out/cl_sldmodu.c`, `cl_sldmfcu.c`,
  `cl_sldarchiveu.c`: archive-closure decompiles from every corpus class `Serialize`, following
  each call that receives the archive (depth 4). `=== EDGE` lines list the archive-taking calls.
- `.../out/lad_*.c`: just the roots.
- `.rescratch/sw26/SerializeMap2026.json`: class -> DLL, `Serialize` address, vtable.
- `.rescratch/sw26/classes_ladder.json`: classes seen per stream in the ladder corpus.
- More decompiles: `PROJ_ROOT=<your copy> ./dump.sh <proj> <prog.dll> <out.c> <spec.txt> <depth> <timeout>`
  or `closure.sh` (spec lines are `0xADDR [archiveSlot]` or name substrings), run from
  the local `sw26gh` research checkout. Use only your
  assigned project copy, never `proj/`. Programs: project `sldmodu` holds `sldmodu.dll`; `sldmfcu`
  holds `sldmfcu.dll`; `swccu` holds `swccu.dll` and `sldarchiveu.dll`.
- DLLs not in Ghidra (sldmgu, sldgcu, slduiu, ...): `.rescratch/sw26/bin/*.dll`; disassemble with
  `.rescratch/sw26/venv/bin/python re/tooling/sw2026/Dis.py <dll> <hexVA> <nbytes>` (resolves imports
  and exports). Ghidra drops some import calls; cross-check suspicious gaps against disassembly.
- 2025 notes in `re/solidworks/records/*.md` are hints only; 2026 differs.

## Ownership

One agent owns each `defs/` module. A class has exactly one owner. To use a class another module
owns before it exists, declare it with `reg.provisional(name, ops)` in your module; the owner's
`reg.define` replaces it. Report every provisional you used.
