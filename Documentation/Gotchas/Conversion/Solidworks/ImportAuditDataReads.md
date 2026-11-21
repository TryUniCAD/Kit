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
loader directory lookups, source-code discovery and the exact schema/cache
directory enumeration. After
initialization, close that phase and deny all file/directory access and process
launches. Continue source and donor audits: permission to import code does not
classify its constants. The shared `ConstructionGuard.py` harness follows this
boundary. Remote verification is pending.

The complete file process initially failed with `adapter package is empty`
because adapter discovery caught a denied source-directory enumeration and
returned an empty package. Do not move the audit after imports to hide this.
Permit and record source-code directory discovery in the import phase while
continuing to deny data-file opens. Close every directory exception when
construction begins.
