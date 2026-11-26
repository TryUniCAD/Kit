# P03 generated Boss independent SDK readback

## Pinned inputs

| Input | SHA-256 |
| --- | --- |
| Saved P03 baseline, 44,796 bytes | `db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357` |
| Saved constructor request | `d460d8352b7e34526a5e95d451d5671454d8b30d8ef96e5adf90111d67812a49` |
| Generated Boss, 33,844 bytes and 32 archive members | `a0e524cc73b844042c7da6bf86b3a12120fb4f73aaf34de7f0d6cc481ebda15f` |

The [candidate implementation](https://github.com/TryUniCAD/Kit/tree/b119a6710d8466e99654c76fcd197a2225e6eb7f/re/automation) emitted the archive in a fresh Windows Python 3.14.6 process in 7.684 seconds. Its file read audit observed only the persisted request and the packaged layout schema as data inputs. The original source SHA-256 was unchanged by every read. The candidate had the same digest before and after each read.

## Independent read and comparison

The reader was SOLIDWORKS SDK revision [c0a401a607](https://github.com/TryUniCAD/Kit/commit/c0a401a607759fb0c2589647c2a22af65ebb7ce1). Each row came from a separate process through `convert.open_document`. The two strict refusals came from [BrepPayloads](https://github.com/TryUniCAD/Kit/blob/c0a401a607759fb0c2589647c2a22af65ebb7ce1/src/convert/adapters/solidworks/Core/Reading/ReadAdapter.py#L4356-L4383). No document was returned on refusal.

| Input | Public options | Result | Document SHA-256 |
| --- | --- | --- | --- |
| Source | Defaults | One B-rep, three retained partition or delta payloads and no diagnostic-list entries | `71efc66275e523a1e8bae05fe0a0dce3e3be0ef9ee59b1800d25e3a96ef11d6c` |
| Source | Strict, no B-rep or tessellation | One body, no B-rep or payloads and no diagnostic-list entries | `9b83c1c196bf86e6012706d8dc5fa174a6c28ada84d07ef5cf00e68c68373582` |
| Candidate | Defaults | `SLDPRT contains no readable Parasolid payload` | None |
| Candidate | Strict, B-rep enabled, tessellation off | Same refusal | None |
| Candidate | Strict, no B-rep or tessellation | One body, no B-rep or payloads and no diagnostic-list entries | `22db547366b21f72b30539c53e78fb1eefb4864aaab102b28be119284bb0cade` |
| Candidate | Lenient, B-rep and tessellation requested | Same document bytes as strict design-only | `22db547366b21f72b30539c53e78fb1eefb4864aaab102b28be119284bb0cade` |

The same two strict design-only JSON documents were passed to the existing [semantic graph comparison](../../automation/SemanticComparison.py) with declared millimetres and zero tolerances. The ordinary candidate checkout exited 1 when the older model rejected the reader's `OutputBodyIds` field. In a separate isolated process the exact reader's document model and codec were loaded first. The unchanged comparison code then exited 2 with `different`. No source fields were removed or normalized between these invocations. The complete comparison SHA-256 is `8856a6ae12aee8aa328b02dec59696ef1279856429c8b6a89898a3e09ecb15ef`. Its tolerance JSON SHA-256 is `6103b9fdeabcf31c36d6bcd74ae43b2c570405aa70087cba8820fb9bb564de40`.

Each graph has 57 nodes and 1,044 tracked fields. All nodes paired with zero unmatched or ambiguous. Each graph retains 188 unresolved entries. They include 56 extension fields, 23 uninterpreted native values, 51 unclassified references, 25 native-only definitions, 25 retained native byte records, six confidence gaps, one independent source-domain gap and one unresolved selection. Four reported reference differences concern the two `N_Axis` selection nodes and their name-based `RectangleSketch` target. There are also paired field differences, including retained record hashes. The 25 definitions remain unresolved on both sides. Matching counts do not establish preservation of their semantics.

## Observed record roles

The source uses rectangle feature 26 and Boss 34. The candidate uses rectangle 57 and Boss 71. Each Boss references its own rectangle and a linked 10 mm positive blind depth. Both SDK Boss operations read as Join. The constructor's prepared Create operation remains a separate input observation. No licensed measurement established Join/Create equivalence.

The rectangle on each side uses Front plane 2, four horizontal or vertical axis relations, four inferred corner aliases and a separate fixed proxy owned by Origin feature 5. The 20 mm driving height uses the left edge from its end to its start. The 40 mm driving width uses the bottom edge from its start to its end. Both driving dimensions belong to the owning rectangle, and the saved coincidence links the independent Origin to the bottom edge start. These typed record bindings are direct observations for the two pinned inputs.

The existing [source order witness](../../automation/P03ConstraintGraph.py) passed the source and refused the candidate. The strict public source tuple projects height before width and the candidate tuple projects width before height. The physical distance blocks on both sides have width at frame 7436 and scalar 7509, then height at frame 7613 and scalar 7665, in `Contents/Config-0-ResolvedFeatures`. Their native point IDs agree.

The cause is the separate `swXmlContents/KeyWords` order. The source stream is 1,763 bytes with SHA-256 `35ab5ede7905ea3f0562195f1ff2d6dedd91cd5d431768f619601ce74536ff48`. The candidate stream is 1,783 bytes with SHA-256 `1100ee74c413cb9bea3703119d13b4452b32e4a5c5444f25aa76e184445c14cd`. The pinned reader's `ParseKeywords` returns height before width for the source and width before height for the candidate. [The keyword reader](https://github.com/TryUniCAD/Kit/blob/c0a401a607759fb0c2589647c2a22af65ebb7ce1/src/convert/adapters/solidworks/Core/Native.py#L1895-L1945) retains XML child order. [BindRectDists](https://github.com/TryUniCAD/Kit/blob/c0a401a607759fb0c2589647c2a22af65ebb7ce1/src/convert/adapters/solidworks/Core/RectDistances.py#L104-L142) then binds exact inline rows by name without changing the existing rule order. The candidate fixture author chooses width first in [PackageXmlState](../WriterResearch/VerifyFreshBoss.py#L353). [PackageIndices](../WriterResearch/PackageIndices.py#L94-L113) already supports either keyword order. This isolates an existing presentation input for further work. It does not justify changing inline bytes, identifiers, display records or member slots.

Both archives' typed resolved reports retained `unsupported SOLIDWORKS body class moSimpleSurfIdRep_c schema 1`. The candidate has no recognized Parasolid payload and 19 actual members outside the 13-name allowlist for [analytic no-cache reconstruction](https://github.com/TryUniCAD/Kit/blob/c0a401a607759fb0c2589647c2a22af65ebb7ce1/src/convert/adapters/solidworks/Core/TypedResolved/Geometry/IsCacheAbsent.py). The predicate returned false for that candidate, and for the source with saved partition payloads. The retained per-role witness SHA-256 is `3db986d2c3858a3572a8c41d0755555b2a3173cf550ab5412df58c9067677be5` and binds all 25 native definitions per side, the 11 ordered relations and the archive-member checks. These are independent reader boundaries. No admission rule was changed to obtain an output.

## Qualification

The observed keyword-to-rule relationship is pinned to these exact read and record results. Broader projection and analytic reconstruction remain unqualified. The generation and SDK comparison used no vendor application and made no model calls. The default strict refusal, unresolved history, native rebuild and save/reopen, independent held-out evidence and public conversion qualification remain open. [Reproduction procedure](../../../Documentation/Changes/Research/Encoder/ConstrainedBossSdkReadback.md)
