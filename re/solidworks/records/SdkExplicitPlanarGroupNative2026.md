# SDK explicit planar group native lifecycle

Task `B04-SW2026-ASSEMBLIES-C10`, owner `/root/assembly_occurrence`, delivery
PR #121. The root agent owns the Windows oracle and publication. This record
qualifies one disclosed generated three-occurrence group and its edited saved
derivative. The original A20/A21 cases remain sealed and unevaluated.

Dependencies are the [explicit group constructors](SdkPlanarGroupConstruction2026.md),
the [dimensioned rectangle native proof](../measurements/2026/SdkRectangleDimensionsNative01.json),
the matched reference checks in [ordered mate lifecycle](SdkOrderedMateLifecycle2026.md)
and the disclosed A22 control. The exit condition for this tranche is a clean
controlled native edit/save/reopen, followed by strict SDK readback of the exact
original and saved siblings. This is not the C10 exit condition for the original
locked cases.

## Frozen construction and observation

Constructor source manifest
`753f64e4222ee9172b24d65abd02cbd2469254b5bf865f1a085c39276791f162`
and the independently replayed construction result
`e2f664a081f6219678a6311001b0853f2702393ade63bb7f8ce5e52cfb099c2e`
precede native execution. The corresponding constructor revision is
`a06b6d4ef0aa7f185e5e9ac8b82803dc159aa583`.

`PrepareSdkPlanarGroup.py` freezes the source, independently predicted fixture,
two deterministic generated bundles, tools and A22 control custody. Its packet
hash is `c572ae2ea2340b30c3096844c6a835c77068701617ace624ea0ee83f51312b57`.
`SdkPlanarGroupPrediction.py` derives geometry and the edit from authored
rectangle dimensions, ordered endpoints and rigid placements. It reads no
native model or generated cache. `InspectSdkPlanarGroup.py` reuses the existing
fresh-process native phase runner and matched semantic reference checks.

The child is a centered 54 × 18 × 8.25 mm dimensioned rectangle prism. Three
occurrences share its actual selected configuration `modeled default`; the
parent uses `Default`. The first occurrence is fixed. All three have a
17-degree Z rotation. Six ordered relationships include a parallel mate
between the two floating occurrences, a positive driving distance, two
coincident mates and two further parallel mates. Actual endpoint indices are
explicit, including reversed pairs. There is no per-case saved field data.

The live distance changes from 134.38 to 150.11 mm. Independent prediction
moves only the third occurrence by 15.73 mm along its rotated local X axis,
while preserving every other relationship. Child D1/D2 sketch dimensions and
boss D1 remain 54, 18 and 8.25 mm.

## Native result

[Sanitized native receipt](../measurements/2026/SdkExplicitPlanarGroupNative01.json)
binds raw result
`333574efef8ac855ccb4b2a4a933b48e386ccbb03aa995d9c975e9a3c2c5198b`.
SOLIDWORKS 2026 SP05.2, executable `34.5.2.0604`, measured four distinct fresh
processes: A22 before, generated edit/save, fresh saved reopen, A22 after.
The observer ran under Windows Python 3.12; generation ran under Python 3.11.

All four phases pass with zero open errors or warnings, healthy controls and
unchanged immutable inputs. The 440 numeric checks are distributed 80, 168,
112 and 80 across those phases. The generated assembly has three solids,
three resolved direct occurrences, six ordered mates and twelve actual
principal-plane references. Its complete native parent/child trees have
31/25 rows and remain stable through edit and fresh reopen. Both selected
configuration names, the fixed anchor, all three child drivers, ordered
endpoint identities, normals, distances and independently predicted placements
pass.

The parent volume is `2.4057000000000007e-5 m³`, area
`0.009396000000000002 m²`, and initial centre of mass is
`(0.08254822653472922, 0.02523752555166664, 0.017255000000000003) m`.
After the edit, its centre is
`(0.08756245113849541, 0.02677052785676285, 0.017255000000000003) m`.
The volume and area are unchanged. Child save and then parent save both return
`[true, 0, 0]`. Fresh reopen preserves the edited dimension and geometry.

Native mass values are reported separately. The generated parent reports
`0.024057000000000005 kg`, while its child reports approximately
`8.019e-6 kg`. Parent mass divided by the sum of repeated child mass is
approximately 1000. Both A22 brackets exhibit the same ratio. This records the
matched native API density behavior; it does not establish general source and
target kilogram parity.

The host report hash is
`6cd2ee1ff33ced1b2fb51124b3b5de72524faf851e86efd17cdcb5cd0d8d9174`.
Its transport return code and supervisor exit code are zero, and transport exit
is confirmed. The host explicitly reports `acceptance: false` and
`guest_state_unknown: true`; native acceptance comes from the separate phase
observations and healthy brackets. The host performed no automatic guest kill,
VM reset or retry.

## Exact public read and typed saved-file audit

`ReadSdkPlanarGroupNative.py` reads through normal public `open_document` with
B-rep and tessellation disabled, asserts document validity, and records any COM
imports. Its independent typed audit uses the actual linked production archive
maps. It writes only in-memory serialization output and private JSON evidence;
the original, saved siblings and native packets stay unchanged.

[Sanitized SDK receipt](../measurements/2026/SdkExplicitGroupPublicReadback01.json)
binds raw result
`035c1c2d8b9ea86b624649ae54ce7230a41d500cfbd4807ebeb4b92f64ccc7c7`
and the separately frozen reader source manifest
`6674ba350f02d53c1d29d3608bb65429112f35ae20c28389d3551c3efed609cd`.
Six fresh workers perform two normal reads and four typed archive audits.
No native process starts, no COM module imports and no held-out input is read.

Both strict public reads retain exactly three occurrences, six ordered mates,
twelve entities, three real child drivers and fixed flags `[true, false, false]`.
They match the appropriate original/edited distance, transforms, linked child
hash, both configuration names and actual datum/occurrence identities. Both
retain the informational legacy scanner diagnostic
`sldasm.native_record_unresolved`; this is not suppressed or represented as
complete independent native-record coverage.

All 26 scoped stream round trips are byte-identical. Each parent contributes
Config, ResolvedFeatures, CMgr, CMgrHdr2, ModelHeader, Header2 and MatesList;
each child contributes the same six roles without MatesList. The native-saved
Definition, History, XML, B-rep and independent caches are outside this audit.

The typed saved parent retains mate IDs `[20, 22, 23, 24, 25, 26]` and driving
dimension ID 21, changing its value from 0.13438 to 0.15011 m. Its Config
activity remains 3 and `f1560` remains 3. Fresh ModelHeader/Header2 `fc4` are
both 3; saved ModelHeader `fc4` is 3 and saved Header2 `fc4` is 4. This matches
the existing [save-context count distinction](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/ExternalReferences/NestedSaveHeaderCountsUseDocumentContext.md),
and does not justify changing the fresh constructor. Exact stamp, manager
header, configuration, bounds and stream hashes are retained in the receipt.

The audit entry points are `read` and `audit`, each taking `--root` and `--file`.
Execute each in a fresh isolated Python interpreter against a frozen checkout.
Apply `compare(document, prediction, edited, child_sha)` to the returned normal
document and the independently frozen prediction. Use the frozen child hash
for the original parent and saved child hash for the saved parent; sibling
resolution must remain within their respective directories.

## Scope and next gate

The measured disclosed bundle is vendor loadable and application usable within
the stated profile. This is a genuine fully SDK-generated three-occurrence
construction and editable native lifecycle. It does not establish lossless
parity or held-out acceptance for either original A20/A21 case. Public assembly
writing remains disabled. Other datum families, alignment modes, flexible or
virtual components, additional child definitions and unsupported dimensions
remain closed.

The [original-case protocol](SdkOriginalPlanarMateEvaluation2026.md) still
requires a complete executable semantic translator, independent prediction,
source custody and root-verified freeze before either sealed input is exposed.
