# Decoder exports do not share directory identities

## Expectation

Two decoder output directories can appear suitable for automatic document pairing.
Their JSON files can include documents, receipts, and run summaries.

## Actual behavior

Fusion research exports use source-path hashes for document directories.
Those directories do not identify equivalent SOLIDWORKS designs.
Matching relative filenames can therefore leave every intended design unpaired.
Selecting every JSON file also includes receipts and summaries, which are not codec documents.

## Workaround

Use the bulk command's explicit pair manifest for independently named exports.
Declare the corresponding document paths from each capture or export inventory.
For matching directory layouts, select `--pattern document.json` to exclude sidecars.
This selection does not establish correspondence between differently hashed parent directories.

See [bulk comparison](../../../Tasks/CompareDecodedDocuments.md) and the [Fusion reader output contract](../../../Reference/Research/FusionResearchReader.md).
Document pairing selects the requested designs.
The semantic engine independently finds feature correspondences within each pair.
