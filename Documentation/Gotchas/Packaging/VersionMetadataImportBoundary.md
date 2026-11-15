# Version lookup imports dependencies during parser construction

Using `version=importlib.metadata.version(...)` in the parser factory reads distribution metadata for every command.
On the queue's Python interpreter, that lookup imports email utilities and then `urllib.parse`, which the isolated runtime blocks.
The result was a wheel formats command failing before argument parsing completed.

Defer metadata imports and lookup to a top-level version request.
Keep argparse responsible for output, placement validation, and exit status, using its [documented version action](https://docs.python.org/3.11/library/argparse.html#action).
Stop version discovery at commands, help, and the option terminator so forwarded arguments and filename operands do not trigger it.
Keep the runtime import guard unchanged.

See [the queue correction](../../Changes/Commands/QueueRuntimeCompatibility.md) and [the failed wheel process](https://github.com/TryUniCAD/Kit/actions/runs/43719461782/job/132828247820).
