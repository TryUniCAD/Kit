# Research launcher runtime boundary

The installed `kit` entry point now composes the production commands with a separate `KitCli` developer package from `Cli/`.
`kit research --root /trusted/checkout TOOL ...` and `python -m KitCli research ...` retain the selected checkout, tool allowlist, fresh SDK interpreter, and downstream argument guards.
`python -m convert` retains formats, decoding, and conversion; its research command reports a JSON error directing callers to the developer CLI.
The SDK does not import developer packages or process modules.
The normal CLI also leaves process modules unloaded until research is explicitly requested.

On Linux and macOS the launcher forwards interrupt, termination, and hangup signals into its separate child session, waits for cleanup, and preserves exit codes or terminating signals.
Windows retains its existing interrupt wait and child exit-status behavior.
Supervisor execution still requires Linux or macOS.
The trusted research checkout remains arbitrary and explicit; research fixtures in CI additionally require the fixed repository-owned `ResearchCheckout` path.

The wheel includes `KitCli`; package metadata, strict analyzers, compile caches, and security scans include the new source root.
The path policy records only its exact ecosystem-required `Cli/KitCli/__main__.py` identity beside the existing SDK module entry point.
Existing source runtime checks retain their original forbidden imports and two-package layout.
Built-wheel isolated execution now imports the developer entry point and runs formats with external process imports and operations blocked.
Research compatibility cases exercise the installed `kit` executable, the developer module, pinned reader receipts, controller and supervisor state, Windows interruption, and POSIX signal cleanup and fresh SDK identity.

Verification: the failed candidate's security log identified seven environment-dependent fixture path flows and one process replacement warning.
The fixture path now comes from the repository location and validates the environment against that fixed root before filesystem access.
No tests, reproductions, builds, or collection ran locally.
Static checks passed with Black 26.10.1, Ruff 0.17.4, Pyright 1.1.414, mypy 2.4.1 with silent dependency following, Bandit 1.9.4, and Prettier 3.8.3.
Python checks covered the repaired launcher and changed modules; type checks targeted the launcher, and Bandit covered its complete new source root with the unchanged repository rule set.
Remote checks on the repaired head and merge candidate remain required before acceptance.
The first repaired head exposed obsolete API metadata expectations for the console entry point and source distribution, plus implicit string concatenation in a new process fixture.
The API compatibility cases now verify the installed developer entry point, retained SDK plugin, and exact wheel source roots; the fixture uses one literal accepted by strict typing.
