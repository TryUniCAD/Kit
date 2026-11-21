# Close an approved clean oracle session

`re/tooling/sw2026/CloseApprovedSession.py` closes one existing session after an explicit user handoff.
Supply a new report path, `--expected-pid` and `--expected-creation-filetime`.
The tool requires the exact process lifetime and pinned 2026 executable.
It attaches through `GetActiveObject(Swapp.PROGID)` only, so a missing active
object fails without an activation fallback or a new application instance.
Every open document must have an existing saved path and a clear modified flag.
A dirty or unsaved document stops the operation before exit.

The tool requests `ExitApp` and confirms process exit through the retained process handle.
It does not dismiss dialogs or force termination.
The report contains document metadata and belongs outside the checkout.
Publish a redacted summary when that metadata contains unrelated user paths.
Ordinary measurement tools continue to refuse existing sessions.

The [historical native handoff record](../../../../re/solidworks/measurements/2026/OracleApprovedHandoff.json)
records the exact selected process and zero open documents at the exit request.
The graceful request returned, but the process remained alive after 30 seconds.
The existing lifetime-checked cleanup helper then terminated that exact empty process and confirmed exit.
The handoff tool itself did not force termination.
The original session was already absent when work resumed, so this record does not establish whether its former unsaved drawing was saved.
This management operation establishes no CAD writer acceptance.

The historical record predates the active-object-only attachment repair.
That repair was verified by AST and static source inspection before its next
native observation. The [later selected handoff](../../../../re/solidworks/measurements/2026/OracleExistingSessionInventory.json)
now records zero documents and a confirmed graceful exit for the same exact
process lifetime inspected by the read-only inventory tool. The current
active-object-only handoff required no forced cleanup. Its subsequent bounded
process inventory retained the observed licensing daemons and background services.
No local product tests ran.
The tool issues no license-server command, service command or VM recovery action.
