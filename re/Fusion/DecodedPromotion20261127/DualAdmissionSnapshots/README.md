# Dual circular extrusion snapshot admission

The snapshot validator accepts all 56 XY saved archives in the existing two-sided draft campaign: 54 drafted states and two untapered controls. Six XY states come from the campaign's holdout_b model. The separate holdout_a model is XZ and remains refused. Twelve XZ states continue to refuse. These are bounded reader results; generated-file native acceptance and full conversion remain unproven.

The [recorded rules](Rules.md) precede implementation. Eight focused production modules under `src/convert/adapters/Fusion/Native/Circular/DualSnapshots` independently validate saved solid/profile/sketch identities, selected circle geometry, identity placement, scoped source caches, passive BODY scan order, complete rooted solid correspondence, sheet source links and disjoint entity coverage. `CheckDualSnaps(Model, Graph, Context, Shape, LiveState)` requires a live state independently validated by the sibling live-history component. It does not substitute snapshot data for live feature history.

`Evidence/SourceCorrespondence.json` records the initial independent graph experiment. `InitialValidator.json` and `ScopeValidator.json` retain earlier successful checkpoints. `FinalValidator.json` binds the final production module hashes and all 68 source archive hashes. `Verification.json` binds integration helpers, the gotcha and exact verification. The parent must map these working-file hashes to its final accepted publication revision.

`Counterexamples/` retains five encoded full `.f3d` files with wrong saved identity, feature tag, sketch source, body order or carrier point. Each still parses as a typed `GeometryState` and refuses at the intended validator boundary. These are mutations of an existing committed native source for research; production contains no saved data or per-case identity values.

Run from the repository root using the locked Python 3.14 environment and unused output paths:

```sh
PYTHONPATH=src:Cli python3.14 re/Fusion/DecodedPromotion20261127/DualAdmissionSnapshots/InspectCorrespondence.py /tmp/CorrespondenceNew.json
PYTHONPATH=src:Cli python3.14 re/Fusion/DecodedPromotion20261127/DualAdmissionSnapshots/VerifySnapshots.py /tmp/SnapshotProofNew.json
PYTHONPATH=src:Cli python3.14 re/Fusion/DecodedPromotion20261127/DualAdmissionSnapshots/PackSnapshots.py /tmp/SnapshotNegativesNew
PYTHONPATH=src:Cli python3.14 -m pytest tests/Convert/Integration/Fusion/DualSnapshots -q
```

The focused suite passes 73 real archive cases: 56 XY successes, 12 retained XZ refusals and five encoded counterexamples. Locked Mypy 2.4.1, Black and existing steering checks pass for all 14 production/test modules. The parent owns composed public SDK/CLI testing and Pyright. No native process, model provider, vendor software or private transport configuration was used or added
