# Angled datum borders depend on the finite hinge

## Expectation

The measured angled datum's display borders appeared to come from the constrained plane's normal adjustment or angular-dimension update.

## Actual behavior

The border dispatcher is a separate slot on the same concrete datum class. In the observed straight through-origin case it uses the finite selected hinge endpoints. The native check expands a zero transverse span from the nonzero longitudinal span. The expansion step then adds 5% of each resulting span at each edge. Distinct native hinge lengths produce distinct margins with unchanged angle and constraint roles. [Build-bound dispatcher and exact disclosed comparison](../../../../../../re/solidworks/records/LocalLinearPatternDatumBorders2026.md)

## Workaround

Resolve the actual hinge, including its finite endpoints, before calculating the display rectangle in this branch. Keep the source of the hinge endpoints and its update timing explicit when constructing a new model.
