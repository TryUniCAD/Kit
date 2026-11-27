# SOLIDWORKS feature family and version coverage

[`re/solidworks/CorpusCoverage.md`](../../../re/solidworks/CorpusCoverage.md) gains a
"Feature family x SOLIDWORKS version coverage" section. It joins the 68 curated families in
[`PlannerCatalog/Sources/FeaturePlan.json`](../../../re/solidworks/PlannerCatalog/Sources/FeaturePlan.json)
to the committed `.SLDPRT` corpus and records, for each family, whether the reader has a typed
decode, whether the writer emits it, how many committed sample files contain it, and at which
document-version generations.

The purpose is the reader and writer delivery plan's baseline item 3: each feature and file version
recorded in one coverage table, with reading and writing tracked separately. Reading is the reader's
typed neutral decode, not native acceptance. Writing is Kit emitting the family from format rules;
only the bounded part writer's `extrude` family qualifies, as one Front-plane line loop and one
forward blind boss.

## Behaviour and usage

The section documents its own reproducible method. The committed count is
`git ls-files '*.SLDPRT' | wc -l`. A self-contained Python census opens each part, reads
`swXmlContents/KeyWords` feature `Type` values, maps them to families through an explicit crosswalk,
and reads the container's `_MO_VERSION_<n>` storage (falling back to `swVersion` in
`swXmlContents/Features`). The census script is embedded in the section so the numbers can be
reproduced from the checkout.

## Limitations

- The census matches on `swXmlContents/KeyWords` feature tags. Sketch geometry sub-families (lines,
  conics, slots, splines, relations, dimensions) are read inside a sketch feature and are not
  separately tagged, so they show `0` samples even where a matched sketch exists.
- `read` reflects a typed decode path in the reader, not native reopening, editing, rebuilding or
  held-out acceptance. `write` reflects format-rule emission only and does not establish the vendor
  contract.
- Version keys are container document-version generations (`19000`, `18000`, `14000`), not every
  service-pack build.

## Verification

At commit `1619f00b`, `git ls-files '*.SLDPRT' | wc -l` returned `322`, and the census opened all
**322** files with no failures. The version census was `19000: 264`, `14000: 57`, `18000: 1`. The
recorded headline gaps are that 17 of 68 families have any committed sample, one family is writable,
and the multi-feature families exist almost only at the older 14000 generation.
