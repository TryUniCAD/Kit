# SOLIDWORKS construction process audit

The research process harness installs `BuildAudit` before importing the builders
or creating the shared schema registry. During imports, it records code-file
opens made directly by the Python import loader and import-loader directory
lookups. It also permits the schema registry to enumerate its exact definitions
directory and bytecode-cache directory, and permits adapter discovery to enumerate
the repository's source-code tree. These directory lookups are recorded. Reads
made by module bodies receive no filename-suffix exemption.

`BeginBuild` closes the import phase. Every subsequent file open, directory read
or subprocess launch raises `PermissionError`, including operations on paths
ending in `.py` or `.pyc`. The metadata process uses this guard and closes its
deliberate forbidden-file probe through a context manager if it unexpectedly
succeeds.

This audit measures the construction boundary; it does not prove that imported
code contains no donor constants. Native dataflow records, source review and the
separate replay scan remain necessary. Earlier suffix-permitting process
evidence does not establish the stronger import-phase claim. Remote checks are
pending; no local tests were run.

The process harness declarations now carry the repository's required rationale
comments, following explicit user authorization. This changes no audit or
construction behavior. Static syntax and comment-policy checks were used;
executable verification remains in remote CI.

After the current main branch was integrated, remote path policy found 33 direct
CI gotcha files against the unchanged limit of 32. The two new process-check
findings now live under `Documentation/Gotchas/Ci/ProcessChecks/`; their links
were updated and the gate remains enabled.
