# XY independently drafted live identities

This package proves the bounded live-state validator prerequisite for the strict Fusion source reader. Writer and target conversion acceptance remain unestablished. No native API or model provider was called.

## Rule and actual source evidence

[Rules.md](Rules.md) was recorded before production implementation. The tag-specific discovery set contains 48 XY drafted source states. Six XY `holdout_b` states were evaluated after the rule was recorded and match the unchanged tag and inventory rules. These are parameter holdouts from the same generator; their numerical geometry was previously measured by the separate dual-side geometry work.

`Proof/Receipt.json` binds every original native source, the exact production/test source files and the rule/script hashes. Its readable summary records 68 passing source outcomes: 54 XY drafted states admitted, 12 XZ drafted states refused and two healthy untapered controls preserving their old strict reader outcomes. All 16 counterexamples are real emitted archives, all pass the general typed document reader, and all refuse the new live validator. The exact candidate hashes and refusal diagnostics remain in the receipt. The 84-case archive integration suite passes.

The first malformed attribute-chain, nested-extension and allocator-owner attempts were refused by serialization before an archive existed. They are retained as failures in `Failures.json`, not counted as archive counterexamples. Repairs create class-compatible malformed chains, a genuinely reciprocal typed nested extension and a nullable invalid allocator owner. Existing codec guards were preserved.

## Contracts

`CheckDualLive(Graph, Context, Model, Shape, FirstMm, SecondMm, FirstTaper, SecondTaper)` returns the fully checked `GeometryState`. `Shape` is the actual `CircleShape`; distances are millimeters and tapers are radians. It requires identity XY, profile-plane NewBody, two distinct physical side slopes, positive side distances/end radii and one body. Root-owned graph/parameter/material/mass validation and the separate snapshot validator complete the public projection composition.

The checked live state includes the complete reciprocal allocator/progenitor/body joins, dynamic side and circle IDs, both independently owned cone faces, cap and rim geometry, joint dual feature groups, full-circle seams, opposite coedges and complete entity coverage. Every attribute must be reachable from exactly one geometry owner's head through reciprocal prior/next links. BODY's one timestamp and one body-tag chain are explicitly checked before the snapshot worker may compare a view without those live-only attributes. All source links must belong to the two joint coedges and selected circle; no unknown record or attribute is dropped.

Counterexamples cover wrong side operation, missing/reversed/incorrect joint group, stale body secondary/main operation, wrong cap/far label, cyclic chain, unsupported reciprocal nested attribute, wrong sketch owner/curve, negative timestamp, mismatched body UUID, wrong history end and missing allocator owner. The corruption helper is `tests.Convert.Integration.Fusion.DualSide.Tags.ChangeTagModel.ChangeTagModel(Model, Sample, CaseName)`; it returns a modified typed model that must still cross `EmitParsed` and ordinary `ReadDocument` before testing admission.

## Retained documents

`Documents.tar.gz` preserves exact original bytes of `Discovery.json`, `Holdout.json` and 54 `Proof/Documents/*.json` live-state models. `DocumentArchive.json` records every original path, size and SHA-256. The archive was verified before loose documents were removed. `Proof/Receipt.json`, all counterexample F3D archives and failure summaries remain directly readable. The archive has a scoped `.gitignore` exception; no force-add is required.

For example, read a retained inspection document without unpacking the native archive:

```sh
tar -xOzf re/Fusion/DecodedPromotion20261127/DualAdmissionTags/Documents.tar.gz Discovery.json
```

With the pinned Python 3.14 reader sources and unused output paths, reproduce the inspection and proof:

```sh
PYTHONPATH=src:. pinned_python3 re/Fusion/DecodedPromotion20261127/DualAdmissionTags/InspectTags.py "$PWD" /unused/discovery.json discovery
PYTHONPATH=src:. pinned_python3 re/Fusion/DecodedPromotion20261127/DualAdmissionTags/InspectTags.py "$PWD" /unused/holdout.json holdout
PYTHONPATH=src:. pinned_python3 re/Fusion/DecodedPromotion20261127/DualAdmissionTags/ProveTags.py "$PWD" /unused/proof
```

Production functions contain vocabulary and relational checks, never captured IDs, tables or runtime reads from this package. General frames, start conditions, other operation/profile families and single-side/merged topology are outside this new checker; existing reader routes remain responsible for their qualified families. Native acceptance and the public SDK/CLI replay are separate root-owned evidence.
