# A verifier import can remove its caller's sibling path

The portable normalization command added its frozen tool directory before importing the source verifier. That verifier removed its own directory from `sys.path` during import. Both files occupied the same directory.

The next sibling import failed before any model conclusion or normalization report. An isolated Python launch and a `runpy` bootstrap both encounter this import side effect.

The corrected command restores the verified tool path after the verifier import. It also requires the tool manifest beside the exact `Tools` directory. Each tool must match its frozen hash. Standard-library paths still take precedence over the research directory.

The correction changes transport initialization only. Keep the failed launch, exact source manifest and later execution result separate.
