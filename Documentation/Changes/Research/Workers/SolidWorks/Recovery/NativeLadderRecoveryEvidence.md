# Retain recovered native ladder evidence

The [research package](../../../../../../re/solidworks/FeatureLadderRecovery/README.md) retains 37 previously missing SOLIDWORKS batches, with 111 native files and strict neutral reports.
Two saved files from the original failed batch remain separate salvage inputs.
The package preserves original source hashes, independently authored API recipes, native measurements, controller outcomes and sanitized report hashes.
It does not change a production reader or writer.

The remaining-batch wall window was 2,491.18 seconds, including recovery and waiting.
The controller retains 34 completed and two failed attempts.
One failed attempt lost native COM; a separate canary later succeeded. Another returned complete native files but lost local supervisor settlement under Python 3.12.
Successful native captures were not resubmitted.

All 111 complete-batch files strictly decoded. Only fifteen front-plane files also match the native centroid.
Forty-eight top-plane and forty-eight right-plane files retain incorrect neutral placement.
Neutral bounding-box volumes match the requested and measured cuboid volumes; explicit neutral volume and area properties remain unavailable.
The [placement finding](../../../../../Gotchas/Conversion/SolidWorks/Readers/TimestampPlaneFallback.md) identifies the next reader work.

Run `python3 re/solidworks/FeatureLadderRecovery/Verify.py --output UNUSED_REPORT.json` with Python 3.14.
The process verified 500 manifest-bound artifacts, all 37 complete cases and their strict reports.
This is evidence consistency, not complete semantic recovery or vendor conversion acceptance.
Both acceptance flags remain false. Production repair and held-out qualification require a separate PR.
