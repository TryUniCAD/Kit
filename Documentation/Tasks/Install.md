# Install the repository environment

## Purpose

Prepare an isolated Kit checkout for Python integration work.
This procedure uses the repository lockfile.
It does not install a CAD application or run tests.

## Before you start

- Install Git and `uv`.
- Obtain read access to the [Kit repository](https://github.com/TryUniCAD/Kit).
- Select an unused checkout directory.
- Provide network access for the locked dependencies.
- Read [the contribution workflow](../Reference/Overview/Contributing.md) before making changes.

Kit requires Python 3.11 or later in its package metadata.
The example selects Python 3.14 for the documented Fusion and CLI research paths.
The first-use environment excludes development groups and optional development dependencies.
Contributors should install the tooling required by their task separately.
See [dependency selection](https://docs.astral.sh/uv/concepts/projects/sync/) for the `uv` group and extra rules.

## Procedure

1. Clone the repository into an unused directory.

   ```sh
   git clone https://github.com/TryUniCAD/Kit.git Kit
   ```

2. Open the repository directory.

   ```sh
   cd Kit
   ```

3. Fetch and verify the current remote main revision.

   ```sh
   git fetch origin main
   git rev-parse origin/main FETCH_HEAD
   ```

   Expected result: both lines identify the same commit. Stop if fetching fails.

4. Create an isolated worktree for the task.

   ```sh
   git worktree add ../KitIntegration -b feat/integration origin/main
   ```

5. Open the worktree.

   ```sh
   cd ../KitIntegration
   ```

6. Install the locked application environment.

   ```sh
   uv sync --frozen --no-default-groups --python 3.14
   ```

7. Record the source revision.

   ```sh
   git rev-parse HEAD
   ```

8. Check the CLI and start Python.

   ```sh
   uv run --frozen --no-default-groups kit --version
   uv run --frozen --no-default-groups kit formats
   uv run --frozen --no-default-groups python
   ```

Expected result: the CLI prints its version and format catalogue, and Python starts with the checkout packages available.
The recorded revision identifies the installed source.
This result does not establish that tests passed.

Use this interpreter for the Python examples in these guides.
For a saved script, run `uv run --frozen --no-default-groups python path/to/script.py` from this worktree.

## Package identity

The distribution name is `unicad-kit`.
The installed Python packages are `convert` and `interchange`.
Use `from convert import convert` for the public conversion function.
Do not infer an import name from the distribution name.

The separate console-script declaration installs the `kit` executable.
Keep `--no-default-groups` on subsequent repository commands to avoid installing development groups automatically.
For contributor tooling, follow the task's declared group and extra requirements.
Windows native research supervision also requires the locked `dev` extra.
See [research prerequisites](ResearchCommandLine.md).
The `kit` plugin entry-point group continues to expose the SDK function.
Run `uv run --frozen --no-default-groups kit --help` for available commands.
See [the CLI procedure](CommandLine.md) for conversion and developer decoding.

## If the task fails

| Symptom                          | Action                                                         | Stop condition                                  |
| -------------------------------- | -------------------------------------------------------------- | ----------------------------------------------- |
| Repository access fails          | Check the account and repository URL                           | Do not use another repository as a substitute   |
| Worktree path already exists     | Select an unused directory                                     | Do not delete another task's files              |
| Branch name already exists       | Select a distinct task branch                                  | Do not reset the existing branch                |
| Locked dependency cannot install | Record the dependency and platform error                       | Do not silently regenerate the lockfile         |
| Python import cannot be found    | Start Python with `uv run --frozen --no-default-groups python` | Do not install an unrelated package named `kit` |

## Remove the task environment

Keep the source files and outputs until the task owner no longer needs them.
Remove only the environment or worktree that belongs to this task.
Do not remove shared checkouts or CAD source files during cleanup.

## Related information

- [Package metadata](../../pyproject.toml)
- [Getting started](../GettingStarted.md)
- [Select a format](SelectFormat.md)
