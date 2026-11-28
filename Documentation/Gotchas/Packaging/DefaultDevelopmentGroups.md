# Repository commands can restore development dependencies

## Expectation

A first-use SDK environment should install only the selected application dependencies.
A later command should keep that selection.

## Actual behavior

The repository has a `dev` dependency group containing security, typing, and analysis tools.
The former installation guide selected every group and extra for first-use integration.
Also, `uv run` includes the default `dev` group unless the invocation excludes default groups.
Excluding development dependencies during `uv sync` alone does not change later command selection.

## Workaround

Use `uv sync --frozen --no-default-groups --python 3.14` for the guide's minimal repository environment.
Keep `--no-default-groups` on subsequent `uv run` commands.
Install contributor groups and extras explicitly when a task requires them.
This does not change the package's Python 3.11 minimum or qualify any CAD route.

## Evidence

- [Repository dependency groups](../../../pyproject.toml)
- [uv dependency selection](https://docs.astral.sh/uv/concepts/projects/sync/)
- [Corrected installation guide](../../Tasks/Install.md)
