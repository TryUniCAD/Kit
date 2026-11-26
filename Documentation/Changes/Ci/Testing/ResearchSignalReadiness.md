# Publish research signal readiness atomically

The research test fixture writes the selected SDK identity to a temporary
sibling before publishing `Ready`. The existing signal and job-control
tests can read the complete identity as soon as the marker appears.

The merge queue exposed the race in the Linux `SIGQUIT` case. The fix
uses the existing integration coverage for signal delivery, exit status
and cleanup. Queue verification for the fix is pending.
[Readiness marker gotcha](../../../Gotchas/Packaging/ResearchSignalReadiness.md)
