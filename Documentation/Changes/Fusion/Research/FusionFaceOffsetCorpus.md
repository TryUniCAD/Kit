# Fusion planar face offset corpus

A deterministic research CLI now resolves signed planar face offsets from native Fusion feature references and face-selection recipes. It measures retained journal geometry and compares it with independent Fusion API observations.

Run `PYTHONPATH=src:Cli uv run python re/Fusion/Reconstruction/FaceOffsets/DecodeOffsets.py re/Fusion/Reconstruction/FaceOffsets/Controls --output /tmp/FaceOffsets.json`. The CLI requires native comparisons when OffsetCorpus.json is beside the archives or NativeObservations.json is in their parent directory, as in the committed corpus.

CaptureControls.py runs only through the private native oracle. It authors six modified controls and two healthy brackets, saves their archives, halves and restores the offset parameter, and records geometry and parameter readback. Two cases are held out from derivation. Source recipes and signed parameters predict volume, area, bounds and centroid in all six cases. Parsed journal measurements also match native topology counts. These are actual source CLI and native API observations; no local tests ran.

Strict neutral projection, curved or multiple-face offsets, native writing and lossless conversion acceptance remain unfinished. The source decoder continues to refuse unsupported histories. See the research Findings.md and Correlation.json for field confidence, digests and measurements.
