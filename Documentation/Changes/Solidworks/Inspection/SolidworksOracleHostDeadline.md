# Bound an oracle transport from the host

The research [host supervisor](../../../../re/tooling/sw2026/RunOracleBatch.py) launches one operator-supplied guest command through `prlctl exec VM --current-user`.
It runs on macOS or Linux and applies host-monotonic no-progress and optional overall deadlines.
It is separate from production conversion and does not establish CAD acceptance.

## Behavior

The supervisor passes an argument array with `shell=False`.
Use a direct absolute guest Python executable and absolute guest script paths.
No command shell string, guest process sweep or VM recovery command is constructed.
The complete host invocation and guest argument arrays remain in the raw report.

The owned `Popen` object is polled directly.
Only its observed return code establishes that the host transport exited.
Guest `Record.json` fields, file absence, stale files and observation errors never establish transport termination or successful native completion.
Standard output and standard error go to separate new host files.
They do not reset the progress deadline.

A background observer hashes progressive `Record.json` files under the new progress root.
New paths or changed file contents reset the host no-progress clock.
Modification time alone does not count as progress.
The report retains signatures, observed stages, source tool hashes, native process identities and host timestamps.
Incomplete JSON remains an observation, not completion.
The polling loop does not wait for a blocked progress-file scan.
Native integer identities, including process creation `FILETIME`, remain Python integers.

On a deadline, the supervisor sends terminate and then, if necessary, kill only through its retained direct host-child object.
Both waits are bounded.
It records whether host exit was actually confirmed, sets `guest_state_unknown=true` and `acceptance=false`, and returns `124` when host cleanup succeeds.
An unconfirmed host transport exit returns `125` and keeps recovery required.
It does not terminate a guest application, reset a VM, kill a process group or retry the command.
Stopping the transport does not establish that the guest job stopped.
The oracle owner must inventory and recover the guest state before another batch.

A normal host exit preserves the transport return code, including an expected source-preflight exit `2`.
It still does not establish CAD acceptance or independently verify guest application cleanup.
An interrupt signal returns `130`, a termination signal returns `143`, and a supervisor failure returns `125`.
Both handled signals pass through the same bounded owned-transport cleanup.
Nonzero transport outcomes require owner inspection before another batch.

## Use

Choose a new absolute host progress root that corresponds to the guest author's new output directory.
The supervisor does not create that directory.
Its default report is the sibling `<progress-root-name>.Host.json`, with sibling stdout and stderr logs.
A supplied `--report` must also be outside the new progress root, and all three host evidence files must be unused.
This preserves the author's output-directory-must-not-exist guard.

Replace the example paths with the actual mapped host/guest paths and installed Python executable:

```sh
python re/tooling/sw2026/RunOracleBatch.py \
  --vm "Windows 11" \
  --progress-root /absolute/host/staging/CurvesPreflight08 \
  --no-progress-seconds 360 \
  --overall-seconds 3600 \
  -- \
  'C:\Python312\python.exe' \
  '\\Mac\Home\staging\AuthorCurves.py' \
  '\\Mac\Home\staging\CurveSpecs.json' \
  '\\Mac\Home\staging\CurvesPreflight08' \
  --checkout-root '\\Mac\Home\Documents\UniCAD\Kit' \
  --generator-revision COMMITTED_TOOL_SHA \
  --case D19Annulus --case D23TangentCapsule
```

The default no-progress limit is 360 seconds; the overall limit is absent unless supplied.
`--poll-seconds` defaults to one second.
`--terminate-seconds` and `--kill-seconds` default to ten seconds each.
`--prlctl` selects the host executable; it defaults to `prlctl` resolved from the host path.
These are supervision limits, not relaxed geometry or acceptance tolerances.

Raw reports include private paths and belong outside repository checkouts.
Redact only in a separately published evidence copy while retaining original hashes and replacement provenance.
Do not resume a timed-out output directory or infer a healthy guest from a terminated host PID.

## Evidence and limits

The [guest-timeout gotcha](../../../Gotchas/Conversion/Solidworks/Tracing/GuestTimeoutsDoNotBoundHostTransport.md) records the stalled control verification that motivated this addition.
Its missing guest timeout result has no established cause.
Direct output files and host timing describe the new implementation; they do not prove that pipes or guest-clock behavior caused the earlier stall.

Verification for this addition is source inspection, AST parsing and formatting only.
No local tests, oracle operation or native acceptance is claimed.
The oracle owner must commit the tool before a new controlled run.
Host process creation and filesystem reporting still depend on a responsive host; this is not guest cancellation or a real-time scheduling guarantee.

The Python documentation defines [child polling and bounded waits](https://docs.python.org/3/library/subprocess.html#popen-objects) and the [monotonic clock](https://docs.python.org/3/library/time.html#time.monotonic).
The [CAD success criteria](../../../Reference/Operations/CadSuccessCriteria.md) remain unchanged: “success under every criterion on this page” or “the end of the available context” are the stopping conditions.
The production SOLIDWORKS adapter remains read-only.
