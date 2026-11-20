# Single-dimension control experiments

A SOLIDWORKS file run now searches its local control corpus for a second save with the same named feature IDs, configuration stream, display settings and dimension names. When exactly one declared dimension changes, it checks both saved values against their own named scalar records. It then intersects the locations of redundant values relative to each scalar. The absolute offsets can differ between saves.

For the P05 revolution fixture, the decoder found the 360° baseline and 90° edited save automatically. Three other declared dimensions retained their values. The angle moved from offset 16262 to 16710. Its copy stayed 538 bytes after the scalar in both files. Both measurements matched the independently recorded SOLIDWORKS reopen values.

When the corpus contains only one value for an unresolved field, `next_control_edits` identifies the feature, parameter, baseline and a proposed change in native units. The turbine-wheel request identifies `D3@MatrizC2` and proposes changing its sweep from 360° to 180° in a separate save. Feed an independently saved edit back using `--control`. A proposed edit is pending until a corresponding file exists.

Run `kit run solidworks --input <part> --directory <new-directory>` and inspect `Input-dimension-evidence.json`. The comparisons describe the measured dimensions in these files. Other model properties may also have changed.
