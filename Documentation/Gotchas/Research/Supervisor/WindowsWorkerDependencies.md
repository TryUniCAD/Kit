# Windows catalogue workers need installed dependencies

## Expectation

An installed CLI can import dependencies from a second environment added to `PYTHONPATH`.
The catalogue supervisor and its workers can appear to inherit that import setup.

## Actual behavior

Python does not process a site's `.pth` files when that site enters its search path only through `PYTHONPATH`.
On Windows, the supervisor stopped at `import pywintypes` even though the other site contained the package.
Adding the Win32 paths let the supervisor start. Its inference workers still could not import NumPy.
The [worker launch](../../../../re/automation/Sessions.py) passes a restricted environment without `PYTHONPATH`.
Both failures occurred in the RequestedCorner and P04 compatibility runs on Python 3.14.6.

## Workaround

Install the candidate wheel, the locked `pywin32` release, and the locked NumPy release in one disposable environment.
Run the catalogue CLI with that environment's interpreter.
Check both imports with `PYTHONPATH` unset before starting the verification.
Keep the worker environment restriction.

With the required packages installed, both CLI cases passed at `d3b2cb982c` in 84.79 seconds.
See the [runner module import gotcha](../Workers/WorkerRunnerModuleImports.md) for checkout-owned modules.
