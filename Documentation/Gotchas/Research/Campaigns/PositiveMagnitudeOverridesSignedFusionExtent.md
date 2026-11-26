# Positive magnitude assignments reverse native Fusion depths

Expected: assigning a positive recipe magnitude preserves the direction chosen by the native builder.

Observed: overwriting `depth_mm` or `cut_depth_mm` with a positive expression removes the native negative sign. P04 cuts then remove no stock, and negative P03 bosses grow in the positive direction. Successful rebuild or export alone does not detect either error.

The existing sample builder now retains each depth parameter sign while assigning the requested magnitude. Baseline and candidate receipts, positive controls and parameter holdouts are in [signed-depth qualification](../../../../re/Fusion/Reconstruction/SignedDepth/README.md). Body count, volume, centroid, feature health and export/reopen geometry must all pass before a control is used for inference.

The corrected builder saves plain negative millimeter expressions. The strict reader previously required the wrapped spelling and rejected those valid controls. It now accepts both spellings while preserving numeric agreement, units and the original expression. That repair does not remove the remaining conversion qualification boundary or qualify cut and YZ semantics.
