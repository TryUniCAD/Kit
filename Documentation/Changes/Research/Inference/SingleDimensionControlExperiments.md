# Single-dimension control experiments

A SOLIDWORKS file run now searches its local control corpus for a second save with the same named feature IDs, configuration stream, display settings and dimension names. When exactly one declared dimension changes, it checks both saved values against their own named scalar records. It then intersects the locations of redundant values relative to each scalar. The absolute offsets can differ between saves.

The P01 discovery rectangle yielded two separate comparisons. Width changed from 40 to 41 mm and height from 20 to 23 mm. Both comparisons matched native reopen measurements. The P05 revolution family is reserved for evaluation. Its earlier observed copy displacement cannot train a reader.

When a field needs another discovery control or a different value, `next_control_edits` can identify the feature, parameter, baseline and proposed native value. The turbine wheel identifies `D3@MatrizC2` and proposes a sweep of 180°. Author the controlled variation in a discovery family. See [discovery control eligibility](DiscoveryControlEligibility.md).

Run `kit run solidworks --input <part> --directory <new-directory>` and inspect `Input-dimension-evidence.json`. The comparisons describe the measured dimensions in these files. Other model properties may also have changed.
