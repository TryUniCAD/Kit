# Preserve the saved two-stock configuration helpers

The internal SOLIDWORKS 2026 two-stock presentation check accepts a Sheet-Metal Master with an empty body list when Config-0 selects its direct `f1018` lane with `f1014=1`. The existing `f13f8` Exploded Views manager still resolves through the linked archive map. Both helpers retain their public rows beside the six persisted cabinet and environment members and all 23 feature roots.

The disclosed edited save retains all 31 public rows in order. The original retains all 30. Eleven isolated Python processes checked both saves before and after this presentation change and refused seven altered graphs. Each process recorded zero external access attempts after imports. The isolated presentation proof preserved the existing public read results and stock-mode refusal. The later saved-stock tolerance change qualifies the complete saved read path.

The proof reads only the two disclosed checksum-bound saves. Pass the original source as `--selected` and the native edited derivative as `--edited`. The optional `--baseline` arm measures the original implementation on the base checkout.

```sh
python3.14 -I -B re/tooling/sw2026/throughsource/ProveStockTree.py \
  --selected /path/to/ThroughMultiStock03/DisclosedNative/ThroughMultiStock.SLDPRT \
  --edited /path/to/GeneratedTwoStockGraph01/NativeAfterEdit.SLDPRT
```

[Exact process receipt](../../../../../re/solidworks/measurements/2026/TwoStockSavedPresentation01.json) ·
[Presentation guide](../../../../Reference/Research/Solidworks/Construction/ThroughAllPresentation.md) ·
[Configuration helper gotcha](../../../../Gotchas/Conversion/Solidworks/Model/Presentation/EmptyDirectSheetMetalMaster.md)
