# P03 public writer admission evidence

## Pinned discovery pair and installed package

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| `re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT` | 44,796 | `db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357` |
| `re/automation/PairedCaptures/P03/fusion-8d53584027ff/P03-fusion-baseline-a.f3d` | 63,524 | `9f109b98ab7d36abeda8d9f88f9b336277238ce0bb3336d99313253ad47b2745` |

Both files are archived at capture revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`. The two installed `kit convert` processes used the existing uv-installed `unicad-kit` 0.1.0 and Windows Python 3.14.6. The install receipt has no Git revision. The current source working copy at the recorded install origin is `84a9b1672dcf986a5feabd1c0e8bcd7c3fab27cf`. Nine checked runtime files match that origin's current physical bytes. The distribution RECORD and launcher hashes identify the installed distribution inventory and executable. The claim covers the runtime files measured by the receipt.

| Installed evidence | SHA-256 |
| --- | --- |
| Launcher | `edc299475badddd4b5a8fbbee5d43974d1ed480defb71ddd87d2a325e00b8a33` |
| Distribution RECORD | `83129614ab026f3f7484df1b3ae77d6ba472ee744827f677605b2f9d2d2ea46c` |
| Two-route receipt | `bd060d30b015e0c7594366f02593e3a6d85582f0eac359c8cacd46eafb54c75c` |
| SOLIDWORKS → Fusion raw stderr | `34796a1aa4c5cc7d6ece3ede2709d7b0fbdf602226042f4cf50ccd3d88742f48` |
| Fusion → SOLIDWORKS raw stderr | `0e7e046eb35b8ffca91fbf47bf03a764d7567ea2c398f9f91bfab72bae339276` |

The commands and exact first refusals are in the [reproduction procedure](../../../Documentation/Changes/Research/Readers/Comparison/PinnedPublicAdmission.md). Both commands exited 1. Their stdout was empty and their destinations remained absent. The source bytes and their independently pinned hashes remained unchanged.

## SOLIDWORKS native and unresolved reader inventory

The independent SDK reader [PR #121](https://github.com/TryUniCAD/Kit/pull/121) at `c0a401a607759fb0c2589647c2a22af65ebb7ce1` produced the full default and design-only documents. They are distinct from the installed CLI run. Their hashes remain documented in the [independent P03 readback](P03GeneratedSdkReadback.md).

The inventory verifies all 25 native definitions. The 19 positive inline ranges cover 11,985 bytes of the 15,037-byte resolved stream. Their ranges are contiguous from byte 30 to byte 12,015 exclusive. Their checked bytes equal the corresponding retained source slices. Six reported rows have no positive range in the public projection. Nine rows have no reported class name. The display labels below suggest role groups, but do not establish which records can be regenerated or omitted.

| Local ID | Reader name | Reported class | Offset + length |
| ---: | --- | --- | --- |
| 8 | Comments | `moCommentsFolder_c` | 30 + 197 |
| 23 | Favorites | `moFavoriteFolder_c` | 227 + 206 |
| 24 | History | `moHistoryFolder_c` | 433 + 201 |
| 25 | Selection Sets | `moSelectionSetFolder_c` | 634 + 213 |
| 22 | Sensors | `moSensorFolder_c` | 847 + 191 |
| 7 | Design Binder | `moDocsFolder_c` | 1038 + 206 |
| 1 | Annotations | `moDetailCabinet_c` | 1244 + 84 |
| 17 | Notes | `moNotesAreaFtrFolder_c` | 1328 + 169 |
| 18 | Notes1___EndTag___ | None reported | 1497 + 403 |
| 10 | Surface Bodies | `moSurfaceBodyFolder_c` | 1900 + 222 |
| 9 | Solid Bodies | `moSolidBodyFolder_c` | 2122 + 220 |
| 21 | Markups | `moInkMarkupFolder_c` | 2342 + 190 |
| 16 | Equations | `moEqnFolder_c` | 2532 + 199 |
| 11 | Material &lt;not specified&gt; | `moMaterialFolder_c` | 2731 + 231 |
| 2 | Front Plane | `moRefPlane_c` | 2962 + 523 |
| 3 | Top Plane | None reported | 3485 + 566 |
| 4 | Right Plane | None reported | 4051 + 598 |
| 5 | Origin | `moOriginProfileFeature_c` | 4649 + 929 |
| 6 | Lights and Cameras | None reported | None reported |
| 12 | Ambient | None reported | None reported |
| 13 | Directional1 | None reported | None reported |
| 14 | Directional2 | None reported | None reported |
| 15 | Directional3 | None reported | None reported |
| 19 | Exploded Views 19 | None reported | None reported |
| 26 | RectangleSketch | `moProfileFeature_c` | 5578 + 6437 |

Every positive range is inside `Contents/Config-0-ResolvedFeatures`. A missing range in this report does not mean the underlying archive omits that owner. The typed configuration and CMgr reports complete their respective reads. The full linked typed read still refuses `moSimpleSurfIdRep_c` schema 1. The narrow rectangle record reader verifies Front 2, Origin 5, sketch owner 26 and Boss 34.

| A06 issue class | Design-only | Default |
| --- | ---: | ---: |
| Unclassified native or extension fields | 56 | 56 |
| Unclassified reference semantics | 51 | 51 |
| Native-only records | 25 | 25 |
| Retained bytes without portable semantics, including six empty | 25 | 25 |
| Uninterpreted native values | 23 | 23 |
| Unverified source confidence | 6 | 6 |
| Unresolved name-based direction reference | 1 | 1 |
| Domains requiring independent comparison | 1 | 3 |
| **Total** | **188** | **190** |

Default adds B-rep and retained payload domains. Both graphs have 57 nodes. Design-only tracks 1,044 fields and default tracks 1,046. The full inventory SHA-256 is `adb1704f8eec3bf1183848e1b83a68a02b1e8ee3625951ae32098ad75c06ada2`. These counts identify reader evidence rather than missing-feature counts. No record or diagnostic was removed.

The source sketch and owner share the exact 5,578 + 6,437-byte span. Owner 26 selects Front 2 and Boss 34 selects the same authored owner. Origin 5 is a separate linked native point. The immediate condition for any future portable reference representation is a reversible, source-bound owner and support mapping that keeps the original native custody. [Source-bound constraint preparation](../../../Documentation/Changes/Research/Encoder/ConstrainedBossIntent.md) · [Direction-owner observation](../../../Documentation/Changes/Research/Readers/Comparison/ConstrainedBossDirectionOwner.md)

## Measured source roles and limits

The historical source measurements are separate from the current installed reads. The SOLIDWORKS capture receipt SHA-256 is `f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94`. Its measurement file SHA-256 is `7d39e0e206340b1c699969064cb343f9ec3b66bd530b98e1bb6498367f6aba85`. The Fusion capture receipt is `f42a7e81b9ae108ba69d440ff411a8828dbc9ee0bbd54d6242c22370cf6560b8`. Its measurement file is `a21f81df15c4fd2afad5ed846b7a19c4f500b6dfea89f6fa7ede72985e4ed636`.

The source applications reported SOLIDWORKS 34.4.1 (executable 34.4.1.1011) and Fusion 2706.1.17. Both before and after source controls returned one body. The two measured sources have one solid, an 800 mm² section, an 8,000 mm³ volume and a centroid of (20, 10, 5) mm within the recorded tolerances. The positive blind displacement is 10 mm. The three individual driving-size edits yielded 8,200, 9,200 and 9,600 mm³. Restoration returned to 8,000 mm³. These are historical source reactions. They supply no target generation or native acceptance evidence.

The independently measured SOLIDWORKS sketch reports four axis relations, two driving distances and the separate Origin coincidence. Shared point identities close the four corners without four more native solver records. The Fusion receipt records geometric constraint types and driving expressions without the full operand identity graph. Its native normal and bounds agree on the baseline. Its complete operand equivalence remains unqualified. The saved source roles require the separate Origin coincidence. The bounded Fusion constructor's fixed corner represents a different constraint relationship. [Paired rectangle discovery evidence](../../../Documentation/Changes/Research/Readers/Comparison/RectangularPairEvidence.md)

The SOLIDWORKS native API source tree has 25 rows while the installed and independent SDK source histories have 26. Both SDK reads report extra row `sldprt:feature:19` at order 23, with type `Exploded Views`, confidence 0.6 and no attributed span. All 25 captured API names occur in each SDK inventory. Their order differs around lighting and environment. The extra reader row does not establish a separate authored feature or its byte owner. Folder and presentation rows require their own owner evidence. The default B-rep and inactive payloads are separate geometry and cache observations. Their observed names or empty inline data do not establish that the source state is optional.

Neither historical capture measures density, body material color or appearance. Discovery receipts pin these sources and their measurements. The capture revision's general corpus manifest does not include these pair hashes in its assets or evidence entries. These discovery inputs do not supply a held-out qualification result. The independent measurement-to-reader join is sealed at SHA-256 `e0158a46ea0e662c8e0e108f61b0b1fd858791f9f75a69cbca37511a60146ac8`. It binds Fusion owner 207, sketch 202, Boss 277, body 309 and XY datum 204 to the measured roles.

## Installed reader evidence and target writer guards

The same noneditable package returned both strict SDK documents in independent fresh processes with B-rep and tessellation requested. The SOLIDWORKS document SHA-256 is `67e1466ad530ecc4abbc90994d57f331b681b7d35a762491069ae10e95fecd68`. Its receipt SHA-256 is `2db29a2b96db1571f1141f06df4ac5042981409db14c035a70be176bdf9185ea`. These are installed reader artifacts. The #121 artifacts above are separately pinned.

The installed `Timeline` and `BuildFeature` retain each native history row. `NativeFallback` keeps its object data and provenance where a portable definition is unavailable. The verified BlindBoss stays typed. The CLI's `CheckPortable` stops before it reaches the Fusion writer. The first actionable source role is the real sketch-owner and support chain. The existing [logical Boss constructor](https://github.com/TryUniCAD/Kit/pull/168) and [P03 source proof](https://github.com/TryUniCAD/Kit/pull/314) supply the checked sketch and operands for a future target consumer. Every other native role still needs an evidence-backed disposition.

The installed Fusion document SHA-256 is `95201be7be7c2a20652f216d686c3879e88297c48453d2db7b1d1d63a0e4ffdd`. Its receipt SHA-256 is `7834acb1b56817edf07f13d567f5075be4af1b530210cea507debec7e2cded17`. `ReadMaterial` joins the physical and visual package references. `ProjectPrism` assigns the typed record to body `fusion:0:309`. The reader reports `PrismMaterial-018`, 7,850 kg/m³ and RGBA `(0.626209681225, 0.626209681225, 0.626209681225, 1)`. It retains `fusion.read_only=true`. The native source measurement reports body label `Body1`. The installed reader body name is empty. Source ownership of that label still needs proof. [Body name projection gotcha](../../../Documentation/Gotchas/Research/Readers/FusionBodyNameProjection.md)

The registry calls `CheckMatWrites` before the SOLIDWORKS adapter's `supports` check and staged write. The target writer has no typed material capability. A future target must preserve the assigned body, name, density and color using measured SOLIDWORKS representation rules. The [Fusion authored material research](https://github.com/TryUniCAD/Kit/pull/333) supplies a bounded format producer. It leaves the original saved alias and appearance graph open. The density and RGBA above are reader-reported. Existing source receipt measurements do not certify them.

The current installed object graphs retain a separate issue inventory. The SOLIDWORKS graph has 57 nodes, 1,046 fields and 191 issues. It adds the `solidworks.part_text_properties_unavailable` diagnostic domain to the #121 default tally, with the same other issue counts. The Fusion graph has 28 nodes, 279 fields and eleven issues. It retains four uninterpreted expressions, five native or extension fields and two domains requiring independent comparison. The issue file retains every issue and exact input pin, SHA-256 `1c2ef659d0a6a973ffe92d97f13e07ba27971a8da40635edb265414f96043a3a`. These are current package observations, distinct from the #121 graph counts.

Both first refusals remain correct. Full history and body support, material or appearance native measurements, multiple independent input lineages, published writer qualification and fresh target acceptance are open.
