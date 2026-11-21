# Queue reader runtime repairs

Shared native name, class, feature, constraint, and rule-context records now live in independent modules.
Count readers import those records directly, which removes their decoder import cycles.
The queue CodeQL suites remain enabled without new suppressions.

Edited-depth reconciliation now computes `source_sha256` from its input bytes.
Generated readers and file-driven graph receipts therefore include the same input identity.
The existing integration case continues to compare the complete output.

The archived P04 report retains its original vocabulary boundary and exact report digest.
It also requires the current reader to register `BrepRef`.
Fusion census failures now include the comparison output so changed outcomes can be reviewed before any baseline update.

Verification: steering passed for 5,055 files, Linux Mypy passed for 5,022 files, and Pyright reported zero errors for 5,020 files.
Queue candidate `8723a937571bd7e4e4780b2e7adf0cf2d5a3eb52` passed CodeQL, Linux and Windows research CLI compatibility, and four of six test shards.
The remaining two shards exposed stale Fusion diagnostic expectations, addressed in [Queue Fusion diagnostic repairs](QueueFusionDiagnosticRepairs.md).
No local tests ran.
