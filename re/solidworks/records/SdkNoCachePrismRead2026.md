# Strict no-cache typed rectangular-prism read

Task `PR121-STRICT-NO-CACHE-RECTANGLE-READ`, owner `configuration_header`, delivery PR #121. The implementation is prepared in a private source overlay for root review. It adds no native writer registration, no native geometry cache and no FCStd acceptance claim. Root retains all native-oracle and Git ownership.

## Behavior

The ordinary part reader can build a validated neutral `BrepModel` when the selected source physically has no geometry cache and its entire typed model satisfies the bounded rectangle profile. It keeps `brep_payloads` empty. Existing cached sources retain their original decoder and errors. It adds an informational `sldprt.brep_reconstructed` diagnostic that identifies the actual profile, boss and driving-depth owners and declares that generated topology does not carry persisted kernel identities.

The shared adapter change is a private overlay around `ReadNativePart`: attempt the complete typed no-cache profile before its existing stored-payload call, use the resulting exact topology summary if present, and otherwise retain the existing path unchanged. Other native parts, assemblies, drawings, supported cached inputs and unsupported data retain their existing branches.

## Admitted source profile

- Outer container version 4, archive version 19000, actual schema-one ordinary part and one independent active Config-0
- Only the declared ordinary stream roles; any geometry/cache stream or unknown additional role prevents reconstruction
- Complete nonprovisional Config, Resolved and CMgr decode, with every allocated object checked against the ordinary constructor class vocabulary
- Exactly the twelve ordinary system folders, cabinet, three actual canonical principal planes, actual model origin, one local profile and one ordinary create boss
- Empty live/ghost body managers, model geometry collections, configuration body transforms, selections, overrides, relation/equation owners and optional shape attachments
- Actual local self-component and datum aliases, matching profile inverse, canonical Front support at the origin and an ordinary fixed model-origin sketch
- One complete four-line axis-aligned rectangle; plain coordinates or the already qualified two-driver/four-axis graph, optionally with its actual external model-origin coincidence
- Forward one-direction blind creation, live positive depth, ordinary plane-start, zero retained forward and reverse draft values, separate dimension owners, and the documented constructor inactive reverse-depth value

The line points, handles, order, driver relations and origin are read from their actual typed owners. Construction entities, extra contours, other curves, ambiguous regions, retired lines, shared/spatial sketches, additional features, multiple configurations or bodies, reversed/mid-plane/two-direction ends, from-offsets, draft, thin/surface/cut modes and additional geometry state remain outside this profile. The guard does not infer geometry from names, hashes, bounding boxes or a visible-operation count.

The actual public history projection must also agree with the native inventory: complete typed status, matching feature identities and extrusion/profile ownership, one ordinary public operation, the actual typed line intents and every public principal frame matching its typed datum. Stale keyword surface classifications or additional cached feature rows cannot qualify a partial legacy projection by supplying only a computed body.

## Geometry derivation and provenance

The typed `moExtrusion_c.f60` parent selects the actual profile. Its `f818.f18` selects the active display/handle/dimension/parameter chain. Both draft chains are checked directly. The profile's `pd_f78.ff0.f00` selects an actual principal datum, its local component aliases the parsed part, and the source `pd_ff0` agrees with the inverse derived by `FrameXform`. `ReadDatumFrame` supplies the actual rigid frame from `moDefaultRefPlnData_c`.

The existing typed line reader resolves every active point and segment handle. It verifies the contour, unary axis relations, independently driving dimensions and optional actual origin relation. `DriverLine` independently compares each driving length with its selected point pair. The fifth external origin point is retained as design intent and is excluded from the swept contour.

`BuildPrism` constructs all neutral vertices, curves, edges, loops, coedges, analytic planes, faces, shell and body from those current values. Its topology validation and independent signed geometry checks establish a closed outward solid. The body topology summary receives actual counts, volume, area and bounds. No native kernel body tag, face ID, rollback mark, atom attribute or Parasolid payload is created.

Existing constructor vocabulary supplies the narrow neutral-state guard. No saved row, value program, offset patch, file hash allowlist or saved geometry is a product input. Relevant constructor/read authorities are:

| Boundary | Existing authority |
| --- | --- |
| Node, model, part and atom neutral state | `Archive/Construction/{Nodes,Model}` and their pinned Config/Resolved field layouts |
| Whole feature inventory | `TypedResolved/IndexFeatures` plus `Construction/System/SystemClasses` |
| Selected independent configuration | `Construction/Configuration/{MakeConfigMgr,MakePartConfig,PartCfgObject}` and typed CMgr aliases |
| Support and placement | `Construction/PlanarMates/ReadDatumFrame`, `Geometry/{ReadRigidXform,FrameXform}` and the actual profile reference |
| Closed contour and intents | `TypedResolved/Lines` and `TypedResolved/LineDimensions`, including `DriverLine` and origin ownership |
| End, draft and feature modes | `SdkBlindEndConstruction2026.md`, `SdkBlindPartConstruction2026.md`, `ProfileConstruction2026.md` and the existing ordinary constructors |
| Neutral geometric construction | `convert.Geometry.Extrude.Polygon.PolygonExtrude.BuildPrism` and its shared topology validator |

`f85c` is deliberately excluded from the fresh configuration zero-word guard: `SetCfgStampMut` derives it from the final actual allocator counter minus one. The native constructor clear is not its final constructed value. The plane constructor-only `f34c` is not a persisted resolved field; the reader validates actual datum geometry and persisted mode owners instead. General typed metadata continues to report its existing broader `full_linked_graph=False` boundary; this addition qualifies only the explicitly checked profile above.

The separate configuration header record identifies `f4c4` as the actual configuration flags copied into the directory header at native address `0x18003ecf3`. The final guard requires the ordinary constructor flags and per-config version rather than interpreting the sole object count as sufficient mode admission. Additional configuration and manager owners remain absent. No meaning is invented for an individual unclassified flag bit.

## Process evidence

The retained first process trial is false. Six fixtures failed identically on baseline and overlay before reaching the intended observations: an invalid text placement, incomplete offset/reuse fixtures, tuple mutation, pre-existing unsupported shrinkwrap grammar, and a rectangle-only neutral projector used for a triangle. That result remains immutable. Corrected fixture packaging reran the complete method against unchanged product code. That passing second trial is also retained. A subsequent source audit found unqualified configuration selectors that the original guard had not explicitly constrained. The mode-closed overlay adds the ordinary constructor predicates, reruns the complete paired method, and adds thirteen serialized negative probes for configuration/manager selectors, per-feature version, stale width/height drivers, a depth alias and an offset external origin point. Its passing result is retained. The final overlay also requires consistency with the public typed projection and reruns all cases with two additional stale-keyword negatives.

The final paired method passes in 120 fresh Python processes: baseline and overlay for six independent neutral rectangles, 51 public strict rejection designs, one unchanged pre-read unsupported shrinkwrap-grammar rejection, and the disclosed F14a initial/saved files. Every audited public read has zero extra file access and zero research implementation imports. All generated input bytes match the baseline. Unsupported cases preserve the exact strict error and the history-only, lenient and tessellation-option behavior.

A separate process runs the actual registered public writer into caller-owned streams and the default strict public reader. Two independent rectangles pass four strict geometry reads and two history reads; eight reversed-end/present-cache/unknown-stream reads reject. The whole public write/read phase uses zero extra file access. This is integration coverage, not unit testing.

| Disclosed F14a state | Input SHA-256 | Strict result | Geometry |
| --- | --- | --- | --- |
| Initial generated file | `44bd9e4259a3e5703a39ecb6d92fe9450b67eb699fc57f44ad48aae9b15c1bcc` | Computed B-rep; zero native payloads | 8/12/6; 6000 mm³; 2200 mm²; centre (10,15,5) mm |
| Native-saved depth edit | `b0aca662be89a5e41449ea46f79ca099aba766cdea0e1c81b56f0e8e0485d122` | Original stored decoder; three raw payloads | 8/12/6; 8400 mm³; 2600 mm²; centre (10,15,7) mm |

Both states retain three live parameters, seven relations and thirteen literal file properties. The saved derivative's complete public document serialization is identical between baseline and overlay. The initial file's history, parameters, sketches and text are unchanged; added B-rep/topology, its derivation diagnostic, inferred B-rep capability and the corresponding existing semantic fingerprint change as expected. No native flag or acceptance attestation is set by this calculation.

The source-only investigation also compares independently reconstructed saved geometry with the decoded native Parasolid: all six face-coordinate sets agree after 1e-8 mm comparison normalization, with signed winding, manifold incidence, volume, area, centre and bounds checked separately. The coordinate normalization belongs only to the comparison; the builder retains actual input coordinates.

## Preserved cache and tessellation boundaries

The experimental generated native partition is not used. Its matching controlled native attachment still opens with warning 32 and zero bodies before rebuild, including after the five forward-fin anchor corrections. This implementation keeps the native writer bytes unchanged and does not turn SDK geometric validity into a native cache claim. See the partition-open and edge-anchor records.

`include_tessellation=True` currently yields zero meshes on the ordinary part path, including the native-saved witness. Reconstruction adds no mesh and changing that option leaves the computed B-rep identical. `include_brep=False` continues to return only the existing history representation. `ApiBrep.ExtractBrep` exports existing native payload records; this no-cache profile has none to extract. Callers can use the computed neutral `document.brep` through separately supported geometry APIs.

## Verification and delivery

Black, Ruff, strict Mypy, strict Pyright and steering pass on the 33 new production/test paths. The adapter overlay adds no steering findings. The donor scan passes on all 29 product paths. Existing unsupported Pyright configuration-option notices remain visible in the private static log; no source rule was weakened. The formal public integration entry is `tests.Convert.Solidworks.Research.CacheFreePrism.NoCachePrismReadTests.TestNoCacheRead`.

The source closure contains 4292 Python files. Its 29 product files match the earlier paired-method freeze exactly; the five formal integration files were added separately. The sanitized process receipt binds the hashes and preserves the false first trial. Root owns application of the adapter overlay, integration on the active revision, remote CI and any further qualification. No Windows process, licensing service, held-out native input or Hopper session was used in this lane.

[Sanitized source-only receipt](../measurements/2026/SdkNoCachePrismRead01.json) · [Existing F14a native lifecycle](SdkFreecadOriginBox2026.md) · [Partition-open evidence](PrismPartitionOpen2026.md) · [Forward-fin evidence](RectangleEdgeAnchor2026.md)

The root integration reran the guarded public registry path on the shared checkout after applying all 38 verified delivery files. Both neutral designs write successfully, four strict geometry reads and two opt-in history reads pass, and eight unsupported cases reject. The process observes zero extra file accesses. The integrated report SHA-256 is `54d57de115d822ec9e062c4c5182f8bb5dbc07735b46569fdbc7e5f8b3a6eccd`.
