# File-driven Fusion stream provenance

## Behavior

File-driven research records the layer used for feature selection and the layer used for physical stream provenance.
If strict Fusion decoding succeeds without usable member spans, the runner can request the partial reader's spans for the same source.
It checks the input digest and bounds each span against the container member inventory.
The strict document still selects experiments. Both successful reports stay in the output directory.

## Usage

Run `kit run --root /path/to/Kit fusion --input part.f3d --directory /tmp/KitFileScope` with a trusted research checkout.
Use a new output directory.
For a decoded input, open `FileScope.json` and check `feature_layer`, `provenance_layer`, and `unattributed_stream_ranges`.
The `provenance_layer` field is null when no valid member span is available.
Each interval uses a zero-based start and an exclusive end in an uncompressed stream.
See the [file-driven research procedure](../../../Tasks/ResearchCommandLine.md#start-research-from-a-cad-file).

## Evidence and limits

At `c4e8a34186`, strict and partial SDK processes read the same pinned RequestedCorner and SavedCuboid files.
Strict reported zero physical spans on both inputs.
Partial reported 61 spans covering 11,067 uncompressed bytes for RequestedCorner and 28 spans covering 6,219 bytes for SavedCuboid.
A Windows installed-wheel run at `d3b2cb982c` passed two CLI cases in 84.79 seconds on Python 3.14.6.
RequestedCorner used strict features and 11,067 uncompressed bytes of partial provenance across the 30-member inventory.
Both saved reports matched the source digest. The strict blind cut stayed in the list of features without an experiment.
The regression checks each reported gap against raw ZIP member sizes and the cited bytes from the partial report.
The P04 through-all control retained its partial feature path and its existing experiment.
Both cases reported incomplete coverage. No native CAD application was used.

The Windows CLI test roster includes the RequestedCorner case and installs locked NumPy for its offline inference worker.
Local collection selected the case in shard 2 of the 85-case Windows roster.
The Linux compatibility suite and complete merge-queue plan collect the same case through the existing test discovery rules.
The merge-group runner installs the locked codec dependency group for file scope tests on shards without research inference tests.

A cited span establishes where a reader found data. Its presence does not qualify every field in that range.
Native conversion acceptance and whole-file understanding still require separate evidence.

See the [strict Fusion provenance gotcha](../../../Gotchas/Research/Readers/FusionStrictProvenance.md) and [Windows worker dependency gotcha](../../../Gotchas/Research/Supervisor/WindowsWorkerDependencies.md).
