# Semgrep console entry point

Invoking an installed package with `python -m semgrep` appears equivalent to its console command.
Semgrep 1.185.0 instead deprecates that module entry point and exits with status 2 before scanning.
See the [upstream module](https://github.com/semgrep/semgrep/blob/v1.185.0/cli/src/semgrep/__main__.py)
and [review evidence](https://github.com/TryUniCAD/Kit/pull/204#discussion_r4649279326).

Resolve the `semgrep` console command from the locked uv environment and invoke its absolute path without a shell.
Retain the findings exit code and exact selected-file checks in process smoke verification.
