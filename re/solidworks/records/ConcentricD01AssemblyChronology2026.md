# D01 concentric assembly revision and feature chronology

Task `B04-SW2026-MATES-CONCENTRIC/source-chronology` in PR #121,
owner `assembly_frontier`, base
`4f3fe8ee989b7df7b15c9b87c29793617047e1aa`.
The source pair is the already disclosed D01 Source and Edited
assembly and their respective cylinder parts in the 2026 SP05.2
`34.5.2.0604` source lock. This analysis advances the
[existing saved context construction](ConcentricSavedCmgrModel2026.md)
under the [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
The next exit remains complete source admission and independently
controlled native proof on the resulting model.

## Actual ownership

| Field or stream | Disclosure and construction |
| --- | --- |
| ModelHeader and Header2 | Both identify the actual `moAssembly_c` and resolve the same creation identity and self save event. The model and configuration each use ID 0 in separate namespaces. The model owns the revision log. |
| Header `f70`, `f50`, `f48` | File creation 1795044311, archive timestamp 1794529626, update time 1795044315 then 1795044345. The three typed inputs remain independent. The output's self file derives its creation key from the generated header and save time from the explicit destination epoch. |
| `moLogs_c.f48/f50` and `moStamp_c` | Both source headers contain 26 ordered logs with 30 created/modified events. The live model, resolved roots, nested lights and note markers, direct occurrences and separate mate stream establish the owners. A log contains the actual owner's allocated ID and its independent caption. The actual root log caption is `Assem2`, with an earlier model title `Assem1` and a distinct current title `ConcentricD01AlignedFree`. Attribution indices derive from the actual user and company tables. |
| Feature `f2a0/f2a4` | All 26 feature and mate objects have nonzero instants unchanged across the edit. Whole seconds and fractional 100 ns ticks reproduce both signed words. The exploded manager has an instant and no revision log. The model itself has a revision log and no feature instant. |
| VisualStates `f78[].ref.ff0` | The three native plane references use actual generated plane IDs and each plane's agreeing first revision event from both headers. Top Plane is source ID 4 and generated ID 13. Moving its first event alone leaves its FILETIME unchanged. |

The [standalone chronology rules](PartChronologyConstruction2026.md),
[creation-log caption evidence](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/CreationLogDocumentNames.md)
and [visual creation-log rule](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/VisualFeatureRefsUseCreationLogs.md)
establish the shared wire fields and their ownership.
The constructor receives semantic names, captions, ordered revisions
and feature instants. Its joins use actual role, concrete class and
name, then take persistent IDs from the newly allocated model.
For example, the source cabinet ID 2 maps to the new cabinet ID 11.
No source archive mapping or saved record is included in the writer
request. The exact source comparisons independently reconstruct each
of the four source headers' revision subgraphs and verify complete
Header writer replay.

## Guarded composer and result

The ordinary fresh assembly recipe still passes `CheckAsmMeta`.
That entry's Header, system and History time seed is intentionally
coupled. The research composer uses the same model, Header,
occurrence and concentric constructors with separate Header clock
intent. It preserves the existing system and version-history inputs
and binds the actual Header file identity before constructing
current references. The edited parent goes through `EmitAsmStreams`
and the shared container writer, with independently computed
VisualStates composed alongside the already proved saved context.
The public writer and original-source admission remain unchanged.

| Comparison | Result |
| --- | --- |
| Earlier saved-context control | Whole parent SHA `232e6a2423d91dd25e1752acf837ab5dcaad443ae71b13dfebbca5b445335ca8` reproduces exactly. |
| Modeled chronology | Two fresh stdin-only workers agree on the complete 11,908-byte parent SHA `d30a40ca8d0b96192c66da436d58addb03021c3d8369c17b55f834b1b71c8b39` and unchanged child SHA `59dcf1090455da469bf5b003f9854a3f13937cafab8c1bb9321862fdca72d408`. Zero audited runtime external accesses. |
| Linked native-format owner readback | Exact Config-0, Resolved and MatesList replay. Same aligned, free mate and signed negative-Z endpoints, both on the constructed child lateral face 6. Fixed/floating order, signed extent of about -46.91 mm, child display key 1 and historical contexts are retained. |
| Independently moved revision event | Changing only Top Plane's first event from 1794529626 to 1794529619 changes just the two parent Headers and VisualStates. The complete contrast SHA is `54b993c93c48a72c0a103ab3c0ef1451a44a9b50698ec1de6d565b60b99290c3`. Its signed geometry, fixed flags, child, and three linked streams are identical. |
| Refusals | Duplicate and omitted log owners, model root as a feature instant, invalid fraction, disagreeing peer Header log and unowned child display. |

The [hash-bound result](../measurements/2026/ConcentricD01AssemblyChronology01.json)
lists source and output hashes, owner IDs, precise instants, changed
streams and refusal results. It excludes personal author/company
strings, comments, source locator text and native files.

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01AssemblyChronology.py \
  --disclosures /absolute/path/to/Oracle121Takeover
```

## Unresolved original-source scope

The source's `CheckAsmRoot` still refuses unprojected root content.
The source header update counter advances from 105 to 106 and root
geometry stamp from 102 to 103. The ordinary generated fresh seeds
remain 101, with a separately computed assembly manager geometry
stamp. These are allocation and update stages, distinct from the
modeled wall-clock events above. The experiment preserves the
generated Header2 model-presence policy, whereas both saved headers
have presence 1. It makes no claim about treating that difference
as a valid source transformation.

The generated fresh Biography and History keep their earlier
values. The native 1,639-byte Biography changes during the edit
and the native 101-byte History remains unchanged. The 43 native
parent streams include 30 additional stream names absent from the
generated 13-stream parent. The receipt inventories them explicitly.
Original document and configuration XML properties, attachment and
linked-document state, and independently owned metadata still need
classification and source admission. Preview, display-list and
tessellation caches need separate native closure. The modeled
chronology imposes no new acceptance or held-out credit.

The subsequent [property owner proof](ConcentricD01PropertyOwners2026.md)
constructs four additional property streams and keeps this chronology
and all prior parent and child bytes exact.
