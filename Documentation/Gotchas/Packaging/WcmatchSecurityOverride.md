# Semgrep's version range excludes patched wcmatch

An ordinary lock upgrade stays within Semgrep's `wcmatch~=8.3`
requirement. The repository's lock had 8.5.2. The OSV check
requires 11.2 or later for GHSA-53pm-wgxf-c6qf.
[OSV job](https://github.com/TryUniCAD/Kit/actions/runs/44841247170/job/136649880512) · [Advisory](https://github.com/advisories/GHSA-53pm-wgxf-c6qf)

Resolve through the project's uv override and regenerate the
lock. Verify the Semgrep and OSV jobs with the resolved version
on the merge-group candidate.
