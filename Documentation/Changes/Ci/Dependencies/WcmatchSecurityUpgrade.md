# Patched wcmatch for development scans

The development lock resolves Semgrep's `wcmatch` dependency
to the advisory's fixed release, 11.2. The uv override permits
the fixed 11.x releases while Semgrep's published requirement
selects the 8.x series. [Upstream advisory](https://github.com/advisories/GHSA-53pm-wgxf-c6qf)

Use the normal frozen environment for the Semgrep and OSV
merge-group jobs. `uv lock --check` verifies the corrected
resolution. Hosted scanner compatibility and queue acceptance
are recorded on the delivery pull request.
