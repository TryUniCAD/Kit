# Source-selected dual extrusion snapshot frames

The bounded snapshot rule passes six XZ discovery sources and six reserved `holdout_a` sources without refitting. Production correspondence now passes all 68 campaign archives when supplied an independently qualified source frame. The existing identity-frame default still passes 56 XY archives and refuses all twelve XZ archives. No native output or conversion acceptance is established.

`FrameRules.md`, `ProveFrameRule.py` and `RuleSeal.json` preserve the pre-implementation rule and exact dependency hashes. `Evidence/DiscoveryProof.json` and `HoldoutProof.json` retain the frozen prediction results. These files are unchanged after unsealing. The historical dependency hashes require the parent's accepted Git binding for replay against that earlier SDK checkpoint; current implementation changes are recorded additively rather than rewriting the seal.

The source-selected sketch frame is separate from BODY bookkeeping. World solid and profile carriers remain in their original state. A certified identity BODY comparison uses the sibling's complete `DualBodyView` check, while original references and transform records remain available to canonical comparison and disjoint coverage. The double-sided profile sheet uses the qualified sketch frame; the single-sided sketch sheet remains local XY. The selected sketch UCS and owned DRMatrix agree with the supplied frame, and occurrence identity remains required. Equivalent empty/explicit identity matrix representations retain the previous default contract.

`CheckDualSnaps` accepts an optional sixth `Transform` argument. Its default is identity, so unrelated callers retain the original boundary. The parent owns public dispatch, geometry, mass and placement-policy composition. The sibling owns `ReadDualFrame` and the actual origin-plane recipe/update ownership guard; this child changes no shared graph policy.

`Counterexamples/` retains six encoded full `.f3d` files with incorrect BODY rotation, translation, reflection, identity-record sharing, profile normal or world/local sheet placement. Every file still parses as typed `GeometryState`; none is made to pass by dropping records. Initial attempts and the actual source hashes remain in `Evidence/`.

Run the current implementation proof from the repository root with the locked Python 3.14 environment and an unused output path:

```sh
PYTHONPATH=src:Cli python3.14 re/Fusion/DecodedPromotion20261127/DualFrameSnapshots/ProveImplementation.py /tmp/FrameImplementationNew.json
PYTHONPATH=src:Cli python3.14 -m pytest tests/Convert/Integration/Fusion/DualFrameSnapshots tests/Convert/Integration/Fusion/DualSnapshots -q
```

The combined archive suite passes 93 cases. The proof separately records 68 qualified source successes, 56 unchanged default XY successes, twelve retained default XZ refusals and six encoded counterexample refusals. Black, locked Mypy and steering checks pass the 17 owned source/test files. `ImplementationReceipt.json` binds the working source and dependency hashes; the parent supplies final accepted revision mapping and composed public SDK/CLI evidence. Models stayed disabled and no native API was called
