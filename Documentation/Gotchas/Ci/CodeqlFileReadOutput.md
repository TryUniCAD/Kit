# CodeQL file reads in privileged workflows

A `cat` that writes to `$GITHUB_STEP_SUMMARY` or standard error might appear safe.
CodeQL `actions/output-clobbering/high` flags each statement that starts with `cat`, `head`, `tail`, `jq`, `yq`, or `<` after a checkout in a `pull_request_target` job.
The redirection target does not change the result.
Read and write the file in the trusted Python step, or print a fixed message.
Do not add a suppression.
See [the queue findings](https://github.com/TryUniCAD/Kit/actions/runs/43338996627/job/131602300559) and the [query source](https://github.com/github/codeql/blob/main/actions/ql/lib/codeql/actions/security/OutputClobberingQuery.qll).
