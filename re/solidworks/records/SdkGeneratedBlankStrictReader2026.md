# Strict reading for the canonical generated blank drawing

The strict reader passes 72 fresh SDK processes in 36 paired groups. Six generated blank files read strictly, retain their complete reconstructed input metadata and reproduce every logical stream and the entire native container. Eighteen unsupported or inconsistent inputs refuse. Partial inspection is unchanged in every pair. The evidence covers host SDK behavior on these scoped inputs. [Measured receipt](../measurements/2026/SdkGeneratedBlankStrictRead01.json)

Task `B04-SW2026-DRAWPROPS/strict-generated-blank-read`, owner `configuration_header`, delivery PR #121. Root owns integration and all native witnesses. The original native D00 source, native-saved SDK derivative, annotations and linked drawings remain outside this strict profile. The ordinary public writer is unchanged and still refuses the preserved source attributes.

## Boundary and implementation

Before this tranche, `ReadDrawing` refused every strict read before parsing, while `MakeDrawDoc` always returned the layout-inspection warning. The new private branch delegates strict reads to `ReadGeneratedBlank`. The existing `strict=False` branch is unchanged.

`ReadBlankIntent` requires exactly the seven streams below and archive version 19000. It fully decodes Definition, Header, Biography and History with the existing typed executors. The independently mapped Header2 must serialize exactly like the actual inline model header. It recovers explicit `BlankDrawInput` owners, invokes the unchanged generative `MakeBlankFile`, then compares all seven streams and the complete container. Any unrepresented authored field, cache, alias, counter, XML row or framing byte refuses. There is no copied stream, saved field program, recorded template or CAD fallback in this reconstruction.

The source document retains genuine `DrawingData` from the actual typed sheet dimensions, not the rounded decimal property copy. Structured source attributes retain `DrawDocOptions`, `ModelDefSettings`, `HeaderInput`, `HistoryInput`, `SelfFileInput`, the native sheet identity and the complete-reconstruction markers. Metadata contains semantic values and a UUID string, never native bytes, offsets or executable field instructions. The warning is removed only after the complete reconstruction passes; rejected sources retain their old partial-inspection path.

## Every stream has an owner

| Stream | Authored or observed state | Derived, constant or volatile boundary |
| --- | --- | --- |
| `Contents/Definition` | Sheet name/ratio/size; actual support ownership; folder names; fonts, widths and style vocabulary; document units; UI standard/preferences; UUID4; inline header | Shared fresh constructors compute IDs, references, maps, transforms, zones and neutral empty managers. Populated model links, sheet geometry, annotation collections, layers and blocks refuse through the complete blank codec. |
| `Header2` | Author/company/comment; separate creation, modification and update epochs; physical self locator and save event | The actual model owns the header and log. The allocator computes the next ID; the proven fresh header counters and absent external directory remain constructor state. Header2 and inline-header disagreement refuses. |
| `_MO_VERSION_19000/Biography` | Typed process telemetry if present | Only the proven empty fresh biography reproduces. Extra or populated state cannot be silently discarded. This tranche does not synthesize source telemetry. |
| `_MO_VERSION_19000/History` | Actual originating build, comment, creation epoch, license category, locale and CJK flag | The fresh profile has one version event and one originating build. Multiple events, incompatible chronology or native-only provenance outside the truthful fresh constructor domain refuse. |
| `ModelStamps` | No separate authoring input | Three unsigned words derive from actual header creation, update and body counters, in the existing emitter order. Conflicting or trailing words refuse. |
| `swXmlContents/KeyWords` | Model name, creation epoch, sheet identity/name/ratio and property-view name | The shared XML emitter derives complete framing and ordinary paper/template vocabulary from the sheet. Unknown nodes or attributes cannot disappear behind the layout parser. |
| `docProps/ISolidWorksInformation.xml` | Six derived sheet system properties | IDs `3 + ordinal`, dictionary membership, section vocabulary and literal `vt` prefix follow the existing shared rules. Additional custom text is not projected by this profile and refuses. |

The container is also classified: directory entries, compression, CRCs, offsets and signatures must be exactly the existing SDK's computed canonical representation. Alternate compression or trailing/unrecognized bytes refuse, even when a permissive stream scanner could recover the same logical streams. This is deliberately narrower than general native container reading.

The [typed blank constructor](SdkBlankDrawingFile2026.md), [sheet factory](DrawingSheetConstruction2026.md), [model factory](DrawingModelConstruction2026.md), [property grammar](DrawingPropertySections2026.md) and [literal-prefix proof](DrawingPropertyPrefix2026.md) remain the field authorities. The machine record pins the exact implementation files used for this slice.

## Locale and chronology distinctions

The fresh style constructor does not persist its full `LanguageId` input. Its ten annotation styles store the selector effect `2 if LanguageId & 1023 == 13 else 0`. History stores its actual locale separately. The reader recovers that encoded effect and chooses a legal reconstruction selector, explicitly marked representative. It never substitutes that selector for the actual History locale. Independent Mu and Nu fixtures exercise differing style/history selectors. [Focused gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Drawings/BlankStyleLanguageSelectorIsNotTheOriginalLocale.md)

Creation, modification, update and file-save epochs are separate official typed fields. Only the existing fresh constructor's creation/comment joins are required. The repeat proof replaces the actual destination and save event, preserves the other owners, and opens the result strictly again. Only Header2 and Definition change. No requirement forces original provenance to equal a later wall clock.

## Proof and remaining work

The six positives are the disclosed SDK alpha, the newly disclosed public alpha `64ce7aa7…`, and four independent neutral designs. They vary UTF-8/UTF-16 text, fonts, line widths, locale/CJK state, units, standards, flags, UUIDs, scale ratios and separate chronology. Each baseline/candidate pair uses bytes, a real source pathname or metadata-only options. Candidate reads permit only the requested pathname opens; all other audited file/process access remains zero. Public JSON serialization preserves the complete source attributes.

The negative matrix includes genuine disclosed linked SDK output, genuine native D00, a genuine native-saved SDK derivative, extra properties/streams/keyword nodes, conflicting header copies/stamps, extra chronology and unrepresented UI/framing. Annotation negatives are structural nonempty markers/collection incidences only; they do not claim a newly authored valid native note. Code also explicitly refuses unqualified annotation classes and populated collections. No old failed writer verdict is changed.

The complete source freeze contains 4701 paths and an 18-path implementation delta. Black, Ruff F401/F821, strict Mypy, strict Pyright and the recorded-payload scan pass. The raw replay is SHA-256 `d664df3daffb937f036d741c937f4d1380f0e2483909c76465bcdf3741f72629`. Original unguarded inventory, one import-prewarm observer failure and a malformed negative-fixture construction remain private historical evidence and are excluded from the passing replay.

The public read-to-public-write route remains closed: `NeedBlankDrawing` rejects source attributes and native provenance. A separate rewrite extension must structurally decode the known semantic metadata into the official typed owners, reject all unknown fields, preserve presentation/UUID/provenance, and replace only explicit destination/save inputs. It must not remove attributes to obtain writer admission. General native authored/saved drawings, model views, annotations, arbitrary styles and original-source held-out acceptance remain unfinished work.

## Independent replay

The external handoff binds both complete source manifests, all fixture/request hashes and the exact probe. It opens no private slots. Use a new output directory:

```sh
python -I -B re/tooling/sw2026/ReplayBlankStrict01.py --method /external/SdkBlankStrictRead01/Method01.json --method-sha256 44a26757e1dff641daf8216a6084e72ccb9ac11a87536ce73ef34dd077f9ab3f --baseline /external/SdkBlankStrictRead01/Base01 --candidate /external/SdkBlankStrictRead01/Code01 --output /unused/BlankStrictReplay
```

The driver verifies every source and input hash before/after the 72 process calls and compares all partial outputs. The fixture builders consume independently authored neutral requests and the existing input mapper, with no vendor file input. Their negative annotation branches intentionally bypass only the production semantic gate to construct unqualified research controls; that emitter is never imported by the SDK.
