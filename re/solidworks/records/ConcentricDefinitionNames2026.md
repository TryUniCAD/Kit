# Resolve linked part labels from the owned file

Task `B04-SW2026-MATES-CONCENTRIC/linked-definition-name`, owner `assembly_frontier`, delivery PR #121. The normal D01 SDK read exposed `ConcentricD01AlignedFree` for both the assembly and its resolved `ConcentricD01Child.SLDPRT` definition. The bounded correction projects `ConcentricD01Child` for the part and retains the original index label in `native_attributes`. [Reader](../../../src/convert/adapters/solidworks/Core/Adapter.py)

## Linked owners

`swModel.swFileRef` identifies the actual file owner independently of the model index's `swName`. On D01, the selected parent model and the child model both store `swName="ConcentricD01AlignedFree"`. The part file owner is `ConcentricD01Child.SLDPRT`. Both `moAssembly_c.f68` occurrences lead to `moReference_c.f3b0` records whose complete typed file keys agree with each other and with the actual child's ModelHeader `f38`. Their persistent feature IDs agree with those in the component index. The child's own `moPart_c` is `ConcentricD01Child`. The parent model's internal title is `Assem1`.

| Disclosed pair | Root model index label | Child model index label | Typed child file and model owner |
| --- | --- | --- | --- |
| D01 native source | `ConcentricD01AlignedFree` | `ConcentricD01AlignedFree` | `ConcentricD01Child.SLDPRT`, `ConcentricD01Child` |
| Native-saved radial pair | `RadialConcentricProbe` | `DisclosedRadialSceneProbe` | `DisclosedRadialSceneProbe.SLDPRT`, `DisclosedRadialSceneProbe` |
| Guarded generated occurrence discriminator | `ConcentricD01AlignedFree` | `ConcentricD01AlignedFree` | `ConcentricD01Child.SLDPRT`, `ConcentricD01Child` |

The disclosed A13/A14 and synchronized-save indexes already exhibit the mirrored-label form. The shared writer intentionally serializes the root filename stem in both index model rows for this format form. The normal public reader applies the correction only to the version-19000 resolved direct external part in this two-definition shape when the two labels mirror the indexed assembly filename and the resolved part basename agrees with its own file row. Distinct saved definition labels continue to name the portable definition. [Prior archive roles](AssemblyInstanceTree2026.md) · [Index constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Assembly/Xml/MakeAsmTree.py) · [Guarded generated control](ConcentricOccurrenceNumbers2026.md)

## Guarded public process comparison

The read replay uses Python 3.11 in sixteen fresh SDK processes. The before source snapshot is `862d575c82d325c27b345456ecc4ec45e807455f`. The after snapshot substitutes only `Core/Adapter.py` by hash. Each worker passes the hash-checked input paths to the normal reader, denies CAD opens outside the declared parent/child pair, and denies process and network calls. The D01 default and metadata-only reads and the guarded generated default read change only the affected definition label and the derived source semantic seal. The actual occurrence names, reference numbers, selected definitions and mate status agree exactly. For D01 both read modes still admit the solved mate.

The native-saved radial read and a synthetic diagnostic with a distinct `swName` have equal before/after documents. The diagnostic changes only the component index of the guarded generated control and is used only as reader input. Disabled component resolution, strict missing-child refusal and non-strict `sldasm.component_source_missing` reporting also match exactly. All original input bytes retain their hashes. The existing process regression now checks both the portable label and the retained raw index label. The host replay started zero native processes and read zero held-out inputs. [Sanitized read receipt](../measurements/2026/ConcentricDefinitionNameRead01.json) · [Existing process regression](../../../tests/Convert/Solidworks/Research/Assembly/XmlIndexTests.py)

The D01 source still lacks complete portable mate-group and body ownership, and whole-source presentation and topology transfer remain open. [Source admission boundary](ConcentricSealedAdmission2026.md)
