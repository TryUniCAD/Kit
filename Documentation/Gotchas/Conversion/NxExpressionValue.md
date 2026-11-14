# NX expression values do not drive geometry on load

## Expectation

Rewriting an expression value should change the model, because NX shows the new
value in its expression list.

## Observed behavior

NX 2506 reports the rewritten value, but the body keeps its stored shape. A
block built from `p0 = 40`, `p1 = 30`, `p2 = 20` was rewritten to `p0 = 60`.
NX then reports `p0 60.0`, while volume stays `23999.999999999996` and mass stays
`0.18793536`.

The expression record is not the only place a value lives. Driving dimensions
are also cached in the feature record, and section 0 carries a handle table with
the same encoded values.

## Workaround

Treat `nx.expression_values` as a parameter metadata edit, not a regeneration.
To change geometry, the feature record and its dimension handles have to be
rewritten as well.

## Evidence

`block_p0.prt` loads with `unloaded 0`, reports `p0 60.0`, and still measures
volume `23999.999999999996`, area `5200`, mass `0.18793536`. An independent
expression behaves as expected: `empty_expr.prt` rewritten to `kit_len = 25.0`
reports `EXPRESSION kit_len 25.0`.
