# Suppressed runtime stderr conceals hosted review failures

[Hosted run 46166204811](https://github.com/TryUniCAD/Kit/actions/runs/46166204811) prepared a small fresh-base fixture and built the pinned container.
The model process then exited with status 1.
Both process streams were discarded, so the job exposed no causal error.
The same account and requested model succeeded in a local tool-free schema smoke.
That result does not establish that the Linux container works.

Capture stderr only in a private temporary file.
Match a fixed list of diagnostic categories and emit only the corresponding trusted category or numeric exit status.
Never publish the raw stream, authentication data or model input as a diagnostic artifact.
Do not change the model, account or sandbox based on an unverified failure hypothesis.
