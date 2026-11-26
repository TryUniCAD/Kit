# Pyright rejects unused return values

File writes and SQLite statements can be used for their side effects.
Their byte counts and cursors might appear safe to ignore in integration cases.
Kit enables Pyright's `reportUnusedCallResult` rule, which rejects these unassigned results.
The [catalogue queue run](https://github.com/TryUniCAD/Kit/actions/runs/44792579752/job/136485007439) reported six such errors in SOLIDWORKS catalogue cases.

Assign an intentionally unused return value to `_`.
Preserve the operation and its observable assertions.
PR checks defer Pyright to merge-group validation, so passing PR checks do not establish type-check acceptance.
