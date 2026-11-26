# Fusion rectangle corner roundoff

Independently API-authored rectangles can retain tiny numerical differences between coordinates that share an intended axis. The opposite corner control includes solver roundoff that makes an exact set of X or Y values contain more than two members. Exact set cardinality therefore rejects an otherwise matched native rectangle.

The bounded multi-feature reader checks every coordinate against its extrema within 1e-9 mm and every edge against its intended axis. It preserves the original coordinates in the neutral sketch and validates generated solid boundaries against the native journal within the explicit geometry tolerance. It does not round the source, infer constraints or permit a generally skewed rectangle. Other strict rectangle profiles retain exact qualification.

Evidence is the opposite corner archive and native observations in [the boundary cut corpus](../../../../../../re/Fusion/Reconstruction/BoundaryCuts/Findings.md).

Width subtraction followed by addition can also reconstruct a different maximum: -10 + (10.1 - -10) gives 10.100000000000001 mm. Two original upper edges at 10.1 mm can then appear not to touch. Clip from the original line extrema and canonicalize only qualified contacts to the stock boundary. The native FlushUpper capture records this separate boundary case.
