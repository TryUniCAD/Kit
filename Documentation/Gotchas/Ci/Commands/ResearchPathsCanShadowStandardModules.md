# Research directories can shadow standard library modules

The linked-drawing SDK worker and its independent counterpart put the research
tool directory ahead of the standard library. The repository also has a research
`dis.py`. In a fresh isolated process, a standard-library import can therefore
resolve to that research program instead of Python's own `dis` module.

The first complete pre-unseal drawing replay stopped at this import boundary
before any model generation. That result is a tooling failure, not a native CAD
format failure and not held-out evidence.

Keep the checkout's `src` and repository root explicit for the intended SDK.
Append the research tool and serializer directories after the standard-library
search paths. Apply the same order to both the SDK worker and its independent
counterpart. Preserve the failed frozen closure and rerun the disclosed process
cohort on a newly bound source snapshot before opening any sealed input.
