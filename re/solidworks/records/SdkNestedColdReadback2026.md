# Cold SDK readback of disclosed nested SOLIDWORKS bundles

| Ownership | Scope |
| --- | --- |
| Task | PR #121 nested assembly output readback |
| Owner | `/root/release_path` |
| Reader | `bd835aab5fc01426976b2e2792129d806116dfc9`, source tree `a207312f5b355adf422edcec68a0fd9f260c5397` |
| Inputs | The seven hash-locked `FrozenGenerated` files from `SdkNestedNeutralNative03` and `SdkRepeatedNeutralNative03` and their original neutral requests |
| Exit | Confirm editable geometry and linked occurrences through the default reader, locate projection gaps and exercise strict re-export refusal |

Seven isolated Python processes called the normal `convert.open_document` entry
with its default strict, B-rep and tessellation settings. Each worker validated
the resulting neutral document and decoded the actual ModelHeader, Config-0 and
ResolvedFeatures chain. The process guard allowed data reads only from the
frozen files declared for that bundle and blocked writes and external programs.
Every source hash matched before and after. This audit used no native processes
or private inputs. The prior SP05.2 native open, rebuild, edit, save and reopen
results remain evidence for these independently authored neutral recipes.
[Earlier native result](../measurements/2026/SdkNestedNeutralNative01.json) ·
[Readback receipt](../measurements/2026/SdkNestedColdReadback01.json)

## Assembly ownership

| Opened assembly | Definitions | Direct occurrences | Expanded depths | Root order, observed / authored |
| --- | ---: | ---: | --- | --- |
| Simple Frame | 3 | 1 | 0, 1 | 1 / 0 |
| Simple Module | 2 | 1 | 0 | 0 / 0 |
| Repeated Frame | 4 | 3 | 0, 1, 1, 0, 1, 1, 0 | 2, 3, 4 / 0, 1, 2 |
| Repeated Module | 2 | 2 | 0, 0 | 0, 1 / 0, 1 |

Definition membership, direct relative order, physical child paths, selected
configuration names, occurrence flags and expanded instance IDs match the
neutral graphs. The repeated instances share the one module definition and
independently reuse the actual leaf definition by path and SHA-256. Every direct
occurrence in the physical assembly is associated with its owner-local
`moAssembly_c.f68` `moReference_c` entry. Its `f08` matches the XML occurrence
feature ID, `f3b0` matches the full file key of the exact child ModelHeader
`f38` and `f3c0` selects the child's active configuration. The typed `f360`
rigid transform is exact. The maximum public local and composed homogeneous
matrix component difference is `5.551115123125783e-17` with translation in mm.

Both Frame reads expose all definition captions as `SdkFrame`. The nested
index's `AddTargetModels` and `XmlModelAttrs` use a shared root caption for
`swModel.swName`. `Assembly.Models` imports that caption and numbers placements
globally across model elements. The standalone Module's existing two-definition
`AsmDefinitions` normalization recovers the leaf caption. Each actual
`moAssembly_c` and `moPart_c` already holds its own authored title through
`f18`. A general correction can bind that title and the native child
configuration only after correlating the typed occurrence, index reference and
actual linked header. A file stem alone cannot establish the caption.

The XML edge and definition configuration IDs are the native string `"0"`.
The linked document's active configuration has public ID
`sldprt:configuration:0` and a typed `native_configuration_id` of zero. The
selection of `Default` or `modeled default` agrees with the original request.
The two ID representations remain distinct in the readback returned to writer
preparation. The parent view includes a unified definition graph and an
embedded Module document with its own direct occurrence index. That inspection
document defers leaf resolution. The containing Frame resolves the one physical
leaf once, and opening Module independently resolves the same file. This
explains the extra embedded subassembly document that the neutral builder
declines.

## Rectangular leaves

| Leaf | Driving depth (mm) | Volume (mm³) | Area (mm²) |
| --- | ---: | ---: | ---: |
| Nested Plate in each bundle | 7.45 | 3489.784875 | 1607.355 |
| Gauge Plate | 10.85 | 5100.937625 | 1888.555 |

All three leaves retain the four ordered lines, actual Front Plane frame,
closed loop, zero constraints, unchanged typed blind direction and own editable
D1. The neutral B-rep generated from the linked profile and depth belongs to
the same one design body ending at the typed boss. Independent rectangle
dimensions reproduce the volume, area, bounds and counts of one solid, one
shell, six faces, twelve edges and eight vertices.

The source step uses `create`. The extracted step uses `join`, which
`TimelineOp` takes from the native operation kind without considering an
initial one-solid producer. `RequireBossDef` expects the ordinary creator.
The public body caption is `Solid Bodies` and the typed producer retains
`Boss-Extrude1`. `BuildPrismGeom` returns the ordinary cached-free geometry
without a producer attachment or explicit cold body name. `WithColdName`
therefore has no owner from which to derive a replacement, and the persistent
body name helpers do not select this capsule.

## Re-export boundary

Implicit same-format writing finds no supporting writer. Explicit public
same-format writes for all seven files and the four internal nested calls
reach `CheckNative` and refuse the retained native-only timeline. No call
publishes a destination. Assembly public timelines keep 17 to 19 native-only
rows and parts retain 18 alongside the typed boss. The explicit physical
linked decode succeeds on both root models, while the public typed report
keeps `full_linked_graph` false. The part-oriented `ProjectTree` needs
`moPart_c` and does not qualify the assembly tree. Assembly component
feature IDs are legacy-only in that report even though their own typed
reference nodes are available. Older native name diagnostics still report
the Lights and Cameras record and some assembly occurrence records.

On untouched documents, nested preparation declines the assembly timeline,
diagnostics and native mate-list payloads. The exact empty mate lists remain as
six-byte payloads in the inspected documents. The default XML has no display
state declaration, mesh or projected assembly display owner in this cohort.
This establishes no display support for populated sources.
`CheckAsmDef` separately refuses cached or external definition state.
`ReadNestedLeaf` first refuses native configuration attributes.
`PlanPartWrite` refuses part diagnostics and source attributes, and the
ordinary blind projection independently refuses the reconstructed B-rep.
The returned default documents also retain source hashes, bytes and other
provenance and inspection metadata.

Model these domains and reconcile typed ownership before attempting cold
native-to-native publication. These measurements retain all original reader
state and establish neither a new public write profile nor held-out coverage.

Run from a worktree with the pinned source tree and an unused receipt path.

```sh
python3.14 -I -B re/tooling/sw2026/nested_publication/MeasureNestedReadback.py \
  --workspace /path/to/disclosed/Oracle121Takeover \
  --output /tmp/SdkNestedColdReadback.json
```

## Verified nested index ownership

The normal resolved reader now binds the complete index to the physical header
keys, typed active configurations and actual reciprocal occurrence features.
The four nested root reads recover five mirrored captions and eight local
placement ordinals. The disclosed sources include two original SOLIDWORKS
2026 native saves, with healthy prior controls, and two generated bundles.

The before-and-after comparison changes only the measured definition names,
placement ordinals and their dependent source semantic fingerprint. The four
standalone assemblies and all deferred reads match the baseline. Each root
refuses missing and crossed physical child data, a foreign selected
configuration and feature ID, and an inconsistent local placement. All
eight resolved inputs still refuse original-source writing without output.
[Change entry](../../../Documentation/Changes/Solidworks/Reading/Assembly/SolidworksNestedIndexOwnerReadback.md) ·
[Guarded result](../measurements/2026/SdkNestedIndexOwnerReadback01.json)
