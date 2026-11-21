# Semgrep console entry point

Invoking an installed package with `python -m semgrep` appears equivalent to its console command.
Semgrep 1.185.0 instead deprecates that module entry point and exits with status 2 before scanning.
See the [upstream module](https://github.com/semgrep/semgrep/blob/v1.185.0/cli/src/semgrep/__main__.py)
and [review evidence](https://github.com/TryUniCAD/Kit/pull/204#discussion_r4649279326).

Resolve the `semgrep` console command from the locked uv environment and invoke its absolute path without a shell.
Retain the findings exit code and exact selected-file checks in process smoke verification.

The Python scan parser still declares `--no-semgrepignore-v2` but explicitly aborts when it is supplied.
Use the console launcher's supported `--legacy` switch to select Python rule filtering instead.
See the [launcher dispatch](https://github.com/semgrep/semgrep/blob/v1.185.0/cli/src/semgrep/console_scripts/entrypoint.py)
and [parser refusal](https://github.com/semgrep/semgrep/blob/v1.185.0/cli/src/semgrep/commands/scan.py).
