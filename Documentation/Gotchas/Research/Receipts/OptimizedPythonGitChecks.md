# Optimisation removes assert expressions

Python `-O` removes the complete expression inside an `assert` statement.
A subprocess call placed there does not run.
This affected the reverse replay retention helper's clean-checkout and Git-blob checks.

Run Git first and compare its result with an explicit `if` that raises an error.
Keep the check enabled when the process uses optimisation.
The repaired helper passes three fresh-process cases under `-O`: clean retention, tracked-change rejection and wrong-blob rejection.
The private checkout and manifest are restored byte-for-byte after the rejection cases.

[Repair receipt](../../../../re/DecodedReadWrite20261127/RetentionRepair.json) binds the script hash and actual outcomes.
Earlier replay receipts retain their original script hash, available at their historical Git revision.
