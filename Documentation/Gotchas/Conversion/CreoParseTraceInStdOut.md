# Creo writes a parse path to `std.out` when it rejects a part

## Expectation

A refused part leaves the trail file's `Start`/`End` lines and the file is simply not retrieved. There is no
statement of where the reader stopped, so a bad record has to be found by bisection and repeated launches.

## Actual behaviour

Creo keeps a second log next to the executable, `std.out`, and it holds the last part of the model it was reading
when it died:

```text
Running Pro/Engineer in no_graphics mode.  No windows will be displayed
0::  ~ Command `ProCmdModelOpen`
0::  ~ Activate `file_open` `Inputname` `\\Mac\Home\Documents\creo-authored\trace1.prt`
ThreadOnhandledException called, exit with cleanup
mode rb file: C:\Mac\Home\Documents\creo-authored\trace1.prt
Sld_FeatDefs
 feat_defs_949
  sub_feat_arr
   (subft_indexnumber)
```

The indented names are the section's record path, one level per nested record, with the innermost line naming the
last record read. For `trace1.prt` — a generated `AllFeatur` with a generated class-`949` element — the path stops
at `Sld_FeatDefs → feat_defs_949 → sub_feat_arr → (subft_indexnumber)`, which locates the failure inside the
element rather than leaving "refused" as the whole answer.

Note what this does **not** mean: the bytes at that record match the vendor's field for field. `ThreadOnhandledException`
is an unhandled exception, so the last parsed record is the last thing touched, not necessarily the offending
record. Reading it as "this field is malformed" is the trap; it is a location hint, not a diagnosis.

## Workaround

Clear `std.out` before each launch (`Remove-Item std.out`) so the tail belongs to that run, then read the last
indented path after the `mode rb file:` line. Use it to narrow a candidate, and confirm any conclusion with a
launch that changes only that record.

`std.out` also records the retrieval attempt itself, which is the only place the *path* Creo failed on appears.

## Evidence

- `re/creo/tools/SketchDef.py` — the generated element behind `trace1.prt`.
- `re/creo/data-model/DataModel.md` — the element's declaration diff.
