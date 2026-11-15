# Creo neutral dimension parameters

## Change

Adds `src/convert/adapters/creo/Stream.py` and extends the Creo reader to decode definition-site
dimension values from `FeatDefs` into neutral `Parameter` records linked to the owning
`FeatureStep.parameter_ids`.

## Behaviour

`StreamParser` decodes the PSB tagged stream: named records (`e0 <type> <name> 00`), compact
integers, doubles, strings, `f8`/`f9` arrays, `e4`-`e7` repeats, `e1` null, `e2`/`e3` compounds, and
`f1`-`f4` closes. Each `e0` byte offset maps to its scanned field so replayed definitions cannot
shift the index.

`ReadDimensions` returns every definition-site `value` node whose payload is a finite double, with
the following `dim_ref` identifier when present.

The reader then emits one `Parameter` per dimension:

```text
id          creo:dimension:<n>
name        Creo dimension <n>
value       ParameterValue(double, ValueKind.KNumber, <unit token>)
role        ParameterRole.KDriving
owner_id    the single protrusion feature id, when exactly one exists
provenance  ProvenanceSpan("FeatDefs", offset, 8, "dimension_value")
attributes  creo.dimension_reference, creo.dimension_index
```

When exactly one feature has root class `917` (`protrusion`), all decoded dimension ids are added
to that feature's `parameter_ids`.

Metadata reports `creo.dimension_count` and `creo.parameters_decoded`.

## Limits

- Both definition-site and positional replayed dimension rows decode. The ladder control stores
  two copies of the sketch rectangle, so eight parameters with four distinct values are emitted.
- Values are emitted with `ValueKind.KNumber`; length versus angle is not yet classified.
- `creo.feature_history_decoded` and `creo.geometry_decoded` remain false.
- The writer is unchanged and still performs exact source replay only.

## Verification

Read through the production adapter on the retained ladder control:

```text
ladder features [('creo:feature:7', ...), ('creo:feature:3', ...), ('creo:feature:11', ...),
                 ('creo:feature:67', ...), ('creo:feature:75', ...),
                 ('creo:feature:74', 'Creo protrusion 74',
                  ('creo:dimension:0', 'creo:dimension:1'))]
ladder params   8 values: -201.719085, -338.938151, -86.06681, -154.43033 (twice)
ladder meta     creo.feature_row_count=6 creo.dimension_count=8
                creo.parameters_decoded=True creo.feature_history_decoded=False
                creo.geometry_decoded=False
                feature 74 parameter_ids has 8 entries
```

`TestFeatureRows` also asserts the synthetic path: two features, one `FeatDefs` dimension, a
`creo:dimension:0` parameter with value `-201.7190851617055`, owner `creo:feature:5`, and
`parameter_ids == ("creo:dimension:0",)`.

## Documentation

- [Creo adapter](../../Reference/Adapters/Creo.md)
- [Feature record change entry](CreoNeutralFeatureRecords.md)
- [Compound-boundary gotcha](../../Gotchas/Conversion/CreoTaggedCompoundBoundary.md)
