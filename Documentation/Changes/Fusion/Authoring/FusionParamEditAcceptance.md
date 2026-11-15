# Parameter edit in a Fusion-saved design

## Problem

Kit could author a design from a `DocumentSpec` and Fusion accepted it, but nothing recorded whether
Kit could change a parameter in a design Fusion had already saved. Authoring and editing are different
paths: an edit has to rewrite the design segment in place and keep every other record intact.

## Change

The edit path is now measured natively.

`BuildParamEdit.py` reads a Fusion-saved F3D, rewrites one parameter record in the design segment, and
writes the result beside an untouched control.
`OpenParam.py` uploads both, opens each in Fusion, and reports every parameter Fusion sees.

The rewrite uses the same record rebuild the parameter tests use: read the bulk spans, replace the
numeric record for the chosen parameter, and re-emit the segment.

## Recorded verification

Source: `re/Fusion/Study/advanced-627f7fe095f4/advanced.f3d`, parameter `d1`.

| Role    | `d1`        | `d2`        | `d3`                 |
| ------- | ----------- | ----------- | -------------------- |
| control | `30.00 mm`  | `35.00 mm`  | `56.309932474 deg`   |
| edited  | `45.00 mm`  | `35.00 mm`  | `56.309932474 deg`   |

Fusion 2706.1.17 opened both and reported the edited value on the edited file, with the other two
parameters unchanged. The run asserts the edited expression and fails if Fusion reports anything else.

An identity rewrite of the same file leaves all 29 zip entries byte-identical, so the edit changes the
parameter record and nothing else.

## Behavior

| Step                        | Result                                        |
| --------------------------- | --------------------------------------------- |
| Kit reads the parameters    | `d1`, `d2`, `d3` with their expressions       |
| Kit rewrites `d1`           | `30.00 mm` to `45.00 mm`                      |
| Fusion opens the control    | `d1` `30.00 mm`                               |
| Fusion opens the edited file | `d1` `45.00 mm`, `d2` and `d3` unchanged     |

## Limits

The source design has no solid bodies, so this run proves the parameter record and not a rebuild of
geometry from the new value. A design with a body would also show the volume change, and the script
checks that when bodies are present.

The edit changes one parameter. A formula that references another parameter is untested.
