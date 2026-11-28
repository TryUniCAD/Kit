# Black multi-file invocation on the local host

## Expectation

The pinned formatter should finish when several changed Python paths are supplied together.

## Actual behavior

During PR #273's Windows static checks, Black `26.10.1` did not finish several multi-file invocations, including one with `--workers 1`.
The task-owned formatter processes were stopped.
The cause was not established; this observation does not establish a source formatting defect.

## Workaround

Invoke the same pinned formatter separately for each changed file, then run its check mode separately for each file.
These invocations completed successfully for the comparison process fixtures.
Do not omit formatting or treat a hung invocation as a pass.
This workaround concerns local static checks and does not replace the remote Black gate or process tests.
