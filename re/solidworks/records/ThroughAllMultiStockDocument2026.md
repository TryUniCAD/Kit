# Saved two-stock selected through-all document

This slice advances `B04-SW2026-EXTRUDE-THROUGHALL` on PR #121. It connects the actual three-atom lineage and verified active partition grouping through the ordinary SDK registry. The disclosed save comes from the two-stock native experiment. The source SHA-256 is `748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3`. The matched unrestricted save is `f87568db0dfa361ea44c42def01063c8ed07ea57c8270098cf3c60995e3e3b22`. [Native experiment](ThroughAllMultiStockScope2026.md) · [Atom lineage](ThroughAllMultiStockArchive2026.md) · [Active grouping](ThroughAllMultiStockCache2026.md)

## Admission and ownership

[The saved-part gate](../../../src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/TryStockPart.py) requires B-rep, ordinary version-19000 Config-0 and one actual `Default` manager row selected by both pointers. Configuration, Resolved, presentation and physical grouping qualify together. The row orders cover 23 persisted roots, six members and one empty configuration helper. The native source's two rectangular profiles preserve their four unary line relations and signed Front and Right datums. The cut profile preserves its free circle and actual Front datum. The shared typed binders compare the three profile attachments to their actual linked owners before the existing portable builders consume them.

| Feature | Neutral operation | Ordered inputs | Live driving length |
| --- | --- | --- | --- |
| 32, SteadyStock | Create | 26 | D1 at 12 mm, native dimension 27 |
| 40, MovingStock | Create | 33 | D1 at 10 mm, native dimension 34 |
| 47, ThroughFeature | Cut | 32, 41 | Depthless through all, reversed |

The cut selection references feature 32's historical body. Consumed atom 101, untouched atom 102 and result atom 103 retain distinct identities. World body 2 belongs to MovingStock, atom 102, with 1 region, 1 shell, 6 faces, 12 edges and 8 vertices. World body 6 belongs to ThroughFeature, atom 103, with 1 region, 1 shell, 8 faces, 18 edges and 12 vertices. Both design bodies retain their linked B-rep identity and active partition payload. The delta payload remains available as a separate raw archive payload.

## Verification

Run the disclosed supervisor from the pinned checkout with fresh processes.

```sh
python3.14 -I -B re/tooling/sw2026/throughsource/ProveStockDocument.py \
  --selected /path/to/ThroughMultiStock03/DisclosedNative/ThroughMultiStock.SLDPRT \
  --unrestricted /path/to/ThroughAllBodies02/DisclosedNative/ThroughMultiStock.SLDPRT
```

The receipt SHA-256 is `d415f032e096010054d3215af9625aa99a110a3a7ca145849840e4073b380abd`. It binds the 13 implementation files, supervisor, source hashes and baseline `f815b77a27d78a3654f9e7c084ce0921c01f692a`. Default and explicitly selected reads yield the same 30 ordered rows, live parameters and analytic topology as the active saved grouping. The real unrestricted save stays on the existing unsupported compatibility route. Copied producer identity, a crossed datum and one shared active depth each refuse positive admission at the associated owner. Disabling B-rep and requesting raw extraction retain the existing output modes. The absent configuration is rejected. All nine stdin-only worker processes observed zero external access attempts after imports. Scoped steering and Mypy passed and the Core donor scan was clean. This evidence qualifies the saved reader slice. Cache-free synthesis, unrestricted multibody semantics, rollback/delta decoding, complete source presentation, a native writer and held-out generalization are outside the measured boundary. [Exact receipt](../measurements/2026/ThroughAllMultiStockDocument01.json)
