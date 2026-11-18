# Constrained line entities retain nonzero reference counts

A closed rectangle with four owned points and four lines can also own two driving
point distances and four unary axis relations. A reader that treats every point
or line `f20` as zero rejects this valid typed geometry. Clearing the dimensions
to regain the line path would lose the actual driving graph.

`f20` counts concrete constraint-handle occurrences. Count each `sgPointHandle`
target in the value group and each `sgLineHandle` target in the unary relation
group, then require each decoded entity to match its own derived count. Do not
replace that check with permission for arbitrary positive values.

Each display also retains a `moSkDimHandleValG2_c`: its `ff0` must be the actual
same sketch object and `ff8` the actual value-group index. Matching class names,
parameter values, rectangle dimensions or source strings do not establish that
ownership. Preserve both selected point references in each public distance.

The [native construction rule](../../../../../../re/solidworks/records/RectangleDimensions2026.md)
and [SDK read ledger](../../../../../../re/solidworks/records/SdkRectangleTypedRead2026.md)
record the independent field and measurement evidence. Existing unconstrained
line loops retain zero reference counts and their previous public behavior.
