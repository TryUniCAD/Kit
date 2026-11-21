# Typed ownership of rigid nested SOLIDWORKS assembly tree rows

| Item | Boundary |
| --- | --- |
| Task | PR #121, `B04-SW2026-NESTED-PUBLICATION`, native readback tree ownership |
| Owner | `/root/release_path` |
| Reader | `42878d802e4d53ba1dd92528a67fa8122880cff0`, source tree `8ec147cb733526d1b281923bf3350e15f91c77e3` |
| Sources | Public native originals N01 SingleFrame and N02 MixedFrame, plus the two previously measured SDK Frame roots |
| Exit | Match each public native-only row to an actual typed owner and each measured native row to a proven parent or default role |

Four fresh Python SDK processes matched all 86 public native-only rows and
all 96 observed native feature rows. The native observations come from the
existing SOLIDWORKS 2026 SP05.2 controlled runs on the exact same inputs. The
probe binds the source author records, independent neutral requests, saved
file identities, native observations, reused proof tools and reader revision
by digest. Each worker uses the normal strict `open_document` route and can
read only its hash-verified disclosed closure. The archive inspections then
consume those same verified buffers. All fourteen file instances kept
their original hashes. [Exact receipt](../measurements/2026/NestedAssemblyTreeOwners01.json) ·
[Original source observations](DisclosedNestedAssemblyArchiveAudit2026.md) ·
[Generated native observations](SdkNestedAssemblyConstruction2026.md)

## Confirmed tree ownership

| Root | Resolved roots | Authored direct occurrences | Stored visible members | Runtime member rows | Index-only manager | Public native-only rows | Native visible rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| N01 SingleFrame | 16 | 1 | 6 | 0 | 1 | 24 | 23 |
| N02 MixedFrame | 16 | 3 | 6 | 0 | 1 | 26 | 25 |
| SDK simple Frame | 16 | 1 | 0 | 6 | 0 | 17 | 23 |
| SDK repeated Frame | 16 | 3 | 0 | 6 | 0 | 19 | 25 |

- The 16 linked roots are the existing ordinary folders, cabinet,
  environment, three principal planes, origin and empty mate group. Both
  originals and both generated roots have the canonical three plane
  frames. Each origin is the actual zero point on its linked front plane.
  The six-byte MatesList continues the exact resolved map and has zero
  members for all eight physical assembly definitions. The public mate
  groups and mate constraints are empty in this profile.
- All eight direct root `Reference` rows are authored occurrences. The
  native timeline representations repeat intent already carried by the
  semantic assembly instances. An occurrence joins its actual
  `moAssembly_c.f68` row through persistent ID and the external-feature
  backlink. Its actual directory entry aliases one local Config-0 slot
  carried into ResolvedFeatures. Directory slot identity is distinct from
  the object's original ModelHeader index. The target file key equals
  that of the verified child header.
- Four real Config-0 environment children and two real resolved cabinet
  children account for six of the seven extra saved index rows in both
  original roots. Their stored typed spans lie within the proper owner.
  The two saved note owners form the existing reciprocal empty pair.
  Both original scenes have the same four decoded light intents when
  insertion time is excluded. These default row roles can still carry
  explicit presentation state when stored.
- The remaining original index row resolves to the real, nameless and
  empty `moAssembly_c.f1590` manager. Its native persistent ID is 1 in
  the two originals. It has no row in this observed native feature tree.
  Its physical presence remains independently represented.
- The generated roots have empty note and environment lists and a null
  `f1590`. The native observer still sees two note rows and four light
  rows, each under the expected real parent. The common default-role
  projection gives those six runtime rows no persisted ID or archive
  span. [Runtime member evidence](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/AssemblyRuntimeRowsCanLackIds.md)

All public IDs match the actual keyword class and tag exactly once. This
audit compares the observed feature kinds and parent relation as a
multiset. The native observation follows FirstFeature/GetNextFeature and
their subfeature traversal, with the existing observer's name-and-type
deduplication. Caption and publication order are outside this result.
[Reused planar owner proof](SdkPlanarRootSourceProjection2026.md) ·
[Existing assembly presentation ownership](AssemblyPresentation2026.md)

## Linked occurrence hierarchy

The same guarded reads reconcile 14 physical definition-local occurrence
records and all 18 expanded native occurrence paths. Every path has the
actual file target, active configuration name and fixed flag. Repeated
occurrences reuse their one physical target while keeping separate paths.
The greatest local matrix discrepancy is `5.551115123125783e-17`.
The greatest independently observed world matrix discrepancy is
`2.842170943040401e-14` with translations represented in millimetres.
Twelve guarded refusals cover detached typed aliases, duplicated public
identities and wrong native member parents in all four roots.

The inspection accounts for every timeline owner in these four roots.
Semantic re-export remains separate. The original roots each declare one
display state and retain distinct VisualStates streams of 1,299 and 1,741
bytes. The two generated roots have empty display-state lists and omit
that stream. Both sides retain source metadata and two empty native mate
payloads per bundle. An exact source projection still needs to retain
explicit light and manager state and decide the bounds of display and
provenance transfer. The result leaves all runtime selection and
writer qualifications in the existing SDK untouched.

## Reproduce

Run the host audit with the exact reader source tree and the four disclosed
source and native measurement directories under one absolute workspace.

```sh
python3.14 -I -B re/tooling/sw2026/nested_publication/MeasureNestedTreeOwners.py \
  --disclosed /absolute/path/to/Oracle121Takeover
```

The command records one sanitized JSON result on stdout. The proof starts
zero CAD processes, opens zero private inputs and creates zero CAD output
files. It contributes zero new native or FCStd conversion credit.
