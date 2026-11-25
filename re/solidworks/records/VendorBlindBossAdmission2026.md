# SOLIDWORKS 2026 vendor-saved blind-boss admission

This record identifies the reader and source-admission boundaries for ordinary
version-19000 parts with one unconstrained Front-plane polygon and one driving
blind boss. The [first encoder milestone](../../../Documentation/Changes/Research/Solidworks/SolidworksEncoderRoundTrip.md)
qualifies the Kit-generated cold family. Its
[source-admission record](../measurements/2026/EncoderVendorSourceAdmission.json)
records separate refusals for vendor-saved parts.

## Dependency comparison

The first encoder revision tested was `c4e8a34186bdd173dad37d843b79bc8a3a59ebb9`.
The independent reader comparison used the exact [PR 121](https://github.com/TryUniCAD/Kit/pull/121)
head `c0a401a607759fb0c2589647c2a22af65ebb7ce1` from a separate checkout.
Both used Python 3.14.6 with zlib-ng 1.3.1. The files came from SOLIDWORKS 2026
SP04.1 build `34.4.1.1011`. The comparisons ran with zero CAD launches.

| Discovery input | SHA-256 | PR 121 linked profile | PR 121 text state |
| --- | --- | --- | --- |
| Author04 baseline source | `02cc9e0ea4b2cebe3b99d908180b409f1ceeffd5cbef13d2a9685caaf4d8ca7d` | 4 lines, 1 loop | Complete |
| Author04 baseline depth control | `460feca54879f2f5095e749a08cbd1d28cfa4a8ae0e7dd4feba924c65b1c013a` | 4 lines, 1 loop | Complete |
| Author04 concave source | `c3e2dbd133fbb35c897178a9650e60b9db000b8ebbd4b301eac05599a3f5c25f` | 7 lines, 1 loop | Complete |
| Author04 concave depth control | `605effedfbcff4826e5e8b3f8f9c9650e8ed93199e88a46007e7bde132306edb` | 7 lines, 1 loop | Complete |
| Discovery01 initial save | `c979ed48249f02a254578bc31ab04365fca5bc61264325af7673406f0b12f246` | 5 lines, 1 loop | Complete |
| Discovery01 first forced save | `ed5193322a7166ed8d0cdca9e0fe3abe46233e11c7368f0b42fdabaed60c3269` | 5 lines, 1 loop | Complete |
| Discovery01 document custom text | `fc27be9236f286777726cc2dcc2b38049295b2d52d4375c583ebf3823e49f5f2` | 5 lines, 1 loop | Unsupported owner |
| Discovery01 profile-only contrast | `acedc181f6da5b8d4a0a17521d957b89250e71a1be865533958bd2f5f298195c` | 5 lines, 1 loop | Complete |
| Discovery01 depth-only contrast | `49b9afe5366d6af21dd848f7bcb68cb81d01a6f7f2b2a1dc404778c66db3467e` | 5 lines, 1 loop | Complete |

At the encoder baseline, each of the four Author04 inputs retained 26 feature
rows and two payloads. `ReadNativeLink(archive, 0)` stopped at CMgr class
`moLinkedAtomIdNode_c` schema 1. The baseline sketch exposed three typed lines,
one unresolved entity and zero closed profiles. Both reconstruction and depth
edit refused before candidate generation for all four sources. Applying the
legacy empty-manager reader verified the 138-byte manager and all text scopes
for these inputs. The ordinary version-19000 text check still reported the
manager as unsupported.

At the PR 121 head, `ReadNativeLink(archive, 0)` and `ReadSldprt(path)` completed
for all nine cases. The public timeline contained 19 features each, and a
typed closed loop had the complete observed line count. The complete literal
text status appeared for the eight empty cases. The custom-text negative
retained a diagnostic at the populated `moFilePropContainer_c` child, and
the SOLIDWORKS API saw its resolved literal after a fresh open. The negative
contained the same one-solid geometry as the calibration baseline. The
initial save and first forced save differ in Header2 self-path initialization,
so this pair describes first-save behavior and is unsuitable for establishing
the warmed no-op noise floor.

The recursive feature API confirmed six extra baseline SDK rows as actual
subfeatures, with matching native IDs. Notes and its end tag belong to
Annotations. Ambient and the three directional lights belong to Lights and
Cameras. Sketch1 appears at top level and as the boss's owned subfeature with
the same native ID. The API did not expose a recursive feature for `Exploded
Views 19`. Its keyword-only observation has no recovered feature record span.

The first encoder's reader reported 13.37 and 21.46 mm for the two Discovery01
depths through display text. PR 121 resolved their `moLengthParameter_c.f58`
values at the boss's `f818.f18` slot as 0.013371 and 0.021463 m. Both the
public driving parameter and the blind extrusion definition then agreed with
the SOLIDWORKS API's rebuilt values of 13.371 and 21.463 mm within binary64
conversion precision. The encoder depends on that typed parameter path.

## Active body evidence

`DecodePartition` produced one `partition` packet and one `deltas` packet from
each Author04 `Contents/Config-0-Partition`. `DecodeBrep` on the active packet
produced one solid body with no model validation errors. The planar bounds and
mass readers produced the following results from the decoded geometry. The
delta digest stayed constant across the depth edit for each source profile.

| Author04 case | Faces / edges / vertices | Volume (mm³) |
| --- | --- | --- |
| Baseline source | 6 / 12 / 8 | 7584.30 |
| Baseline depth control | 6 / 12 / 8 | 10531.10 |
| Concave source | 9 / 21 / 14 | 7316.96 |
| Concave depth control | 9 / 21 / 14 | 9166.88 |

All nine public reads on PR 121 returned zero per-body face, edge and vertex
counts and no per-body volume. For the Author04 four-edge and seven-edge
sources and Discovery01 first forced save, `ReadBodyOwner` resolved native
feature 32, and its `ReadOutputAtom` was the actual `ReadMgrAtom` object.
The boss's public `output_body_ids` was empty in all three.

The exact-cache comparison refused the four-edge source. Its public model
already had a design-body ID, and removing that one difference still did
not make the compared graphs identical.
It accepted the five- and seven-edge source geometry, with 203 and 255 typed
kernel nodes respectively. The body-name proof then refused them at its
six-face requirement. The typed kernel records and archive atom identity
provide inputs for a fuller boundary proof. Completing that proof requires
the linked shell and ring inventories, matching sketch and extrusion owners,
and the contents of both physical payloads.

The four Author04 cases and five Discovery01 cases are calibration inputs.
A separately authored, healthy source was sealed before rule derivation at
SHA-256 `0de0b983f46e1a0a2553efd192f916b13227b23a95a62b806e1795a7fa8ff3f1`.
No vendor-authored part received source admission or a writer receipt in
this comparison.

## Warmed save control

Discovery02 used the same saved title and initialized self locator for both
no-op snapshots. The native oracle rebuilt and reopened them with matching
geometry. Nine of 36 clear streams had different digests: the exchange
configuration header, CMgr header, Config-0, ModelHeader, active partition,
Header2, biography, SOLIDWORKS information and core properties. The active
partition differed even though both `ResolvedFeatures` and `Definition`
remained byte-identical. `CusProps` and `docProps/custom.xml` changed only
in the custom-text contrast. These exact comparisons identify streams to
investigate before declaring cache ownership.
