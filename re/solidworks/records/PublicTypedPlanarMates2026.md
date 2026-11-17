# Public typed planar mate reads in SOLIDWORKS 2026

Normal public reads pass for all six disclosed assembly/child pairs. Three native successes remain successful and three generated files previously rejected for empty entities now have two real occurrence selections and valid neutral mate rules. A frozen 42-process comparison preserves the six independent projections, deferred component behavior, and all six child document JSON results. This is a reader integration result, not a new native writer or held-out family acceptance.

| Ownership | Value |
| --- | --- |
| Task | `B04-SW2026-PUBLIC-PLANAR-MATES` |
| Owner | `/root/assembly_occurrence` |
| Delivery | PR #121 |
| Scope | Ordinary version-19000, one configuration, one aligned coincident/parallel/positive-distance mate, two direct resolved part occurrences, principal-plane endpoints |
| Dependencies | [Typed MatesList codec](SdkMatesListCodec2026.md), SDK linked Config/Resolved maps, shared Header2/ModelHeader identities, independently loaded child files, existing native assembly occurrence index and planar projection |
| Exit for this tranche | Six public read successes with ordered occurrence/datum parity, unchanged legacy fallback and child reads, generated process regression and strict physical mismatch rejection |
| Remaining product boundary | Other configurations, mate families, options and reference kinds, broader topology and native/held-out writer acceptance |

## Cause and integration

The legacy reader extracts endpoint selection strings from a mate stream. A17/A18/A19 retain such strings. The three fully generated counterparts retain their actual resolved plane wrappers and occurrence chains, but omit optional display strings. The legacy parser returns zero entities and the public document validator rejects the resulting mate. The missing strings do not mean the native selected references are absent. [Specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/SelectionStringsDoNotDefineMateEndpoints.md)

The `AsmDoc` hook runs after the existing legacy mate/payload/group construction. The new `Core/TypedMates` modules replace that result only when the complete ordinary profile passes. Existing public mate/entity IDs, owner definitions, list ordering, payloads, groups, component resolution and filtering remain owned by their existing implementations. The replacement changes the source entity from optional text to the actual child plane ID and supplies the ordered occurrence path. [Entry point](../../../src/convert/adapters/solidworks/Core/TypedMates/WithTypedMates.py)

The reader does not search for a similar model by filename. It reuses the physical source paths and component documents already resolved under the caller's read options, then checks each child's physical SHA against the loaded document. A unique basename/configuration key is only an index into that verified set. The native shared file identity, creation fields, selected configuration, update stamp and datum owner must also agree. Ambiguous keys, stale bytes, wrong child identity or absent public datum fail typed admission. `resolve_components=False` leaves the legacy route untouched and performs no additional typed child reads.

An unqualified outer profile stays on the original route. A qualified-profile attempt that cannot complete falls back only to the already constructed legacy data and reports `status=unsupported`; it never marks a partial graph admitted. If that legacy mate has no entities, the reader raises with the exact typed rejection cause. The ordinary document validator remains unchanged.

## Exact graph and semantic guards

The new reader uses the SDK's actual ModelHeader → Config-0 → CMgr → ResolvedFeatures → MatesList ownership chain. Its complete mate stream must re-encode to the exact original bytes. The shared planar projection verifies the resolved wrapper's mate ID and endpoint ordinal, its actual assembly owner, one-hop external-feature identity and backlink, occurrence membership, child file/configuration/stamp and actual child `moRefPlane_c`. [Projection rules](PlanarMateSdkProjection2026.md) · [Chain proof](PlanarMateReferenceChains2026.md)

Every selected neutral plane must also exist under the same ID and name in the already loaded public child document. The cache check applies the actual occurrence's proper rigid row-vector transform to the selected native principal plane origin and normal, then compares both with the stored wrapper. It rejects scaling, shear, reflection, nonfinite data, malformed affine matrices and contradictory plane geometry. Its coordinate comparison uses relative tolerance `1e-10` and absolute tolerance `1e-12`; this is a consistency check, not a native mass-property acceptance tolerance. [Endpoint transform rule](AssemblyPlanarEndpointConstruction2026.md)

The promoted input branch is explicit aligned state `f3b4=1`, two endpoints and the ordinary empty auxiliary collections/null auxiliary owners. A distance requires `(f4c0,f4d8,f4dc,f4e0,f4f4)=(1,1,3,3,0)` and a finite positive driving value reached through the real display/feature-dimension/length-parameter chain. The neutral value is that length in metres multiplied by 1000, with unit `mm`. Solver status `f3b8` is independent and admits the constructor and solved states 0/1. [Mode construction proof](PlanarDistanceMateConstruction2026.md) · [Native command translation](PlanarMateInputTranslation2026.md)

Mate and distance-dimension persistent IDs must be assigned, less than the actual header allocator, and distinct from each other and existing model features. The existing resolved-root feature index alone is insufficient: Config-0 owns the actual `moReference_c` occurrence IDs. The collision set explicitly combines both typed owners. A physical negative changes a mate's ID and both wrapper owner IDs to an occurrence ID; it rejects before any neutral replacement. The native registration allocator is documented in [mate publication](CoincidentMatePublication2026.md). The driving length also requires the ordinary local handle branch, null `fe8/f100`, and parameter alternate-value flag `f68=0`; contextual/alternate values are not silently projected as the local scalar. [Shared local parameter boundary](TypedResolvedRead2026.md)

The node update word guard admits the native constructor's pending-update word `1` and the separately proved bit-8 update word `0x100`. It does not interpret either as suppression. The exact inherited getter `0x4b28e090` returns `f0c & 0x100`; setter `0x4b30f9f0` changes only that bit. An original-PE read independently verifies both slots on all three concrete tables: coincident `0x4cfa46e0`, parallel `0x4cf9fe10`, and distance `0x4cfafd18`, at offsets `+0x230/+0x238`. Its source-bound receipt has SHA-256 `39b212e1f833f658de74c5a810de4806dbc8a4c21683b065ff094ce94427db0d` and is reproduced in the sanitized receipt below. These are the independently recorded lifecycle operations, not values selected as defaults from a file. Other node words remain unqualified here. [Node lifecycle and pinned image evidence](CoincidentMateLifecycle2026.md)

No additional native predicate was invented during this source integration. A REA status check found no open target, and the existing native lifecycle record answered the specific flag question. No Hopper document was opened or closed, no native application ran, and no original sealed inputs were accessed. The prior 19-file MatesList tranche remained byte-exact.

## Evidence and reproduction

The current and baseline import trees were frozen before execution. The baseline differs only by the exact prior `Core/Adapter.py`; all common dependencies are identical. The 4,768-file snapshot binds base revision `377d385ca8373e1efdbf7deb2cbbf2b95eb7f9c7`, with freeze manifest SHA-256 `6d0ed34779cd9ac0f847024ea0ca0d6d412eadf773f99b9bb16caef7dae1a8bb`. The six-pair process receipt has SHA-256 `d36fdf54f7ff25cfb146917ef52950d3ed9db2d14122e8902691e492e5406ba7`.

For each pair, seven independent Python 3.11 processes perform the current public read, independent research graph projection, previous public read, previous/current deferred-component reads, and previous/current child reads. All six current documents validate. The three prior native successes remain successful, while the three previous generated failures reproduce `has no entities`. All six current ordered occurrence/datum/frame/value projections match the established independent graph path. All six deferred results match their baseline results exactly, including failures. All six ordinary child JSON results remain identical. The 42 process identities are distinct and all 12 original file hashes remain unchanged.

The permanent generated checks construct fresh native bytes from a neutral input through the guarded research composer, then invoke normal public SDK reads in fresh processes. The positive check independently requires reverse endpoint order, two actual occurrence paths, the real child Right Plane and the authored driving length. Diagnostic copies independently alter list framing, prefix, child stamp, assembly owner, endpoint ordinal, selected datum, plane cache, distance options, Config tail, and child identity. Further copies test an unassigned mate ID, occurrence/mate ID collision, dimension/mate ID collision, and a nonlocal distance handle. All fourteen copies reject through the public route, followed by a healthy original generated control. These copies have `writer_output_count=0`; they are diagnostics and receive no writer acceptance credit.

The final generated source snapshot differs from the six-pair snapshot only by the diagnostic preparer's expected error text for a nonlocal handle. Every SDK source byte is independently checked identical. Its complete freeze SHA-256 is `e95cd446c60b1a517aab59000f0b03ebb89c198acf451db18c0ab9259b99dfad`. The completed generated process receipt has SHA-256 `a237703d726dd92adbcc850c9110bfb54a4fcaf6d9473172113a54a68571a860`. It also binds an additional neutral case whose two aligned occurrences have authored basis vectors `(0.6,0.8,0)` and `(-0.8,0.6,0)`. Its predicted normals, origins, selection order and 0.06725 m driving length were locked before generation. Public readback matches those independent values. An earlier speculative input rotated only one occurrence and the existing composer refused its nonaligned planes before any public read; that failed preliminary input remains private and unchanged. No writer change followed that refusal.

This tranche does not replace the existing instance flag or broad assembly projection. Its report says `full_selected_mate_graph`, not full assembly coverage. Fixed-state recovery and other assembly fields retain their independent coverage requirements.

[Sanitized public receipt](../measurements/2026/PublicTypedPlanarMates01.json) records exact input/code/proof hashes and verification limits. The normal complete suite contains `tests/Convert/Solidworks/Research/Assembly/TypedMates/PublicMatesTests.py` and `PublicMateRejectTests.py`. Black, Ruff, Mypy, Pyright and steering are checked locally on the scoped source/tests. The configured Pyright reports three preexisting unrecognized repository setting names; its source analysis reports zero diagnostics. Remote CI remains an independent gate owned by the parent.

With frozen current and baseline roots, the six-pair check is:

```sh
uv run --isolated --frozen --extra dev --python 3.11 python -I -B re/tooling/sw2026/CheckPublicMates.py \
  --root /absolute/path/to/FrozenCurrent \
  --baseline-root /absolute/path/to/FrozenBaseline \
  --cohort /absolute/path/to/InputManifest.json \
  --output /absolute/path/to/UnusedPublicProof
```

The tool retains full current/projection documents privately and emits a sanitized comparison receipt, plus the complete source manifest. It refuses an existing output directory and verifies source and original input identities after all processes. No native vendor acceptance, full drawing/assembly scope, or held-out generalization follows from these source-only reads.
