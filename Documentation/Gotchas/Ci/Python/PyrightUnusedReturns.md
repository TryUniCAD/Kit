# Pyright rejects unused return values

File writes and SQLite statements can be used for their side effects.
Their byte counts and cursors might appear safe to ignore in integration cases.
Kit enables Pyright's `reportUnusedCallResult` rule, which rejects these unassigned results.
The [catalogue queue run](https://github.com/TryUniCAD/Kit/actions/runs/44792579752/job/136485007439) reported six such errors in SOLIDWORKS catalogue cases.

Assign an intentionally unused return value to `_`.
Preserve the operation and its observable assertions.
Pyright runs on both pull requests and merge-group candidates.
The [PR #397 run](https://github.com/TryUniCAD/Kit/actions/runs/46065343140/job/140729181002)
reported four further unused results in complete archive and CLI integration checks.
The repair retains every call, expected exception and destination-preservation assertion.
An expected exception does not exempt its call from this static rule.
