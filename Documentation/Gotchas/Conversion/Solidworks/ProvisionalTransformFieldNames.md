# The first provisional transform schema wins

## Expectation

The later resolved-body schema replaces the document-definition schema's
provisional transform field names.

## Observed behavior

The registry loads schema modules in sorted order.
`Registry.provisional` returns immediately when a name already exists, so the
definition module's `mgXform_c.restore` remains active.
Its fields are `has_matrix`, matrix `f08`, translation `f58/f60/f68`, scale
`f70` and flags `f78`.
Using the later module's `matrix/t0/t1/t2/scale/flags` names caused the
[remote component check](https://github.com/TryUniCAD/Kit/actions/runs/43674690691)
to reject a newly constructed definition stream with missing field `f58`.

## Workaround

Construct graph fields for the actual registered schema.
Preserve a single shared transform vocabulary when consolidating the schemas;
wire-equivalent provisional declarations do not establish matching field names.
