# Drawing source epoch ownership in SOLIDWORKS 2026

**Unqualified constructor expansion.** This record binds native clock ownership and a new controlled probe proposal. No constructor guard, public read/write flag, writer or native acceptance result changes.

| Item | Boundary |
| --- | --- |
| Task | B04-SW2026-DRAWING-ORIGIN-PROFILE, source epoch dependency |
| Owner | `/root/flag_ownership`; `/root` owns integration and the native oracle |
| Delivery | PR #121 |
| Target | SOLIDWORKS 2026 SP05.2, executable version 34.5.2.0604 |
| Inputs | Already-disclosed D01–D04 and generated replay06 metadata; original licensed modules outside the checkout |
| Dependency | Actual Header, self-file, root-log and version-history owners; the frozen origin writer and linked SDK codecs |
| Exit | Independently modeled clock axes pass a newly frozen controlled native lifecycle and typed readback before constructor admission expands |

## Finding

The native format does not impose one common creation epoch on the header, model-root log and version history. The current fresh constructor does impose that policy. Its separate `ModifiedAt >= CreatedAt` guard is also stronger than the bound header serializer.

This distinction explains a source refusal; it does not justify removing a guard. Higher-level native load/save callers and cross-document identity still need controlled measurement for each proposed fresh state.

The [native metadata](DrawingSourceEpochNative2026.json) pins four original modules, 27 complete function bodies, nine instruction windows and the relevant imports. It contains addresses and hashes, not vendor instructions or decompiled code. PE exception-directory sizes bound the unwind records; raw `.pdata` padding was not interpreted as records. Chained fragments are retained, including all four fragments of `updateRevisionLog`.

## Independent clock owners

The table uses the ordinary version-19000 path. Native `su_CTime` stores a signed 64-bit runtime value. The archive encoding writes its low 32 bits; reading `0xffffffff` yields runtime `-1`, while other words are zero-extended. These runtime and wire representations must remain distinct.

| Owner and field | Class | Bound rule | Confidence and limit |
| --- | --- | --- | --- |
| Header `f70` | volatile identity bookkeeping, optionally supplied as explicit model provenance | `getCreationTime` returns this member. Creation setters also update the actual self-file creation identity | Confirmed in the selected methods; upstream invocation is not fully mapped |
| Header `f48` | volatile update bookkeeping | `getCurrentUpdateTimeStamp`, `setCurrentUpdateTimeStamp` and `setUpdateTimeStamp` access this member directly | Confirmed; no assertion that higher-level saves leave it unchanged |
| Header `f50` | volatile archive-time slot, called `ModifiedAt` by the current constructor | Serialized independently, with the local-calendar sentinel repair below | Confirmed repair and representation; broader business meaning remains partial |
| Header `f20` → actual model `moLogs_c` → first `moStamp_c.f18` | revision-event bookkeeping | Owned by the actual model persistent id and name; event time is not automatically `f70` | Confirmed owner and selected setter behavior |
| `_MO_VERSION_19000/History` → `moVersionState_c.f08.f18` | independent version-history event bookkeeping | `moVersionHistory_c::fileCreated` constructs a new embedded stamp using its own clock sample | Confirmed native factory; arbitrary fresh combinations are unmeasured |
| Actual self `moExtObject_c` → shared `f28` | external file creation identity | `getTimestamp` reads the actual shared record; creation setters replace that shared record when required | Confirmed; this probe preserves equality with header `f70` |
| Self `f60` and manager-header `f60` | separate save bookkeeping | Different owners supply external-directory modification and last-save fields | Existing [directory-time rule](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ExternalReferences/ChildDirectoryTimesHaveDistinctOwners.md); not root/history event clocks |
| User, company and comment strings | authored metadata | Explicit neutral inputs and their actual header-table indices | Do not infer them from any clock |

`su_CTime::GetTickCount` is wall-clock seconds, despite its name. The exact function calls `_time64(NULL)`. It is not the Windows uptime counter. The header's `f48` constructor uses a local-calendar 1990-01-01 time; it is not an irreducible Unix-second constant. Its `f50` constructor uses native unset time `2592000`; `f70` starts at runtime `-1`.

The [existing header construction record](HeaderConstruction2026.md), [history record](HistoryConstruction2026.md), [header epoch integration](SdkHeaderEpochIntegration2026.md) and [portable projection record](DrawingOriginPortableProjection2026.md) provide the surrounding graph rules.

## Creation identity versus first event

Let `C` be header `f70`, `R` the first event of the first revision log, and `S` the actual self-file creation identity. These methods require the corresponding valid log graph; they are not general missing-log handlers.

`moHeader_c::setCreationTime` at `0x31a05ec0` applies:

1. If `C != R` and `C != -1`, leave this creation identity unchanged.
2. If `C == -1`, choose `Cnew = R`.
3. Otherwise choose `Cnew = _time64(NULL)`.
4. Store `Cnew` in `f70` and pass it to the self object's `setTimestamp` when that object exists.

It does not change `R`. Therefore `C == S` with `C != R` is an explained native state. The setter can produce it; this does not prove that the source author reached this particular setter.

`resetCreationTime` at `0x31a05b30` differs: a supplied time changes the first event as well as `C` and the self identity. With no supplied time it derives the creation identity from that first event. `sanityCheckAndSetCreationTime` at `0x31a05c90` repairs nonpositive creation identity from the appropriate log/current-time branch.

The self setter at `0x31a01f60` compares the current shared record, creates a replacement shared definition when the time changes, and calls `hashNewFileRecord`. It is not merely a blind in-place assignment to every shared alias. A future fresh constructor must preserve its own actual identity relationships rather than imitate a native pointer update.

The version-19000 header load has a separate context branch:

| Native helper state | Bound behavior |
| --- | --- |
| Helper `+0x2c == 1` | If the revision graph is present, call `setCreationTime` and record the old/new creation mapping |
| Helper `+0x2c != 1`, self creation equals `C` | Leave `C` and the first event alone |
| Helper `+0x2c != 1`, self creation differs from `C` | Repair `C` from the first root event and apply that identity to the self object |

The corresponding store branch writes the first root event in helper mode 1 and writes member `f70` in the other current-version path. The semantic enum name for mode 1 and its exact selection by ordinary Open/SaveAs remain unproved here. It must not be labeled a copy/save mode by assumption.

## Archive time `f50`

Let `M` be runtime header `f50`, `C` creation identity, `N` a new wall-clock sample, and `U` native unset time. The bound store code applies this conditional formula:

- If `local_year(M) != local_year(U)`, preserve `M` through this branch.
- If archive condition `0x80` is present, preserve `M` through this branch.
- Otherwise, when zero-based local month of `M` is zero, choose `N`.
- In the remaining sentinel-year month branch, choose `C` when `C != -1`, else choose `N`.

The month/year offsets are independently corroborated by `su_CTime::GetMonth` and `GetYear`, and `GetLocalTm` resolves to `_localtime64`. The formula depends on local calendar state; it is not an unconditional constant or universal chronology repair.

There is no `M >= C` comparison in this complete serializer. That proves the selected serializer does not enforce the current constructor ordering rule. It does not prove that every upstream native caller admits arbitrary chronology.

`moHeader_c::getLatestModificationTime` at `0x31a05250` does not read `f50`. It selects the greatest signed event time among the tail stamps of nonempty revision logs. The current `ModifiedAt` name is not sufficient reason to substitute `f50` for that getter's result.

`updateRevisionLog` at `0x31a06330` locates the matching log id and appends the supplied stamp when it is not already present and has the required runtime class. It does not synchronize `f50`. `moStamp_c::updateStamp` changes its own status, comment and wall time, independently of the header clocks.

## Update and version history

For version 19000, header `f48`, `f50` and `f70` all have explicit serialized values. Loading a header counter of 101 temporarily samples wall time into `f48`, but the later version-qualified read overwrites it with the saved `f48`. That temporary assignment does not establish the final loaded update time.

`moVersionHistory_c::fileCreated` at `0x4c720800` receives the header to obtain actual user/company indices. It calls the `moStamp_c` constructor on the newly allocated version state with status zero and no comment. That constructor samples `_time64` into its own `f18`; it does not copy header `f48`, `f50` or `f70`.

The History and Header codecs are independent. Current SDK fresh composition makes their initial clocks equal as a construction policy. The read/write layouts do not contain a cross-stream equality requirement. Version/date-code provenance and its unresolved high flag remain independent of this clock finding; this note supplies no authenticity or license-derived generation rule.

## Already-disclosed observations

The [metadata reduction](../measurements/2026/DrawingSourceEpochObservation01.json) retains all eight pairs and the 20 exact source fingerprints. Its source is root's immutable intake04, SHA-256 `a25475ec393ded731ec197a03db54863973841230be0c870b862753d5fa807df`. No native CAD payload was reopened for this reduction.

| Native child | Header `f70` | Header `f50` | Header `f48` | First root event | First history event |
| --- | ---: | ---: | ---: | ---: | ---: |
| D01 | 1795013932 | 1794529625 | 1795013942 | 1794529623 | 1794529625 |
| D02 | 1795014217 | 1794529625 | 1795014227 | 1794529623 | 1794529625 |
| D03 | 1795014533 | 1794529625 | 1795014542 | 1794529623 | 1794529625 |
| D04 | 1795014821 | 1794529625 | 1795014832 | 1794529623 | 1794529625 |

Every row's actual self creation equals its header creation. All four have `f50 < f70`. Their drawing headers and root/history clocks are separate owners, also retained in the JSON. These measurements are source evidence, never future generator constants. No inference that their equal history/`f50` values are required is made.

The four replay06 generated pairs use the constructor's coupled root/history creation times and independently modeled modification/update/save times. Their earlier measured acceptance does not transfer to a newly split clock input.

Feature `f2a0/f2a4` FILETIME words are a different representation and lifecycle. Existing source observations include nonuniform subsecond words. This work does not explain every native feature-time update or replace those words with a header epoch.

## Frozen discovery proposal

The [structured plan](../../tooling/sw2026/DrawingSourceEpochProbePlan01.json) uses four new linked pairs and independently chosen geometry and clocks. It is a frozen proposal, not an executable packet or an emitted candidate.

The common child creation epoch is the new modeled value `1760000123`. The baseline has later archive time, a distinct update time and equal initial root/history event times. Each other case changes exactly one clock axis: archive time before creation, first root event before creation, or history event after creation. The drawing clock domain remains fixed, and self creation remains equal to header creation. Feature dates and the origin's own `DatumTime` are not silently replaced with the varied root/history values.

A private discovery composer must apply this clock model to actual fresh typed nodes before final stream emission. It must re-emit the complete linked graphs with shared SDK codecs, retain both header identities and the real self alias, and construct history from the explicit model. It must not edit saved bytes, read a vendor file, change current production guards or promote a copied event table.

The minimum proposed native batch has 18 fresh processes: two healthy controls and four lifecycle phases for each of four cases. The depth edit and view movement have independently declared values. Exact trees, all live dimensions/relations, analytic solid measures, real displayed origin, model/configuration link and separate fresh reopen must pass. Typed host comparison records all clocks and every history/log state after each saved phase.

The observer uses ordinary documented COM modeling/inspection APIs. It does not hook a native setter. A changed saved clock is therefore a phase-wide result until a specific caller is independently proved. Operation wall-time bounds are recorded for diagnostics; OS filesystem times never substitute for archive times.

## Remaining boundaries and attestation

- Native high-level load/save caller selection for helper mode 1 is not closed.
- The complete semantic purpose and every upstream writer of `f50` are not closed by its sentinel repair.
- Arbitrary split clocks have no new native measurement yet.
- Source style, provenance/history flags, naming and out-of-plane dimension text remain separate constructor refusals.
- Feature FILETIME scheduling, arbitrary external histories and other versions are outside this tranche.
- No hidden input, VM, CAD application, codec/schema execution or product test was used in this phase. No shared worktree or public admission changed. Native and held-out acceptance remain false for the proposed expansion.

The mandatory CAD stopping conditions remain: “The first is success under every criterion on this page.” and “The second is the end of the available context.” This bounded evidence handoff does not declare the broader CAD goal complete.
