<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Written feature recipes for the catalogue runner

`re/automation/FeatureRecipeSpecs.json` gives each in-scope catalogue entry
one written authoring recipe. A recipe states the seed body, the build steps,
the driving parameters, the expected body count and volume, one or more
variations and a driving edit. It extends the paired recipes in
`PairSpecs.json` and refers to them for P01 to P05.

A written recipe is an authoring intent. It is not captured evidence and it
does not make an entry runnable. Only a reviewed route in `FeatureRoutes.py`
with pinned native archives makes an entry runnable.

## Scope

| Catalogue  | In scope                                                                                          | Entries |
| ---------- | ------------------------------------------------------------------------------------------------- | ------: |
| SOLIDWORKS | 33 part modelling families: reference geometry, sketches, solid, surface, pattern and sheet metal |     260 |
| Fusion     | All feature types except the abstract `Feature` and `MeshFeature` base classes                    |      83 |

289 recipes cover these 343 entries. Shared recipes cover a SOLIDWORKS entry and its Fusion counterpart, for
example `fillet-constant` for the constant-radius fillet and `FilletFeature`.
The file's `scope` field lists the families and exclusions. Assembly, drawing,
simulation, routing, interchange and other non-part families have no recipes yet.

## Planner behaviour

- An entry with a written recipe and no reviewed route keeps its `blocked`
  status. Its blocker becomes `pinned_native_evidence_required` and its plan
  carries `recipe_spec`.
- `RunFeatureCatalogue.py` records such entries as `awaiting_capture`. Entries
  with no recipe stay `recipe_unavailable`.
- Mapped entries keep their routes and also carry `recipe_spec`.
- Entries with retained readback evidence keep their decoder-route blocker.

## Commands

Show one recipe with evaluated volumes:

```shell
python re/automation/InferenceGrid/FeatureDispatch.py \
  --feature family:fillet:constant-radius-fillet recipe
```

Validate the file and measure coverage against both catalogues:

```shell
python re/automation/InferenceGrid/FeatureSpecs.py \
  --solidworks-catalogue FeaturePlan.json --fusion-catalogue Catalog.sqlite
```

Exit status 0 means every in-scope entry has a recipe. Exit status 2 lists
in-scope entries without a recipe. Exit status 1 means the file is invalid or
names an entry that the catalogue does not contain.

## Validation rules

The loader rejects the whole file when any rule fails:

- Each catalogue entry belongs to one recipe only.
- A paired recipe names an existing `PairSpecs.json` recipe and nothing else.
- A mapped route and its written entry name the same paired recipe.
- Every seed, step, parameter and edit is present and typed.
- Volume formulas use a bounded interpreter: numbers, `+ - * / **`, `pi`,
  `sqrt`, `sin`, `cos`, `tan` and `radians`. The loader does not execute
  formula text as code.
- A volume that `adds` or `removes` material must be greater or less than its
  seed volume. `keeps` must be equal.

## Verification evidence

- The checker ran against the PR #164 `FeaturePlan.json` and the Fusion
  planner `Catalog.sqlite`. It reported 260 of 260 SOLIDWORKS and 83 of 83
  Fusion in-scope entries written, with no unknown identities.
- `FeatureDispatch.py manifest` on the SOLIDWORKS catalogue reported 253
  entries waiting for capture, 5 mapped, 2 waiting for a readback route and
  325 out-of-scope entries without a recipe. On the Fusion catalogue it
  reported 81 waiting for capture, 2 mapped and the 2 excluded base classes.
- `tests/Research/Inference/Scope/FeatureRecipeSpecTests.py` runs the dispatch,
  batch and checker processes on fixture catalogues.

## Limitations

- The volumes come from analytic geometry. No recipe has been authored in
  SOLIDWORKS or Fusion yet. Expect corrections when captures run.
- Recipes with a null volume state a check instead. Record the measured value.
- Recipe text does not establish support, decoding or writing for any feature.
