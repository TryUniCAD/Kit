# Pinned readers require the sealed corpus history

Expected: a full-history checkout contains the corpus manifest's source revision.
Actual: rewritten public history does not contain the sealed original revision, so `FusionReader.py` fails its `rev-parse` provenance check before decoding.
The [initial feature session](https://github.com/TryUniCAD/Kit/actions/runs/44912585750/job/136871348626) demonstrated this failure on source `72207ec5684d89bf98023427ce4f49eac3a5d122`.

Run the source checkout's `re/automation/CaptureHistory.py fetch` before invoking pinned readers.
This is the same hydration boundary used by the existing full-audit planner and reader integration jobs.
