# Concurrency queue validation

GitHub supports `queue: max` for preserving multiple pending concurrency-group requests.
The pinned actionlint 1.7.12 release rejects that key.
Replacing it with the default single-pending behavior cancels older audit requests instead of serializing all of them.

Use the pinned upstream concurrency-support revision with the full analyzer enabled.
It validates `single` and `max` and rejects `queue: max` with unconditional in-progress cancellation.
Do not suppress the syntax check or remove concurrency keys from the analyzed workflow.
The [upstream change](https://github.com/rhysd/actionlint/pull/654) and
[GitHub concurrency documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)
describe the compatibility boundary.
