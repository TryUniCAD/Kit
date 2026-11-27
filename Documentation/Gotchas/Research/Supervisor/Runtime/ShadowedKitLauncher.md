# Another Kit launcher can select the wrong interpreter

## Expectation

Installing Kit with Python 3.14 can appear to ensure every later `kit` invocation uses that interpreter.

## Observed behavior

The rectangle-recovery follow-up resolved `kit` to a separate installation with a Python 3.12 entry point.
The supervisor aborted during child settlement because that interpreter did not expose `os.waitid` on this host.
The explicitly installed Python 3.14.6 runtime exposed both `os.waitid` and `os.wait4`.
This launcher failure was separate from the remote SOLIDWORKS COM failures.

## Workaround

Resolve the command before resuming durable jobs. Inspect its entry-point interpreter.
Use the verified Python 3.14 installation's absolute executable path when another installation shadows it.
Do not modify unrelated installations, global search paths, process fences, or accepted job receipts.
Preserve the failed attempt and verify returned native artifacts before deciding whether native work needs another run.
