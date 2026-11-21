# Wcmatch star matching security repair

The development lock now selects `wcmatch 11.2` and `bracex 3.2.2`.
The uv override requires `wcmatch>=11.2,<12` because an ordinary targeted upgrade retained 8.5.2.
Use the checked-in lock when synchronizing scanner dependencies.

[GHSA-53pm-wgxf-c6qf](https://github.com/advisories/GHSA-53pm-wgxf-c6qf)
affects versions through 11.1 and identifies 11.2 as patched.
The [11.2 release](https://github.com/facelessuser/wcmatch/releases/tag/11.2)
repairs multi-star filename matching and requires bracex 3.2 or later.
The [queue scan](https://github.com/TryUniCAD/Kit/actions/runs/44842304309/job/136653444827)
found the advisory in the previous lock.

Verification: uv 0.12.5 resolved 204 packages and `uv lock --check` passed.
Only the two package versions and the override changed in the lock.
No local tests ran.
Semgrep compatibility and security acceptance require the next merge-group candidate; the override alone does not establish them.
No scanner finding was suppressed and all existing gates remain enabled.

The Semgrep queue job first runs `uv run python -m tools.Security.SemgrepPaths`.
This process smoke check gives the installed scanner four real Python inputs and a local rule.
It requires the include glob to select the intended directory and filename, the exclude glob to remove a matching control, and exactly the retained file to produce a finding.
The ordinary repository scan remains a separate required step in the same allowlisted job.
