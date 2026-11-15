# Close an approved clean oracle session

`re/tooling/sw2026/CloseApprovedSession.py` closes one existing session after an explicit user handoff.
Supply a new report path, `--expected-pid` and `--expected-creation-filetime`.
The tool requires the exact process lifetime and pinned 2026 executable.
Every open document must have an existing saved path and a clear modified flag.
A dirty or unsaved document stops the operation before exit.

The tool requests `ExitApp` and confirms process exit through the retained process handle.
It does not dismiss dialogs or force termination.
The report contains document metadata and belongs outside the checkout.
Publish a redacted summary when that metadata contains unrelated user paths.
Ordinary measurement tools continue to refuse existing sessions.

Static syntax and source review are complete.
The native handoff observation remains pending.
This management operation establishes no CAD writer acceptance.
