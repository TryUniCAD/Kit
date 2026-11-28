<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Apply written recipes with an assisting agent

The opt-in [automatic builder-development loop](AutomaticBuilderDevelopment.md)
adds bounded generation, independent qualification and runtime registration for one
missing offset-plane builder. The handoff behavior below remains the default.

`RunRecipeCampaign.py` walks every written recipe in the selected feature
catalogues, including recipes that have no executable mapping yet. It reuses
the existing native authoring, verification and decoding runner. It does not
restrict the campaign to the nine newly implemented builders.

```shell
python re/automation/InferenceGrid/RunRecipeCampaign.py --directory C:/Research/RC --solidworks-catalogue FeaturePlan.json --solidworks-host Host.json --native-ready --watch
```

Add `--prepare-only` to inspect the complete queue without launching CAD.
`--authoring-grid three-values` is the default; `baseline` selects the written
default values. Fusion uses `--fusion-catalogue`, `--native-config`,
`--native-kind`, `--native-resource` and `--fusion-lifecycle` from the existing
runner. Native execution retains the existing platform requirements.

The assistant reads `NextRecipe.json`, which contains the exact written recipe,
seed, aliases, source hashes and previous failed attempts. The assistant resolves
the missing mapping or execution failure in the existing executor, commits local
source changes on the working branch, and writes `RecipeReply.json`:

```json
{
  "key": "COPY_FROM_NEXT_RECIPE",
  "recipe_sha256": "COPY_FROM_NEXT_RECIPE",
  "status": "ready",
  "reason": "Describe the implemented correction."
}
```

The running `--watch` loop reloads code in a fresh step process, checks that the
mapping actually exists, and continues. A reply cannot mark native verification
as passed. `skip` requires a concrete reason and remains incomplete. The script
uses this file handoff with its assisting agent; it does not make model API calls.

`Campaign.json` preserves per-recipe progress and attempts. Each attempt has its
own native receipts, logs and decoder result. Interrupted native attempts resume
through the existing runner. `CampaignResult.json` separates pending assistance,
native verification, unresolved decoding and features without a written recipe.
Unmapped features and unresolved decoding never become successful coverage.

The configured SOLIDWORKS catalogue prepared 256 recipe groups covering 260
written feature entries: 14 executable groups and 242 requiring assistance.
Two real CLI process checks cover the full written roster, repeated preparation,
source-bound handoff and rejection of unsupported ready claims. This establishes
the campaign workflow, not complete native coverage of the catalogue.

An actual one-step campaign pilot at `b58cab72` selected mid-plane extrusion,
launched the existing native runner and saved its first file. SOLIDWORKS failed
normal shutdown, so the campaign retained the failed attempt and requested
assistant help. It accepted zero native observations and did not run the
dependent decoder. This verifies dispatch and failure handoff, while native
completion of that recipe remains unresolved. The separate offset-start proof
at `7a868f5e` is retained independently.

Delivery is local at the user's request. No DLLs or native archives are included
in source commits. Step ownership is recorded in the
[automation register](../../../../Reference/Research/AutomationSteps.md).
