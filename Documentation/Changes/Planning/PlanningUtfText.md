# Planning text uses UTF-8 on every host

The planning builder and claim reader now decode maintained text explicitly as UTF-8.
The check command uses the same encoding when comparing generated views.
Previously, a Windows legacy locale could decode UTF-8 output with its system encoding and report unchanged views as stale.

The existing planning CLI and file formats are unchanged.
A process regression writes a non-ASCII task name, disables Python UTF-8 mode, and verifies generation and comparison.
It also checks the generated UTF-8 task name directly.
All five planning process cases passed on Windows Python 3.14.6 in 24.27 seconds.
The complete maintained generation and immediate `--check` also passed.
Hosted checks and configured review remain pending on the published revision.

See [planning maintenance](../../Planning/README.md), [the encoding gotcha](../../Gotchas/Research/Planning/ExplicitUtfText.md),
and [PR #121 readiness](../Ci/Testing/SolidworksReadinessFixtureMerge.md).
