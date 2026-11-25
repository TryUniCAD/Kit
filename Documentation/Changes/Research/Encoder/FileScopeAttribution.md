# File-driven Fusion stream provenance

## Behavior

File-driven research records the layer used for feature selection and the layer used for physical stream provenance.
If strict Fusion decoding succeeds without usable member spans, the runner can request the partial reader's spans for the same source.
It checks the input digest and bounds each span against the container member inventory.
The strict document still selects experiments. Both successful reports stay in the output directory.

## Usage

Run `kit run fusion --root /path/to/Kit --input part.f3d --directory /tmp/KitFileScope` with a trusted research checkout.
Use a new output directory.
For a decoded input, open `FileScope.json` and check `feature_layer`, `provenance_layer`, and `unattributed_stream_ranges`.
The `provenance_layer` field is null when no valid member span is available.
Each interval uses a zero-based start and an exclusive end in an uncompressed stream.
See the [file-driven research procedure](../../../Tasks/ResearchCommandLine.md#start-research-from-a-cad-file).

## Evidence and limits

At `c4e8a34186`, strict and partial SDK processes read the same pinned RequestedCorner and SavedCuboid files.
Strict reported zero physical spans on both inputs.
Partial reported 61 spans covering 11,067 uncompressed bytes for RequestedCorner and 28 spans covering 6,219 bytes for SavedCuboid.
A cited span establishes where a reader found data. Its presence does not qualify every field in that range.
Native conversion acceptance and whole-file understanding still require separate evidence.

See the [strict Fusion provenance gotcha](../../../Gotchas/Research/Readers/FusionStrictProvenance.md).
