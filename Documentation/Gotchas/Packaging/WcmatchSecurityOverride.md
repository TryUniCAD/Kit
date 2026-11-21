# Wcmatch security override

An ordinary `uv lock --upgrade-package wcmatch` retained 8.5.2 in the scanner dependency graph.
The [queue OSV scan](https://github.com/TryUniCAD/Kit/actions/runs/44842304309/job/136653444827)
then rejected the lock for [GHSA-53pm-wgxf-c6qf](https://github.com/advisories/GHSA-53pm-wgxf-c6qf).
The advisory was published to the GitHub database on November 20, 2026, so a later candidate can fail despite unchanged dependency inputs.

Require `wcmatch>=11.2,<12` through the uv overrides and regenerate the lock.
Retain the required bracex upgrade and verify the locked Python floor remains supported.
Keep Semgrep and the security scanners enabled to establish compatibility on the merge-group candidate.
Semgrep 1.185.0 declares `wcmatch~=8.3`; lock consistency alone therefore does not establish path-selection compatibility.
The Semgrep job exercises its actual CLI include and exclude filters against positive and negative files before scanning the repository.
