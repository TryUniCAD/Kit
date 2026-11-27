# Argument parser exit control flow

An argument parser error exits the process, but static analyzers can disagree about that control-flow boundary.
CodeQL reported a potentially uninitialized shard count after the runtime-sizing error handler called `ArgumentParser.error`.
Pyright accepted that path as terminating.

Return exit code `2` explicitly from the command boundary after reporting invalid runtime inputs.
This preserves rejection and makes the failure path explicit without suppressing either analyzer.
See [the audit finding](https://github.com/TryUniCAD/Kit/actions/runs/45073400945/job/137365207795).
