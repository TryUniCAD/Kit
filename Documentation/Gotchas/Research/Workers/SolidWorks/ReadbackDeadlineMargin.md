# Application workers need time to record a timeout before stop_at

Expected: when its client deadline expires, an application worker records `cancel.json`, the fence and `result.json`, then exits with `waiting_application`.

Actual: the supervisor sends `CTRL_BREAK_EVENT` at the session's `stop_at` (`Sessions.py`).
Every application worker set its deadline to `stop_at - 1`, which left one second for three fsynced atomic writes, client close and interpreter exit.
On loaded Windows runners the SOLIDWORKS readback worker sometimes ran out of that second.
It died with `0xC000013A`, and the session finished as `retry` with reason "session stopped: deadline" instead of `waiting_application`.
`WindowsRearmTests::CheckRearm` then saw either no rearm park ([run 45195833207](https://github.com/TryUniCAD/Kit/actions/runs/45195833207/job/137766584419)) or no `application_rearm_failed` after attempt 2 ([run 45165853352](https://github.com/TryUniCAD/Kit/actions/runs/45165853352/job/137663519459), [run 45098329814](https://github.com/TryUniCAD/Kit/actions/runs/45098329814/job/137443411490)).

Workaround: `ApplicationProtocol.STOP_MARGIN_SECONDS` (3 s) is now the single margin.
The SOLIDWORKS readback worker, the Fusion application worker, the Fusion continuous fixture and the protocol fixture all subtract it from `stop_at`.
Changing a job's lease or timeout would not help, because they move `stop_at` and leave the fixed margin unchanged.
The 3 s value is three times the budget that was exhausted; it was not measured as a p99.
