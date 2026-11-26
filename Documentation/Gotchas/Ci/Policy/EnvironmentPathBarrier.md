# Environment and argument paths need a modelled barrier

## Expectation

A path read from a user's own environment variable, or passed on the command line to a test-only receiver, can appear too trusted for security analysis to matter.

## Actual behavior

The merge queue runs CodeQL with the `local` threat model, so environment variables and `sys.argv` are taint sources.
On PR #290 at `53b38e18`, the queue reported three blocking `py/path-injection` findings.
One was `KIT_RUN_DEFAULTS` reaching a file open in `Cli/KitCli/RunDefaults/LoadPreset.py`.
The other two were the forwarded `--catalogue` read and `--directory` creation in `tests/CliResearch/Defaults/ArgumentSink.py`.
The queue removed the PR because any unsuppressed result fails the job.
Plain validation such as `expanduser` or `is_absolute` does not clear these findings.
CodeQL reports the `pathlib.Path` built from the tainted value as the file access.
Wrapping that object as `ResolveLexical(Path(Value).expanduser().absolute(), Root)` still failed, because the reported path existed before the barrier.
The model pack in `.github/CodeQL/extensions/KitPython/PythonModels.yml` recognises only the return values of the `convert.Security` boundaries.

## Workaround

Route the path through a modelled boundary that enforces a real root.
`LoadPreset` expands and absolutizes the override as a string with `os.path`, then resolves it with `ResolveLexical` against the user's home directory.
No `pathlib.Path` object exists until the barrier returns one.
The process tests set `HOME` and `USERPROFILE` to their temporary directory.
The receiver resolves both arguments with `ResolveLocal`, because it inherits the test's working directory.
`KitCli` already depends on `convert`, so no equivalent barrier or new model entry was needed.
Do not suppress the query, exclude the paths, or add a model entry for an unconstrained helper.
Run the queue's CodeQL configuration locally, or run a fresh queue candidate, before treating the change as clear.
