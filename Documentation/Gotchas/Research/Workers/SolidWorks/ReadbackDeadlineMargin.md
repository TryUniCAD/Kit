# The readback worker needs time to record its timeout before stop_at

Expected: when its client deadline expires, a SOLIDWORKS readback worker
records `cancel.json`, the fence and `result.json`, then exits with
`waiting_application`.

Actual: the supervisor sends `CTRL_BREAK_EVENT` at the session's `stop_at`
(`Sessions.py`). The worker's deadline was `stop_at - 1`, which left one second
for three fsynced atomic writes, client close and interpreter exit. On loaded
Windows runners this sometimes ran out. The worker then died with
`0xC000013A`, and the session finished as `retry` with reason
"session stopped: deadline" instead of `waiting_application`. `WindowsRearmTests::CheckRearm`
then saw no rearm park ([run 45195833207](https://github.com/TryUniCAD/Kit/actions/runs/45195833207/job/137766584419)),
or no `application_rearm_failed` after attempt 2
([run 45165853352](https://github.com/TryUniCAD/Kit/actions/runs/45165853352/job/137663519459),
[run 45098329814](https://github.com/TryUniCAD/Kit/actions/runs/45098329814/job/137443411490)).

Workaround: the readback worker now stops dispatch at `stop_at - 3`. Changing
the test's lease or timeout would not help, because they move `stop_at` and
leave the fixed one-second margin unchanged. The Fusion worker and the protocol
fixtures still use `stop_at - 1` and can hit the same race.
