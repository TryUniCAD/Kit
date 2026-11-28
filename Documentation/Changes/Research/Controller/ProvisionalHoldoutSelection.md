# Provisional holdout selection

A07 inference reports include `assessment.provisional_holdout_selection` when
one candidate matched all samples and holdout evidence contradicted every
competing candidate. The value identifies a member of `assessment.hypotheses`.
The report retains the frozen discovery digest, candidate identities and
counterexamples. A tie leaves the field absent.

The assessment retains its `ambiguous` status. Selection used the withheld
samples, so qualification still needs an independent replay of the selected
rule through the existing qualification gate.

The worker process regression runs the same synthetic discovery inputs against
three holdouts. One selects the first offset, one selects the second, and one
leaves both offsets viable. The process assertions compare discovery digests,
candidate identities, selection and counterexamples across all three results.

See [deterministic inference](DeterministicInference.md) for runner setup.
