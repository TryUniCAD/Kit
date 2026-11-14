# Triangle source depth recovery

## Expectation

The decoded native operation's `length_mm` preserves the full source depth and a baseline stream's dynamic-field positions apply to every authored triangle.

## Actual behavior

`length_mm` is derived from native dimension display text and can contain only two decimal places. In one seeded example, the text yielded 18.0 while the authored value was 17.995855. The 10,603-byte variants also shift the four positive depth fields by two bytes relative to the 10,601-byte baseline, so reading at 9408 can produce an unrelated value.

The corrected bounded corpus uses a shifted offset of `baseline_offset + len(stream) - 10601` for 9408, 9480, 9968, and 9992, then requires all four millimetre values to agree after six-decimal source normalization. These are source-research witnesses, not permission for the production writer to copy a recorded stream.

## Workaround

Recover source research parameters from consistent native depth copies rather than dimension display text. Refuse conflicting, missing, or nonpositive values. Preserve rejected output attempts separately from fresh public writes, and do not overwrite existing files because the writer intentionally refuses replacement.

Regression and acceptance still use independently computed analytic geometry and SOLIDWORKS rebuild results. Four matching witnesses identify a source parameter; they do not independently establish vendor acceptance of a newly generated file.

See [the corpus builder](../../../../re/tooling/harness/BuildRandomTriangles.py) and [the triangle change record](../../Changes/Solidworks/SolidworksThreeLineNativeHistories.md).
