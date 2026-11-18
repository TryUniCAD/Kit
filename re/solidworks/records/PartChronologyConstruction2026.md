# Part chronology and source identity in SOLIDWORKS 2026

**Typed component construction passes 32 host processes. Complete original-source preparation remains unqualified.** No new native lifecycle ran.

| Item | Boundary |
| --- | --- |
| Task | B04-SW2026-PART-CHRONOLOGY |
| Owner | `/root/configuration_header`; `/root` owns integration and the native oracle |
| Delivery | PR #121 |
| Base | `48122d40b3930e2c011135f30f1c2f46a9bec045` |
| Target | SOLIDWORKS 2026 SP05.2, executable 34.5.2.0604, archive version 19000 |
| Sources | Three previously disclosed ordinary Front revolves and disclosed through-all D01 |
| Dependencies | Shared Header, Config, Resolved, History and file-identity codecs; actual generated feature owners |
| Exit reached | Source-owner correlation, generative Header component, precise feature-time encoding and guarded process proof |
| Remaining exit | Complete source-intent projection, every unsupported source owner, controlled native qualification and independent originals |

## Separate time owners

The [native range ledger](PartChronologyNative2026.json) binds the original installed modules and selected function ranges. It contains addresses and hashes. It contains no vendor instructions or binaries. [Earlier complete clock trace](DrawingSourceEpochOwnership2026.md) and [measured independent epochs](DrawingSourceEpochNativeLifecycle2026.md) supply the established shared rules.

| Owner | Representation and rule | Construction boundary |
| --- | --- | --- |
| `moHeader_c.f70` | Creation identity, runtime `su_CTime`; modern wire value is unsigned 32-bit Unix seconds | Explicit `HeaderClocks.CreatedAt`; shared self creation must retain this identity |
| `moHeader_c.f50` | Independent archive-time slot with a local-calendar unset-year repair | Explicit modern `ArchiveAt`; this is not the latest-revision getter |
| `moHeader_c.f48` | Independent update wall time | Explicit `UpdatedAt`; it is not the header counter |
| `moLogs_c.f48` | Actual owning model or feature persistent ID | Derived from the supplied real node, never a supplied numeric patch target |
| `moLogs_c.f50` | Independent caption | Explicit text; identity does not depend on matching the current node name |
| `moStamp_c.f18` | Individual revision event, whole Unix seconds | Explicit ordered semantic events with separate attribution |
| Feature `f2a0/f2a4` | Low/high FILETIME words stored as signed 32-bit values | `FeatureInstant` preserves whole seconds and 100 ns fractions |
| Feature `f2b0/f2b4` | Creation file version and build code | Provenance, not time; this tranche adds no assignments |
| Feature `f300/f301/f2ac` | Creation service pack, subservice pack and kernel behavior | Separate provenance, exposed by the bound creation-version getter |
| Feature `f2b8/f2bc` | Last-update file version and build code | The bound `getLastUpdateVersion` reads these fields; they are not another epoch |
| Version-state embedded stamp `f08.f18` | Independent version-history event | Existing explicit `HistoryInput.CreatedAt`; no inferred header equality |
| Date-code-history states | Ordered build codes with a separate high flag | Read and exactly re-emit; the unresolved high flag is not generated |
| Biography start/end `f08/f0c` | Independent runtime FILETIME pairs | Observation only; fresh generation retains the existing empty biography |
| Self shared `f28` | File creation identity | Existing `MakeSelfFile` derives it from the actual generated header |
| Self `f60` | Save-event Unix seconds | Explicit `SelfFileInput.SavedAt` |
| Manager-header `f60` | Separate manager save owner | Existing `MakeMgrHeader`; experiments preserve the admitted equal-save policy |
| `docProps/core.xml` creation/modification | Separate explicitly named XML dates | Observed only; no new XML constructor or public projection |

Header counters `f08/f40/f44` and feature `f29c` are allocation/update counters. They are not clocks. Previous-open scalar fields are not promoted to Unix epochs.

The selected field layouts and native owners are **confirmed** for this build. Complete original-source emission and the new variants' native behavior remain **partial**. Attribution names, captions, comments and declared events are inputs. Numeric attribution indices, collection lengths, log IDs and time words are derived. Class/schema declarations and enum codes are format vocabulary. Runtime telemetry and unresolved source flags are not constructor inputs.

## Disclosed source correlation

The [receipt](../measurements/2026/PartChronologyConstruction01.json) binds all four original file hashes and the exact observations. No hidden source was read.

| Source | Header creation `f70` | Archive slot `f50` | Update `f48` | Latest log-tail event | Self and manager save | Logs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full revolve | 1794894338 | 1794529625 | 1794894348 | 1794894346 | 1794894349 | 26 |
| Partial forward | 1794894388 | 1794529625 | 1794894398 | 1794894396 | 1794894399 | 26 |
| Partial reverse | 1794894436 | 1794529625 | 1794894446 | 1794894443 | 1794894446 | 26 |
| Through-all D01 | 1795020274 | 1794529625 | 1795020282 | 1795020282 | 1795020287 | 28 |

Every source's first model event is `1794529623`. Its first version-history event is `1794529625`. These are observations, never generator defaults. The native methods explain independent owners; equal values do not establish an equality rule.

The three revolve axis references select actual profile ID 26. Their stored creation selectors equal the profile's first log event: `1794894343`, `1794894393` and `1794894440`. Separate feature FILETIME values retain fractional precision and can describe later updates. The composer must derive a selected reference from its emitted log, not from the feature FILETIME or document clock. [Existing reference-time rule](../../../Documentation/Gotchas/Conversion/Solidworks/FeatureReferenceCreationTimes.md)

The four actual `moPrtExplViewManager_c` helpers have zero FILETIME words and no name. The observer records that state separately. It does not interpret zero FILETIME as Unix epoch zero. The raw observer's `zero_constructor_state` label is observational, not attribution to a measured constructor call.

## Typed construction

[`MakeIntentHead`](../../../src/convert/adapters/solidworks/Archive/Construction/Chronology/MakeIntentHead.py) is a separate internal Header factory. It leaves `HeaderInput`, `MakePartHeader`, every existing caller and public registration unchanged.

`RevisionBook` receives ordered user/company names and `RevisionLog` intentions. Each log supplies an actual constructed node, independent caption and ordered `RevisionEvent` values. The builder computes user/company indices, actual log IDs, collection lengths and fresh object graphs. Created and modified operations use the mapped codes 0 and 1. Unknown operations, ambiguous names, foreign owners and unsupported classes reject.

The Header factory requires the real `moPart_c`, concrete schema-one owners, unique signed-range persistent IDs and one actual model creation event. Nonmodel features must point to that same actual part. Each Header role receives separate mutable log/stamp nodes. The normal complete composer retains one shared self object across its two Header roles.

The factory uses the shared fresh Header initializer. It then supplies the independent archive slot and semantic revision graph before serialization. It computes no field from a saved byte span. Its conservative wall-time domain excludes unset-time and sentinel-year branches.

[`MakeFeatTime`](../../../src/convert/adapters/solidworks/Archive/Construction/Chronology/MakeFeatTime.py) derives ticks as `(seconds + 11644473600) * 10000000 + fraction`. It splits the result into signed native words. A zero fraction reproduces existing `FeatureTime` exactly. The operation does not simulate registration, rebuild scheduling, version marking or a frozen document.

The current Header-owner whitelist covers the measured part/system/sketch/boss roles. Through-all D01 contributes log-grammar correlation. Its cut owner is not added to this factory's admission by that comparison alone.

## Source identity and current refusal

All four originals store model name and self name `Part1`. Their physical basenames differ. Their stored self paths are empty and persisted self state is 8. The [ordinary native factory](AssemblyConstruction2026.md#ordinary-self-reference-construction) derives the self name from the actual model independently of its path. The store can derive persisted bit 8 from runtime bit `0x100`. This tranche does not establish that runtime bit's full meaning or transplant it into new output.

The unchanged `CheckPartInput` currently requires output stem equality with the modeled name. An ordinary mismatched-path experiment correctly refuses there. The separate lower-owner experiment constructs only the already mapped self/header relationships with an explicit destination. It retains the ordinary preparation refusal as a required check. It is not a public writer path or original-source conversion.

Two such lower-owner cases preserve actual Config model name, both self names, full declared paths, creation identity, save event and strict cacheless geometry. The public reader has no flat `metadata['name']` projection at this revision. The observer verifies typed identity and records that public gap. [Identity gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Chronology/TypedModelNameIsNotFlatMetadata.md)

## Verification

The 30-process chronology result passes four native-source observers, eight complete neutral constructions and eighteen rejection workers. Source semantic log reconstruction exactly reproduces both Headers. Seven source streams per part re-emit exactly. All 102 nonzero feature times reconstruct their exact native words. Four zero states remain distinct.

Four coupled constructions preserve all previous whole-file hashes. Four split constructions vary archive time, root events, attribution, captions, update/save times and the version event. Two deterministic builds agree. Only Header2, ModelHeader, CMgrHdr2 and History change. Config, Resolved, Definition, CMgr, Biography and KeyWords remain identical. Strict public history/default reads preserve geometry and complete B-rep validation.

Two further processes verify the lower self-owner experiment. The source input files remain unchanged. Audits reject file opens, process launches, network events and native-library loads during product execution. Directory metadata operations were not separately audited. Black, Ruff, steering, strict Mypy and strict Pyright pass all thirteen new SDK files. The donor scan reports no recorded payloads in 4,592 Python files.

The root replay reproduces the exact 30-worker chronology report and the
two-worker standalone identity report. The first combined wrapper reached
all thirty chronology results and failed on an isolated identity runner
import. The corrected independent combined replay passes all 32 fresh
workers. Its aggregate hash is
`f3873f0bbd6a6058b611dd03574838f900707f27de688e5ce3b4d0401d54a0ca`.
The identity workers and modeled cases are identical across the standalone
and corrected isolated reports.

The first false chronology result stopped on a lazy observer code import. The second stopped on an expected `TypeError` reported as `ValueError`. Both remain false. The corrected worker requires the actual exception class for the named case. Both identity failures remain preserved: the valid ordinary preparation refusal, then the reporter's unsupported flat-name assumption. No SDK repair or relaxed geometry decision was used.

## Remaining source owners

Complete original preparation remains refused. Required work includes complete source presentation, primary/density unit settings, anonymous configuration manager identity, historical Header state and source properties. Feature event scheduling and every dependent reference-time join need explicit source-to-target construction. History's high flag and populated Biography telemetry remain observation-only. Native body-label authority remains the prior separate boundary.

The thirteen-file SDK layer adds no source-to-public preparation bridge, public registration, new vendor acceptance or original held-out credit. The new split/header/self variants require controlled native qualification. Existing four native-qualified artifact hashes remain unchanged.
