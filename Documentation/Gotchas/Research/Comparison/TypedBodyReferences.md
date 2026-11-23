# Typed body references need graph declarations

## Expectation

Equivalent decoded designs can use different body, face-selection and parameter identifiers.
Their declared dependencies should correspond independently of those identifiers.

## Observed boundary

The graph reference table previously omitted `FeatureStep.OutputBodyIds` and `DistanceCut.TargetBodyIds`.
It also omitted the three typed `FaceOffset` operand identifiers.
The walker recorded unresolved reference semantics, then retained the raw identifiers as exact fields.
Independent reidentification could therefore produce observed differences alongside unresolved evidence.

The common model already defines these fields as typed dependencies.
Fusion's cut projection populates output-body and target-body identifiers.
Their omission was a comparison declaration gap, not evidence of different geometry.

## Current behavior

The graph now declares those fields as references.
Existing ordering and multiplicity rules remain in force.
Actual target changes remain observable.
Unknown references are not globally masked or removed.

Face-offset cases can still contain unresolved topology or selection observations.
Correct reference correspondence does not establish full B-rep comparison or native acceptance.

See the [follow-up change](../../../Changes/Research/Readers/Comparison/BulkComparisonFollowups.md)
and [semantic comparison contract](../../../Reference/Research/SemanticComparison.md).
