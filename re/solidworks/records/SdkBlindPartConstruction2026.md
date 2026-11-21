# SDK ordinary blind-boss part composition

Task `B04-SW2026-CONSTRUCTION`, owner `/root/flag_ownership`, delivery PR #121.
This tranche composes the first complete SDK-only rectangular forward blind-boss
candidate from an actual neutral `CadDocument` and explicit native presentation,
target, output and provenance inputs. It does not register or enable a public
SOLIDWORKS writer. Native load, rebuild, driving edit and persistence acceptance
for these exact bytes remain separate measurements owned by the oracle owner.

## Construction boundary

[`MakeBlindPart`](../../../src/convert/adapters/solidworks/Archive/Construction/Part/MakeBlindPart.py)
accepts a real neutral document and `PartBuildInput`. Its supported profile is
one active independent configuration, one canonical Front Plane support, one
unconstrained closed axis-aligned four-line rectangle, one positive driving
length parameter named `D1`, one ordinary forward blind create extrusion and
one resulting design body. The document may use explicit millimetre, metre or
inch lengths; the construction plan uses metres. The initial process cohort
authors millimetre documents with distinct geometry and document identities.

The projector validates the document and its actual configuration, parameter,
support, sketch, feature and body references. It rejects native B-rep/payloads,
meshes, assemblies, drawings, materials, selections, extra document metadata,
additional modeled entities, expressions, suppressed or configured features,
second direction, draft, offsets and target references. Supported construction
settings require matching document units, effective ISO standard one, explicit
styles, folder/plane names, clocks, author/company/comment, target build, density,
leader selection, self path and journal name. No captured native input supplies
these values.

`PartCandidate` retains the original actual `SystemValue`, profile and boss
graphs, `HeaderValue`, `TopHeader`, `ManagerHeader`, Definition graph, Config and
Resolved maps, all ten stream buffers and the computed container. `CurrentConfig`
returns the actual independent manager configuration node. Linked drawing or
assembly construction can consume these nodes directly. No decoding or research
object reconstruction is needed to obtain the child model or configuration.

The actual self identity is `HeaderValue.FieldsValue["f38"]`, shared with
`TopHeader` during construction. `ManagerHeader` is the actual third header
returned by `MakePartHeaders`; consumers use its own `f60` save event rather than
inferring manager provenance from the self file. The part's ordinary `f2f8`
remains null. A convenient returned configuration is not a new wire backlink.

## Field rules and provenance

This is a source promotion and composition of previously documented current-build
rules. No new vendor executable, listing, native observation or held-out payload
is used. Model addresses in the linked ledgers bind `sldmodu.dll` SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

| Owner / field group                                  | Classification                                            | Generative rule and existing evidence                                                                                                                                                                                                                                                                                                                                                                                 |
| ---------------------------------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Model, manager, folders, principal planes and origin | Input, derived identity and documented constructor state  | Reuse the complete [SDK part system](SdkPartSystemConstruction2026.md), [part root](SdkPartRootConstruction2026.md), shared `PersistentIds`, node/concept/feature initializers, explicit units/styles and actual configuration selection. No saved feature table is input.                                                                                                                                            |
| Ordinary profile data and origin distinction         | Constructor state and actual references                   | `MakeProfileData` factors the existing complete contour/profile state: actual sketch/support, model-to-sketch frame, absent derived profile and fresh contour/body caches. Ordinary `pd_f11c=-1`; origin initialization applies its existing `& ~6` transition to `-7`. Origin bytes must remain unchanged. [Profile rules](ProfileConstruction2026.md)                                                               |
| Rectangle points, line endpoints and adjacency       | Input and derived topology                                | Four ordered neutral vertices construct actual point and line records, two independently owned incident line handles per vertex, permanent/creation namespaces and counters computed by the shared [polygon factory](SdkPolygonConstruction2026.md). No stream offsets or recorded operations are used.                                                                                                               |
| Profile and boss IDs                                 | Derived bookkeeping                                       | Both allocate through the same actual part allocator after the system graph. The boss parent list retains the actual profile. Counts are obtained from actual collections. [Model rules](ModelConstruction2026.md)                                                                                                                                                                                                    |
| Boss base/body and `f28/f810/f818/f838`              | Constructor state, derived history and input              | `MakeBossNodeMut` initializes the documented model/body/atom bases. Binding adds the actual one-profile parent list, `f28                                                                                                                                                                                                                                                                                             | = 0x140`, constructor `f810=-1`, actual complete end specification and inactive zero scalar. This is a create boss, not the cut body-selection family. [Profile/live extrusion rules](ProfileConstruction2026.md) |
| Five parameter/value/handle/display graphs           | Input, mode-derived vocabulary and constructor state      | Construct roles `1,2,3,4,19` in native constructor order. Roles 1/2/19 use length parameters; 3/4 use angle parameters. `D1/D2` receive the input depth; draft/from values are zero for the selected mode. Each real dimension allocates `f50`; parameter node `f08` remains `-1`. [Blind-end rules](SdkBlindEndConstruction2026.md)                                                                                  |
| Common display state and subtype                     | Constructor state and explicit presentation               | Share the previously proven distance constructor fields, text and value bases. Boss length text kind is 2, angular kind is 13; mate distance remains kind 18. Actual handle/value/parameter identities and the distinct native angle/distance tails remain intact. Explicit design-intent and leader inputs control their documented bits. [Dimension construction](ProfileConstruction2026.md)                       |
| End and from-end branches                            | Derived mode and actual references                        | Shared `MakeBlindEnd` owns the full ordinary forward blind end. A real type-zero from-end retains the `D19` runtime graph. Conditional serialization may omit inactive displays; it does not cancel their actual ID allocation. [Transient dimensions](../../../Documentation/Gotchas/Conversion/Solidworks/TransientDimensionsConsumeIds.md)                                                                         |
| Configuration progress and Header counters           | Derived bookkeeping                                       | Update the actual active configuration after all five dimension allocations. Header counters use that allocator. Independent CMgr map base one is distinct from the Header→Config→Resolved linked namespace. [Configuration manager](SdkPartSystemConstruction2026.md)                                                                                                                                                |
| Header self file and CMgrHdr2                        | Input, derived identity and constructor state             | New actual path/title handles, part kind two and selected configuration ID/name come from explicit input and actual nodes. Header2 is model-absent; ModelHeader is model-present. CMgrHdr2 derives its one active row from the manager/configuration and its own explicit save event. [Header rules](HeaderConstruction2026.md), [CMgrHdr2 rules](ConfigurationManagerHeader2026.md)                                  |
| Biography and version history                        | Explicit provenance, derived counts and constructor state | New empty biography; one current-version state, explicit originating build without claiming native-save provenance, one explicit stamp and date-code object. Counts follow constructed lists. Severity/minimum-memory constructor states are `0/0xffffffff`; license-origin category, language and CJK state are explicit. [History rules](HistoryConstruction2026.md), [metadata rules](MetadataConstruction2026.md) |
| Keywords                                             | Input and derived presentation                            | New XML from actual configuration/feature IDs, names, concrete class vocabulary and the one active `D1` depth in declared presentation units. Ordinary feature/Sketch/Extrusion tags retain native UTF-8 framing. No cached XML is accepted. [Metadata rules](MetadataConstruction2026.md)                                                                                                                            |
| Container                                            | Documented format rule and derived framing                | Shared SDK `BuildSldprt` composes the ten computed buffers using format version four, known signature vocabulary, compressed content, lengths, CRCs, directory entries and offsets. It reads no template or existing file.                                                                                                                                                                                            |

The SDK factory follows the active fresh model initializer: three distinct empty
`suObList` nodes occupy `f9d8/fa48/fa50`. The older mathematical research part
factory chooses null inactive pointers at those fields. The independent
comparison explicitly performs the three documented fresh allocations on its
own newly built reference graph, then reserializes its Config/Resolved pair.
This is a declared constructor-policy difference, not a fitted saved-file patch.
Production neither imports that reference factory nor consumes its bytes.

## Complete stream ownership

The writer reuses the admitted SDK Header, CMgr, Config, Resolved and Definition
codecs. New small current-version CMgrHdr2 and empty/fresh history codecs use the
same `ArchiveNode`, scalar/string/tag/count/maps and field evaluator. They have
ordinary version-19000 guards, concrete root checks and complete-stream reads.
Populated biography and other version-history states are not admitted by this
fresh profile. No unsupported branch becomes opaque data or a copied tail.

The ten stream names are `Header2`, `Contents/Config-0-ModelHeader`,
`Contents/Config-0`, `Contents/CMgr`, `Contents/CMgrHdr2`,
`Contents/Config-0-ResolvedFeatures`, `Contents/Definition`,
`_MO_VERSION_19000/Biography`, `_MO_VERSION_19000/History` and
`swXmlContents/KeyWords`. Config binds the actual direct header references;
Resolved extends the exact Config snapshot with the independent manager context.
Raw wire fields and reader/runtime-only fields remain distinct.

The public adapter remains unchanged. This callable returns an unqualified
construction candidate; it does not turn a byte-complete graph into qualified
public writer support.

## Process proof and custody

The initial immutable source packet contains 70 executable overlays: 59 SDK
modules, six permanent process-integration modules and five research transport
scripts. `SourceManifest01.json` SHA-256 is
`5ac79c146843c81750bdd3ee64eacd8854951d88b5937de3a390c027553749f8`.
The eight common dimension and twenty shared metadata/files/history source
bindings remain unchanged for parallel consumers.

`TestBlindPart` runs two independently authored real neutral documents through
three separate interpreters each:

1. Guarded SDK-only build, actual aliases and five dimension lifetimes, complete
   ten-stream/container output, twelve invalid complete requests per model.
2. Separate guarded container decode, complete typed read/serialization of all
   ten streams, ordered rectangle topology, actual profile/support/depth paths,
   self identity, configuration-prefix aliases and completed grammar reports.
3. Independent fresh research mathematical construction from the same neutral
   design and explicit settings, with the declared active-list initialization,
   followed by all ten payload comparisons and allocator/map comparisons.

Runtime input-file opens, directory enumeration and process launches are denied
inside each construction/preparation boundary. Production sources and codecs
load before that guard. The SDK-only build and preparation count actually loaded
research implementation modules, excluding their named test transport helpers;
they fail if any implementation module is present. The mathematical comparison
is deliberately a separate research process and is never a production dependency.

Preparation checks compact and extended endpoint/handle encodings through their
actual conditional fields. It does not demand runtime-only sketch `f138`,
unencoded parameter owners or inactive `D2/D3/D4/D19` displays after raw readback.
The retained live path is boss→end→distance display→actual handle→value→parameter.

The worker performed static checks only. The root independently froze 4,576
source files, manifest SHA-256
`61f13cdca7100618f9b0e9925649b8a684b43b93d8eb384cb9f77d4e8c9db65b`,
and passed both the permanent `TestBlindPart` integration and unchanged
`TestPartSystem`. A separately persisted eight-worker replay retained both raw
requests, two identical SDK builds per design, preparation and mathematical
comparison reports, and every generated stream. Its `BuildProof.json` SHA-256 is
`e1291e07bc665ac737886dab257d377b32bc2e135ac196536509f69e1569c763`.

All twenty distinct logical payloads matched both typed preparation and the
independent mathematical reference. All twenty-four distinct invalid complete
requests rejected. Both SDK-only phases reported zero research implementation
imports, and every worker reported zero runtime input reads. Typed load/store
usage completed without missing or provisional schemas. Both generated Config
maps end at 87 and Resolved maps at 202; their observed schema counts are 120
and 105. Actual dimension IDs are 20 through 24 with parameter IDs still `-1`.
These are observed bookkeeping results, not construction constants.

The two container lengths are 8,166 and 8,243 bytes, SHA-256 respectively
`750261e28691593f0163c172498ea3c5760a5c29fa231d4a5a9f8f309aaebe9d` and
`9166c766f48fe5e20a4f041ed0bfa9f368ce1d1b790d654baaafab81a9428618`.
The worker independently checked all seventy frozen source bindings and the
raw worker/report/stream metadata. The sanitized
[process receipt](../measurements/2026/SdkBlindPartConstruction01.json) binds
those exact sources, reports, generated bytes, ownership checks and limits.
The raw proof does not record the Python version; the receipt does not infer it.
No separately persisted test-framework report is claimed for the two permanent
test calls. The retained raw replay provides the detailed component evidence.

Earlier part-system, polygon, blind-end and distance-mate results remain
component evidence. Neither those results nor this byte/graph proof establish
native acceptance of the new complete composition.

## Native experiment and remaining scope

The first authored case has a centered 24×16 mm rectangle, `Sketch1`,
`Boss-Extrude1`, active `modeled default`, depth 12.75 mm and no sketch dimensions.
Its analytic one-body volume is `4.896e-6 m³`, area `0.001788 m²` and centre
`(0,0,0.006375) m`. A successful live `D1@Boss-Extrude1` edit by 3.875 mm predicts
depth 16.625 mm, volume `6.384e-6 m³`, area `0.002098 m²` and centre z `0.0083125 m`.
These are neutral geometry calculations, not native measurements.

The private root-owned deck binds the exact source manifest, encoded output path,
request constructor, generated stream/container hashes, ordinary COM semantic
checks, separate fresh-process reopen and healthy disclosed controls. It refuses
existing output paths. Original generated bytes and raw results remain immutable.
No worker VM/CAD/COM or native instrumentation is used.

Native cache regeneration, final presentation and solver state, clean open,
rebuild, edit, save and reopen for these exact generated bytes remain unqualified
until measured. The six sealed held-out files are not opened or used. Broader
sketches, planes, modes, features, materials, configuration graphs and general
public writer qualification remain outside this selected profile.

The CAD stopping conditions remain:

> The first is success under every criterion on this page.
> The second is the end of the available context.

The component is a complete concrete construction candidate. Full CAD success
and public support still require every criterion and the remaining measured scope.
