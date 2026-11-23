# The job-object stub omits its returned handle

## Expectation

`win32job.CreateJobObject` returns an owned handle that callers can query, use, and close.

## Actual behavior

The pinned `types-pywin32` declaration reports a `None` return value.
This made a Windows-target Mypy check reject otherwise valid handle operations.
The [pywin32 implementation](https://github.com/mhammond/pywin32/blob/main/win32/src/win32job.i) declares the result as `PyHANDLE`.

## Workaround

The isolated console test fixture resolves this documented entry point with `getattr`, matching existing Windows research boundaries.
It retains the returned wrapper until cleanup and converts it to an integer only for APIs and typed ownership transfer.
The owner always terminates the private job and closes its handle.
No type-ignore comment or policy exclusion is required.
