# Independently drafted circular side geometry

Task child: bounded offline geometry prerequisite for `A16-DecodedReadWrite20261127`. Owner: delegated Fusion worker, exclusive production directory `src/convert/Geometry/Extrude/Circular/DualSide` and integration directory `tests/Convert/Integration/Fusion/DualSide`. Root owns shared readers, integration, registers and PR #397. No native API or model provider was called.

## Source and implementation binding

The source is the committed `re/Fusion/TwoSidedDraft20261127/Capture.json` and its 68 hash-bound native archives, originally delivered by PR #394. The existing campaign records Fusion 2706.1.17, 101 source observations, independent first/second distance and signed taper edits/restorations, a swapped-side counterexample and two combined parameter holdouts. These remain same-generator holdouts, not independent generator lineages.

The original production base is `93b24ed0feeb033be95fe91622fb615f519dcd65`. `Receipt.json` binds the source capture and the original 16 production/integration Python files by SHA-256. `Documents.tar.gz` retains the exact original bytes of all 202 fully typed neutral BRep documents from the original and mass-qualified replay; `DocumentArchive.json` binds every member path, size and digest. The archive was read back and compared before loose JSON files were removed. These documents are newly computed from actual API controls; no source body payload, template or recorded coordinate table is loaded by production code.

## Confirmed bounded rule

Each side starts at the same profile radius `r` and profile plane. Side one travels `a` along the actual sketch normal, and side two travels `b` against it. Their independent taper parameters store radians, despite display units `deg`:

`r_upper = r + a*tan(first_taper)`

`r_lower = r + b*tan(second_taper)`

The stations are `-b`, `0`, `a`. A positive draft expands away from the profile on its own side. This creates two frusta sharing one circular rim, with no internal cap. The exact volume and axial first moment are the sum of the two frustum integrals, and the exposed area contains two lateral areas plus the two far caps. The centroid is transformed through the actual API sketch basis and center. Bounds include the profile radius at the joint, which can exceed both end radii.

Independent positive drafts can produce a concave hourglass meridian. Existing `BuildFullSweep` requires a strictly convex meridian, so it cannot build that valid shape. `BuildDualSide` validates this specific ordered radial graph and reuses the lower-level periodic ring, exact cone/cylinder/plane face and closed-shell builders. It does not change the shared revolve convexity guard. Equal signed world slopes merge the intermediate point; both untapered source controls consequently retain one cylindrical side face.

Actual active native journals corroborate the nonzero-draft topology: four faces, three full circular rims, two signed cone carriers and two planar end caps. The two cone axes point in opposite extent directions, their origins share the profile center, and their sine/cosine values retain their own taper roles. The source feature's reciprocal first/second/taper bindings and body serializer ownership are checked independently of the generated solid.

XZ source journals contain an explicit identity `TransformNode`. The archive integration checks prove all its columns, translation, scale and rotation/reflection/shear flags before creating an unplaced comparison view. They never modify the retained source model or ignore an arbitrary placement.

## Recorded verification

`ProveDualSides.py ROOT UNUSED_OUTPUT` is deterministic offline evidence preparation. It uses actual measured API controls and preserves documents, per-comparison outcomes and source hashes. Current results:

- 101 observations, 1,313 comparisons, zero numerical failures or errors
- 68 native archives, 68 passing full-reader/typed-journal comparison cases
- 69 real archive integration cases passed after the final cap, seam, reciprocal-coedge and JSON checks, in 6.41 seconds
- Black and scoped Python steering passed; locked Mypy 2.4.1 passed all 16 files

The integration comparison covers complete neutral JSON restoration, BRep validation, volume, area, centroid, bounds, native reciprocal parameter ownership, current-body serializer binding, saved cone/rim/cap carriers, face counts, closed seam endpoints and reciprocal coedges. The swapped-side case has equal volume and opposite axial centroid; volume agreement alone cannot swap the taper roles. Source and held-out archives share this same path.

The initial archive run passed 43 cases before refusing an explicit XZ identity placement. Validation of that node resolved the comparison setup without relaxing any production guard. Initial naming/splitting and type-check errors were repaired; `Failures.json` retains these attempts. Native capture and API health were not remeasured.

## Remaining gaps

The scalar role and analytic geometry rules are confirmed only for the measured circular, untapered-or-positive-end-radius, two-sided distance family and tested principal frames. This helper constructs neutral geometry; it does not admit new strict-reader inputs, write a native file, qualify arbitrary neutral edits or establish target acceptance.

Production `ReadParameters` still requires a zero second taper. `ProjectSpan` and its current-body/snapshot policy still assume one cylindrical or single-frustum side, and remain unchanged. Before integrating this helper there, prove the whole persistent face/edge/feature tag graph, operation/progenitor attribution at the shared joint, complete saved solid plus profile/sketch sheet correspondence and material/graphics obligations, then integrate the independently proven mass/inertia check. The integration checks here do not claim complete snapshot, graphics or persistent-name coverage. Full first/second taper projection must preserve both distinct owned controls rather than replacing their values by a fitted single cone.

[ProjectionPlan.md](ProjectionPlan.md) lists exact shared paths and the remaining validation gates for root coordination. No shared reader changes are included.

General profiles, collapsed cones/apices, arbitrary occurrences and other start/Boolean conditions remain refused or outside this evidence. Native target load/edit/restore/rebuild/save/fresh-process reopen of Kit output is still required for writer or conversion claims. No existing read-only or qualification marker was removed.

## Complete mass tensor extension

`DualMoments` integrates each linear-radius segment exactly. It computes volume, the signed axial first moment, the radial disk second moment and the raw axial second moment. `MeasureDualMass` rotates the axisymmetric second-moment matrix through the actual sketch axis and translates it from the profile center to the world origin before converting it to inertia. Off-diagonal inertia is the negative raw cross moment, matching `RotaryMass`; density is not applied. Results are in mm⁵, converted by `100000` for the native cm⁵ cache.

`ProveDualMass.py ROOT UNUSED_OUTPUT` preserves every actual cached value and corresponding prediction. `MassInitial/Receipt.json` records 748 passing comparisons across all 68 saved archives: volume, area, three centroid values, three diagonal inertia values and three off-diagonal values. It uses the unchanged `CacheNumbers` relative tolerance `1e-6` and absolute tolerance `1e-8`, only for native numerical caches. All eleven deliberately corrupted cache components refuse with the exact analytic-cache diagnostic after actual archive emission and reading; those counterexample files and hashes remain in `MassInitial/Counterexamples`.

The extension closes the bounded mass/tensor prerequisite. It does not close persistent feature naming, complete snapshots, material/graphics coverage or public reader admission. The historical geometry receipt retains its original source hashes; the only subsequently changed source among those files is preserved byte-for-byte in `HistoricalSources/CheckDualNative.py`. `MassRevision/Receipt.json` repeats the full geometry proof at the current source hashes, including mass validation.

The expanded native-archive integration suite passes all 80 cases, including eleven encoded cache-corruption refusals. Scoped Black, steering and locked Mypy 2.4.1 pass all 21 Python files. `MassValidation.json` binds this final source set, receipts, moved gotcha and change entry. The gotcha now resides in `Documentation/Gotchas/Conversion/Fusion/Geometry/Drafting/` to preserve the direct-directory bound. The parent subsequently formatted the changed Markdown with cached Prettier 3.6.2. Pyright remains a remote verification obligation.
