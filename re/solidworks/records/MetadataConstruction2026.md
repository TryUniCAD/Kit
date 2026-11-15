# SOLIDWORKS 2026 metadata construction candidates

The research builder in [`Metadata.py`](../../tooling/sw2026/builders/Metadata.py)
constructs `Header2`, configuration `ModelHeader`, `Biography`, `History` and
`KeyWords` streams from explicit semantic inputs. It returns new archive objects
or bytes and opens no files. It does not consume a saved stream, a captured table,
a donor file, a recorded field program or a vendor runtime.

Status: **research construction candidates, without fresh-document vendor
acceptance**. Native constructor seeds establish initial object state. They do
not establish the complete state after a model has been built and saved. The
unresolved fields below prevent a general fresh-model writer from being claimed.
The related eight-control ladder proves source-codec byte identity only.

## Interface

Place both `re/tooling/sw2026` and `re/tooling/sw2026/serial` on the caller's
import path. Use the same `Core.Obj` and `Classes.registry()` module instances as
the other 2026 builders. All public construction parameters are keyword-only.

```python
stamp(*, status, user_index, company_index, timestamp, comment) -> dict
header(*, next_id, user_names, company_names, revision_logs, created_at,
       modified_at, updated_at, model_present, component_count, update_stamp,
       body_stamp, license_flags, license_type) -> Obj
biography() -> Obj
history(*, states, failure_severity, minimum_free_memory, license_origin,
        language_id, cjk_saved, cjk_warning) -> Obj
keywords(*, name, timestamp, configurations, features) -> bytes
streams(*, registry, header2, model_headers, biography_record, history_record,
        keywords_data) -> dict[str, bytes]
```

`string_array(*, values)` and `object_list(*, values)` construct the two archive
containers used by the header. They do not import preexisting archive objects
from a file. `streams` uses the shared schemas at format version 19000 and map
base 1; archive map tags, class declarations, object references, counts and string
encodings come from the source codec. Each call creates its own archive map.

`model_headers` maps integer configuration ids to distinct semantic header
objects. The output names are `Contents/Config-{id}-ModelHeader`. The other names
are `Header2`, `_MO_VERSION_19000/Biography`, `_MO_VERSION_19000/History` and
`swXmlContents/KeyWords`. Keyword configuration ids must match model-header ids.
This component returns stream bytes; it does not construct a complete part or
assembly container and does not make one loadable by itself.

## Authored provenance and graph inputs

All timestamps are explicit unsigned 32-bit Unix time values. No function reads
the host clock, user identity, machine telemetry or a vendor installation.
`modified_at` must be at least `created_at`. `created_at` must equal the first
stamp of the first revision log. The builder does not silently substitute the
native timestamp sentinel or constructor clock time.

Each revision log is `{"object_id": int, "stamps": [semantic_stamp, ...]}`.
The optional `name` must be empty because `moLogs_c.f50` has no recovered role.
Log ids must be unique and below the caller's next allocated persistent id.
A semantic stamp contains exactly `status`, `user_index`, `company_index`,
`timestamp` and `comment`. Status 0 is the recovered fresh-state profile. Every
stamp resolves its indices through explicit authored user/company tables.
History indices must resolve to the same names in Header2 and every model header.

The caller supplies the next persistent id produced by its allocator. The
builder does not use feature count as an id formula. In particular,
`24 + 2 × visible_feature_count` is refuted by the native allocation code.
An owner model pointer determines `model_present` independently for Header2 and
each ModelHeader; matching booleans are not assumed.

History `states` contains mappings with `file_version`, `date_codes` and `stamp`.
Each date-code entry is `{"build_code": int, "native_save": bool}`. Build codes
must be explicit nonzero low-24-bit originating-build provenance. They are not
calculated from geometry or copied from a saved control. A supplied value is
an authored assertion, not evidence of a native vendor save. Since native-save
flag semantics remain incomplete, `native_save=True` fails rather than being
fabricated or cleared. A caller without truthful build provenance cannot use
this constructor as a default history generator.

`license_origin` explicitly preserves one of the recovered categories
0/10/20/30/40/50. It must describe the authored provenance and must not be used
to erase an existing classification or impersonate a licensed vendor save.
Header license flags/type are explicitly required and currently accept only 0;
nonzero values fail because their construction domains remain unresolved.

Keywords contain only the caller's actual neutral document graph. A configuration
has `id`, `name` and `material`. A feature has `id`, `name`, `kind` and optional
`tag`, `dimensions`, `children`, `dissectable`, `root`. Tags are limited to the
recovered `Feature`, `Sketch` and `Extrusion` families. No stock feature-name/id
table is supplied. Dimensions have a unique `name` and finite numeric `value`
already expressed in presentation units. XML escaping and UTF-8 come from
ElementTree. Feature ids are unique; every referenced child must exist. The
multi-child text grammar is unresolved, so more than one child fails.

## Header fields and binary ownership

The DLL and hash identities are recorded in
[`HeaderConstruction2026.md`](HeaderConstruction2026.md) and the
[2026 manifest](../v2026/Manifest2026.json). Addresses below are actual 2026
addresses, not offsets inferred from control bytes. All header/log/stamp
addresses in this table belong to `sldarchiveu.dll`.

| Emitted fields              | Classification and formula                                                                                       | Binary evidence                                                                            | Remaining restriction                                                                      |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| `f08`                       | derived input: allocator's next id; highest id is `f08 - 1`; native allocation increments and skips reserved ids | `0x31a05230`, `0x31a052d0`                                                                 | reserved-id policy belongs to the model allocator, not feature count                       |
| `f10/f18/f20`               | input names plus constructed log/stamp graph; list counts are lengths                                            | `0x31a049d0`, `0x31a03120`, `0x31a030b0`, `0x31a04da0`, `0x31a05420`                       | only authored identities and fresh status 0                                                |
| log `f48/f50`               | input object id; empty string constructor seed                                                                   | constructors `0x31a02690`, `0x31a026e0`                                                    | log ownership beyond explicit ids and nonempty `f50` unresolved                            |
| stamp `f08/f0c/f10/f18/f20` | status 0, name-table indices, explicit time, explicit comment                                                    | constructor `0x31a02790`, default `0x31a02860`, serializer `0x31a048b0`                    | no other status domain recovered                                                           |
| `f40/f44`                   | derived input counters, initial native seeds 101/101                                                             | constructor `0x31a02580`, `0x31a02587`; mutations `0x31a04f20`, `0x31a05340`               | callers supply counters reflecting actual model operations                                 |
| `f48/f50/f70`               | volatile inputs: update/modification/creation timestamps                                                         | `0x31a025b4`, `0x31a034f0`, `0x31a05ec0`                                                   | full native save normalization still needs acceptance                                      |
| `fec`                       | derived `int(owner_model is present)`                                                                            | save instructions `0x31a03575`–`0x31a03586`                                                | separate owner context per stream                                                          |
| `fc4`                       | derived input component count, currently required 0                                                              | `0x31a05380`                                                                               | assembly reference state not constructed                                                   |
| `f7c/f80`                   | explicit license inputs, currently required 0                                                                    | `0x31a052a0`, `0x31a052b0`                                                                 | nonzero domains unresolved; must not clear prior provenance                                |
| `f28/f30/f38/f88`           | constructor-null attachment, external-reference, self-reference and replaced-component lists                     | ctor `0x31a02540`; getters/creators `0x31a052c0`, `0x31a04d10`, `0x319f89d0`, `0x31a04d50` | no linked files, replacements or reference graphs in this profile                          |
| `bboxflag`                  | derived native pointer-presence seed 0                                                                           | ctor `0x31a025ec`, serializer `0x31a034f0`                                                 | empty cached bounds are a construction candidate, not proven neutral output                |
| `fcc/fd0/fd4`               | volatile previous-open seeds -1; current fields are also -1 on construction, so save falls back to previous      | ctor `0x31a0264b`–`0x31a0266b`, serializer `0x31a034f0`                                    | never copied session measurements                                                          |
| `f58/f60/f64/f68`           | constructor seeds 0 for lock, break counter, freeze and detachable state                                         | ctor `0x31a02540`; `0x31a058b0`, `0x31a062b0`, `0x31a04ba0`, `0x319f8780`, `0x319f9a30`    | initial profile only                                                                       |
| `f78/f98/fc0/fc8/fe8`       | constructor seeds 0; usage/icon enums, unknown flags/scalar and copied state                                     | ctor `0x31a02540`–`0x31a02670`; getters `0x319f8a70`, `0x31a056a0`, `0x31a05100`           | enum/flag domains and later state transitions unresolved                                   |
| `f9c/fa0/fa4/fa8/fac/fb0`   | constructor seeds 0; native add rule ORs a flag; 2/4/8/16/32 increment the corresponding count                   | `0x31a04a40`; removal `0x31a05920`                                                         | 2/4/8 are macro-feature categories below; 16/32 and the full mask domain remain unresolved |
| `ff0/ff4/ff8/ffc/f100`      | constructor-zero external-reference summaries                                                                    | ctor `0x31a02540`; synchronization `0x31a06210`                                            | individual summary meanings unresolved                                                     |
| `f104/f108/f10c`            | constructor seeds 0 for visible-sketch, annotation and graphics state                                            | `0x31a06430`, `0x31a05f40`, `0x31a05f50`                                                   | final model-derived rules still required                                                   |

`sldutu.dll!ut_getUnsetTime` at `0x3d03ebb0` returns literal `0x278d00`.
This utility fact is fully recovered, but does not justify using that sentinel
as every generated document's modification time. The builder requires authored
timestamps instead. None of the related ladder's invariant header values is
treated as a new global constant.

### Active content is not ordinary feature count

The export at `sldarchiveu.dll!0x31a04a40` is named
`moHeader_c::addActiveContentFlag(swActiveContentTypes_e)`. Flags 2, 4, 8,
16 and 32 increment `fa0`, `fa4`, `fa8`, `fac` and `fb0`, respectively;
the function ORs the supplied flag into `f9c`. Removal at `0x31a05920`
decrements the matching counter and clears that bit only when its counter
reaches zero. These are accumulated active-content counts, not the number of
all ordinary sketch/extrude feature objects.

The following caller classification comes from actual 2026 `sldmodu.dll`
instructions. `moFeature_c::undelete` at `0x4bb53b20` first checks that the
object is a `moMacroFeature_c`, obtains its owning model header, then calls
`addActiveContentFlag` at `0x4bb53c31`. Its branch classification is:

| Category | Native condition                                                      | Evidence                                     |
| -------- | --------------------------------------------------------------------- | -------------------------------------------- |
| 2        | macro feature's virtual slot `0xc60` returns true                     | call `0x4bb53c07`; selects 2 at `0x4bb53c11` |
| 8        | preceding condition false and `moMacroFeature_c::isCOMFeature()` true | call `0x4bb53c1b`; selects 8 at `0x4bb53c20` |
| 4        | both preceding conditions false                                       | selects 4 at `0x4bb53c29`                    |

The primary macro-feature vtable is `0x4d0c4020`; its `0xc60` slot points to
`0x4c005d40`, which returns `(macro.fcc8 >> 4) & 1`. That bit's authored
semantic meaning remains unresolved. `isCOMFeature` is exported at
`0x4b2bd490`. Deletion mirrors these branches in `moFeature_c::onDelete`
at `0x4bb4e320`, with removal call `0x4bb4e420`. Legacy macro loading also
adds these categories at `0x4bb24ca6` for file versions below `0x2fa4`.

This recovers three categories without asserting a meaning for the native
macro flag, inventing values for categories 16/32 or proving that no other
subsystem contributes. The current constructor profile emits the initial
zero-content seeds and does not construct active macro-content state. See the
[counter gotcha](../../../Documentation/Gotchas/Solidworks/HeaderActiveContentCounts.md).

## Biography and history fields

Detailed construction evidence is in
[`HistoryConstruction2026.md`](HistoryConstruction2026.md). The addresses in
the next table belong to `sldmodu.dll` unless another owner is named.

| Fields                      | Classification and construction                                                                                          | Evidence                                                                                                               | Remaining restriction                                                                   |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Biography `n/records`       | derived zero-length persisted list                                                                                       | serializer `0x4c71ec40`: explicit loader branch appends a newly initialized current record after reading saved records | zero-record candidate has no target acceptance; no fabricated machine telemetry         |
| History `n/states`          | derived nonzero length of authored states                                                                                | serializer `0x4c71fb70`, appender `0x4c720800`                                                                         | loader dereferences the last state; empty history rejected                              |
| version-state `f08/f30/f38` | explicit semantic stamp, target version 19000, constructed date-code-history object                                      | serializer `0x4c720030`                                                                                                | only the recovered current-version profile                                              |
| date-code `n/states/f08`    | derived nonzero length; explicit build code with native-save flag absent                                                 | serializers `0x4c71f5b0`, `0x4bb5cba0`                                                                                 | native-save flag `0x01000000` semantics unresolved; missing provenance rejected         |
| `f28/f2c`                   | explicit severity and minimum-free-memory provenance; native accumulation uses max/min; constructor seeds 0/`0xffffffff` | ctor `0x4c71dea0`, serializer `0x4c71fb70`                                                                             | authored supplied state, no host-memory observation or recorded telemetry               |
| `f30`                       | explicit origin category 0/10/20/30/40/50                                                                                | helper `0x4c720ab0`                                                                                                    | no erased or fabricated license history                                                 |
| `f38/f3c/f40`               | explicit language and CJK state; save sets `f3c=1` when `(LANGID & 0x3ff)` is 4, 17 or 18                                | serializer `0x4c71fb70`                                                                                                | rejects missing saved-CJK flag for these language ids; broader flag behavior unresolved |
| build-code utility          | if tagged `t` is 1..99999, add 2000000 below 9600, otherwise 1900000; outside range return unchanged                     | `sldutu.dll!su_getFullDateCode` `0x3d0107b0`, tagged helper `0x3d014520`                                               | originating-build metadata decoding unresolved; no generated vendor-build claim         |

## Keywords framing and evidence limits

The format is byte `0x86`, an XML declaration for UTF-8, CRLF, a `Keywords`
element, then CRLF, without a BOM. The format field and its 2026 source-codec
verification are recorded in the parent research. Configurations and features
are emitted from actual semantic inputs. The historical 2025 stock table is
not a construction source. This component has no recovered native serializer
address for every keyword subtype; unsupported tags and multi-child encodings
therefore fail closed.

## Verification and remaining work

The PR adds subprocess integration checks in
`tests/convert/solidworks/research/MetadataConstructionTests.py` and the dedicated
`MetadataProcess.py` driver. Inputs are synthetic authored JSON, including
explicit non-native test provenance. After source-schema imports, the child
blocks all file opens, directory reads and subprocess launches. It constructs
variable stream sets, decodes them through the actual source codecs, consumes
every byte and re-encodes identical bytes. Assertions cover persistent ids,
independent owner context, variable log/date-code/configuration/feature counts,
authored Unicode, XML escaping, dimensions and links. Rejections cover missing
build provenance, unsupported native-save flags, nonzero license fields and
cross-header identity mismatches. Code imports occur before the runtime input
guard; the test does not claim to prohibit source-module reads.

No tests, reproductions, collection, imports of the builder or CAD operations
were run locally. Local verification is restricted to static parsing and
formatting. Remote PR CI supplies process-check evidence. Neither those checks
nor source-control round trips establish vendor acceptance.

The remote [workflow-quality smoke job](https://github.com/TryUniCAD/Kit/actions/runs/43673584432/job/132688748536)
checked the PR merge of head `a0bac133eef1fba1ade4659e50caa52650e2bce9` into
base `577a5127ace5234ca9d2fe4a7255715740c87b5d`. It selected all three metadata
process checks and completed with **126 passed, 158 skipped in 19.55 seconds**.
The skips are unrelated unavailable source corpora. The new metadata process
checks passed and did not use those corpora. This is process-construction
evidence, not a native application acceptance result; later PR heads require
their own fresh remote checks and approvals.

The next acceptance measurement requires the oracle owner to combine these
records with generated model/configuration streams and validate a held-out
document plus a passing control. Unknown header summaries, flags, reference
graphs, bounds, final counters and save normalization still require recovery.
Assemblies and inherited vendor provenance remain unsupported here.

The governing [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
state: “There are two acceptable stopping conditions. The first is success under
every criterion on this page. The second is the end of the available context.
Missing grammar is the work. It is not a blocker.” This component PR does not
narrow those conditions or complete the parent writer goal.
