# Construction-axis point providers can fail the research prefix guard

## Expectation

Identical TwoPoints axis inputs should retain the same decoded support ownership when only revolution angles change.

## Observed behavior

The unequal-axis campaign recovers angle roles and the selected construction axis on all 46 archives.
Eight archives from the second-angle and swapped-angle cases fail support-provider qualification.
The diagnostic is `Unsupported construction-mode point provider`.

The inspected provider records retain their 178-byte length, method code 10 and axis-owner trailer.
Their first 23 bytes differ from the all-zero prefix required by the research helper.
Other captures with identical axis inputs satisfy that guard.
This observation does not establish the meaning of the nonzero bytes or a causal relationship with angle changes.

## Workaround

Retain the refusal and compare explicit selected-axis geometry separately from full support qualification.
Do not remove the prefix check or treat cached geometry as proof of complete support semantics.
A future rule needs independent controls, held-out counterexamples and coordinated decoder ownership.

See the [campaign evidence](../../../../re/Fusion/UnequalAxis20261127/README.md).
