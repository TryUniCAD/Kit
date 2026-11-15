# Import-time data reads can escape a construction audit

## Expectation

An empty runtime-read list proves that fresh construction consumed no source
file or data fixture.

## Actual behavior

A guard installed after imports misses data consumed by a module body or by
registry initialization. A guard that accepts every `.py`, `.pyc`, `.so` or
`.dylib` path also accepts data files with those suffixes. Such an audit cannot
support an unqualified zero-read claim.

## Workaround

Install the process audit before importing builders. Permit and record code
opens only when Python's import loader directly requests them, together with
loader directory lookups and the exact schema directory enumeration. After
initialization, close that phase and deny all file/directory access and process
launches. Continue source and donor audits: permission to import code does not
classify its constants. The shared `ConstructionGuard.py` harness follows this
boundary. Remote verification is pending.
