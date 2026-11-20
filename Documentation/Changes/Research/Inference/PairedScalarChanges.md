# Comparing scalar records across a controlled edit

Pass a matching edited SOLIDWORKS part with `--control` to `kit run --root . auto --input baseline.SLDPRT --control edit.SLDPRT --directory /tmp/paired-run`. When a generated reader passes replay, it reads the corresponding member of each control. In `Input-scalar-streams.json`, the member's `paired_changes` lists both byte offsets and values when exactly one scalar changes and the ordered record names match. It intersects the matching declaration IDs from both saves. A single shared ID is a candidate for the feature that owns the dimension.

Use related saves of the same model. Matching names and IDs alone cannot establish model identity or prove correspondence if same-named records were reordered. Multiple changes, a different layout or an unreadable control leave ownership unresolved.

A local P05 baseline run supplied two independently saved edits. For the revolution edit, the generated reader found the angle change from 360 to 90 degrees at offsets 16262 and 16710, with only feature 34 shared. For the height edit, it found 12 to 14 mm at offset 8260 in both saves, with only feature 26 shared. The reader reported both changes in native system units.
