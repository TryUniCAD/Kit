# SOLIDWORKS 2026 drawing concept prefix

The ordered sheet and model-view graph can be recovered before the drawing model's resolved tail. `moDrawing_c::Serialize` calls the shared model serializer at `0x4c95d388` in `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Its current-version calls at `0x4c224e7b` and `0x4c224e8a` dispatch slots `+0x4b8` and `+0x4c0` for lightweight and resolved data. The resolved method first calls the context wrapper at `0x4c2341d0`, which invokes `moConcept_c::SerializeResolvedData` at `0x4c17baa4`. The native concept ends after its counted resolved node list and list trailer.

The [prefix process](../../tooling/sw2026/serial/CheckDrawingPrefix.py) follows those methods through that boundary. It consumes the common Definition prefix, inline model header, complete lightweight method and first resolved concept method. The list owns the single sheet and the sheet owns its complete view nodes in native list order. Any discovered view has already consumed its full archive body when the reader reaches the concept boundary. The prefix treats the later active sheet pointer separately. The first profile uses a single sheet. The [full Definition check](DrawingDefinitionGrammar2026.md) independently verifies that pointer aliases this sheet in all three controls.

| Disclosed case | Consumed bytes | Next archive slot | Reached methods | Registry methods marked provisional |
| --- | ---: | ---: | ---: | ---: |
| `D00EmptySheet` | 5,919 | 119 | 96 | 0 |
| `D01FrontView` | 11,235 | 178 | 115 | 5 |
| `D02MovedFrontView` | 11,245 | 178 | 115 | 5 |

These positions are measurements. The reader consumes native tags, string lengths, class counts and the actual node list. All three prefixes re-encode exactly in memory with identical final map indices. The view orientation name, scale numerator and denominator, and all thirteen model-to-view transform values come from `moAbsoluteView.f1018`, `moDrView.f780/f788` and `moDrView.f5e0`. The model reference points to the same inline-header directory object and carries the actual configuration name. [Prefix receipt](../measurements/2026/DrawingConceptPrefixCheck01.json)

## Shared reference dependencies

All five provisional registry entries from the part view were traced in the pinned binary. These are wire observations in the disclosed front-view path. Other parent types or flag branches require separate evidence. The registry retains its broader provisional designations.

| Wire owner | Applicable reader framing | Evidence |
| --- | --- | --- |
| `moChainComponent_c` | Shared component body, an archive pointer to the chain, then its unsigned state word `f30`. | Entry `0x4c21b8c0`, base call `0x4c21b8ef`, write `0x4c21b908` and `0x4c21b913`, load pointer `0x4c21b940` |
| `moReferenceChain_c` | Mode word, flags under the native condition guard, external-feature-list pointer, integer `f20` and inline selected configuration. Consume the integer even when its lifetime value is unused by the neutral projection. | Entry `0x4b66e370`, store at `0x4b66e429`, `0x4b66e4a8`, `0x4b66e4b3` and `0x4b66e4c4` |
| `moExtFeatureList_c` | Current format count and that many object tags. Native ordinary drawing uses the shared non-database object map. | Entry `0x4c1784f0`, count load `0x4c178764`, object load `0x4c17879f` |
| `moExtObjectInterface_c` | Inline shared file definition and configuration, byte flags and feature identifier, then a pooled archive name handle in this context. | Entry `0x4c179410`, name store `0x4c1794b9`, shared-file load `0x4c179500`, current name load `0x4c179684` |
| `moExtFeature_c` | Shared interface body, archived feature object followed by a trailing integer at this archive version. | Entry `0x4c178a30`, interface call `0x4c178a98`, reference load `0x4c178cb7`, trailing load `0x4c178dde` |

The drawing chain is entered by a `moCompRef_c` within the view's geometry references. In the disclosed view the chain names one external feature. Its reference backlink already allocates the `moReferenceInternal_c` later used by the view. This ordering requires a shared archive map throughout the prefix. The observed lifetime state `f20` in D01 is 49. The assembly chain's ordinary fresh construction value is a separate context. This record supplies no drawing writer value for that state. [Assembly reference context](OrdinaryOccurrenceConstruction2026.md)

The common tag, count, string and map loops live in the SDK archive primitives. The fully typed current `Header2` decoder can consume the drawing model's inline header through those same primitive callbacks. The remaining classes in this prefix include default units, common model properties, feature concepts, the profile and sketch graph, and the drawing sheet and view owners. The older layer and display manager rules reached later in the complete Definition are outside this prefix.

## Independent view cache check

The sheet and view bucket serializers invoke the inline graphics list under `uiViewBucket_c.f10` then `gcBucket_c.f6c8`. The owner is `suDynList<uoDisplayItem_c>::Serialize` at `0x3c805c80` in pinned `sldmfcu.dll` SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`. At this prefix, both normal bucket types carry two type-9 pen records, framed by a native list count. The sheet bucket then stores native paper height and width as doubles. The view bucket stores a centring transform and a paper placement transform before its first outline. The outline and position agree with Header2 and the native object graph on both disclosed views. [Display restore context](DrawingSdkInspection2026.md)

The prefix validates the read projection beyond the SDK's header and XML inspection. Whole-document strict reading, application geometry, editing and generation remain unqualified. Held-out source payloads remain sealed.
