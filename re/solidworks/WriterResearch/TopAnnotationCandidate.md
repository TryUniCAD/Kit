# Construct a part with a Top annotation view

`ComposeTopAnnotation.py` takes one JSON object with exactly three fields. `schema` is `kit.sw2026.top-annotation-candidate.v1`. `document` is the full typed `CadDocument` JSON for the existing Front-plane line-loop blind-boss request. `annotation_view` carries the view separately from sketch or display state.

| Annotation field | Accepted meaning |
| --- | --- |
| `configuration_id` | The sole active neutral configuration's exact identifier |
| `role` | `top` |
| `projection` | `orthographic` |
| `frame_direction` | `view_to_model` |
| `origin_unit` | `mm` |
| `transform` | The full existing interchange `Transform` JSON with a zero origin, axes `+X`, `+Z`, `-Y`, and typed vector components |

The origin is in model coordinates and axes are unit directions. The three view axes in model coordinates become the rows of the model-to-view rotation. The serializer derives the two negative zero components of the negative depth row. The persisted request has no native view IDs, slots, packet bytes, or annotation scene pointers. View visibility and assignment remain native oracle observations for this request. Plane visibility, display states and materials retain separate ownership.

The constructor populates the generated model's existing `fa48` `suObList` with one `moAnnotationView_c` schema 1. It allocates the ID from the generated view high-water mark and increments only `feb0`. The existing configuration writer allocates the class and object and passes its actual resulting map into the resolved writer. Both lanes are emitted from the same in-memory part graph. [Annotation field evidence](ConfigScene/Annotation.md)

```powershell
python re/solidworks/WriterResearch/ComposeTopAnnotation.py --request Request.json --native-locator C:\KitA12bResearch\reconstruction.SLDPRT --written-at 1785626030 --scratch Scratch
python re/solidworks/WriterResearch/VerifyTopAnnotationCandidate.py --scratch Replay
```

The replay constructs the request from the prior authored neutral geometry. Two fresh processes generate the same complete archive and manifest. The existing plain constructor at the same encoded locator and epoch remains the contrast. The script compares the exact streams and strict SDK fields and retains both archives in the requested scratch directory. Seventeen typed owner indexes move by two. Thirteen byte-local differences in four retained records have the same compact layout and arithmetic delta. The typed map attests the allocation change, while those retained-byte observations carry only the width and delta check. Fresh vendor measurement must establish application behavior. [Offline contrast](../measurements/2026/VendorBlindBossTopAnnotationCandidate.json)
