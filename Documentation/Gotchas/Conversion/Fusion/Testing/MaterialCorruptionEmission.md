# Material corruption can refuse before archive emission

The high-level `EmitParsed` path validates native material references before it writes an archive.
Replacing an asset ID with a missing target therefore fails in the fixture constructor.
That failure does not prove that the public reader rejects a malformed archive.

For a reader corruption case, retain the original container and its material parts.
Emit the changed typed entity segments with `EmitDocSegment`, then rebuild that container with `EmitContainer`.
The resulting file contains the invalid reference and crosses the real public reader boundary.
Keep every production document and material validation call enabled.

The independent-side admission suite uses this method for missing physical and visual assets.
Its initial high-level emission failures remain recorded with the public proof.
