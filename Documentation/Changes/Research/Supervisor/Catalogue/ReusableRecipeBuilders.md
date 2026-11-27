<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Reusable catalogue recipe builders

The catalogue authoring prototype adds nine explicit SOLIDWORKS bindings through
shared profile, seed, extrusion, and revolution builders. Written recipes alone
do not authorize execution. Unknown recipes and unsupported controls fail before
native entry. Existing P01–P05 defaults remain unchanged.

| Capture mode | New recipe identities                                                                                |
| ------------ | ---------------------------------------------------------------------------------------------------- |
| `discovery`  | `extrude-two-direction`, `extrude-midplane`, `extrude-offset-start`, `extrude-thin`, `extrude-up-to` |
| `holdout`    | `revolve-two-direction`, `revolve-midplane`, `revolve-thin`, `revolve-cut`                           |

## Usage

Use a trusted checkout and a SOLIDWORKS catalogue containing the selected entries.
Choose an unused output directory outside the checkout.

```shell
python re/automation/InferenceGrid/RunFeatureCatalogue.py --solidworks-catalogue FeaturePlan.json --directory C:/Research/RecipePlan --author-samples --authoring-grid three-values --prepare-only
```

`--authoring-cases` selects entries and parameter overrides. The optional
`--authoring-grid three-values` adds two legal values for each exposed parameter,
changing one parameter at a time. Without this option, authoring uses the baseline
cases. Parameterless recipes retain one baseline. Resume uses the saved grid.

Remove `--prepare-only` and supply the native host settings described in
[catalogue sample authoring](CatalogueSampleAuthoring.md) to execute authoring.
Native SOLIDWORKS execution requires a Windows desktop context outside AppContainer.
New recipe batches contain at most three cases. Each case retains its own native
bundle and dependent decoder job. Native output and phase reports persist under
the run's `NativeAttempts/<session>/Capture` directory after session cleanup.

## Limits and evidence

Closed-contour thin extrusion, up-to-next, and up-to-vertex variants remain
unsupported. The new bindings target SOLIDWORKS. Native Fusion acceptance remains
unverified.

Process checks cover compilation, parameter guards, source pins, batch preparation,
immutable artifact publication, and decoder transport. These checks do not establish
native acceptance or decoded feature semantics. Native verification, unresolved
decoding, and qualified conversion remain separate results. Neutral artifacts
require portable qualification.

The local prototype has 103 passing process cases across focused runs. At `6ca573b5`,
the offset-start baseline had the expected geometry; SOLIDWORKS did not exit
after `ExitApp`, requiring cleanup of the owned process. The fresh second phase
and downstream decoder did not run. A batch-only finalizer drain did not resolve
shutdown. A post-owner finalizer drain at `7a868f5e` then passed the full bounded
offset-start native run and automatically completed the decoder job, which still
reported unresolved semantics. One new binding is native verified; the other
eight remain unverified. The
[written recipe campaign](WrittenRecipeCampaign.md) now drives recipe application
with an assisting agent rather than treating these nine bindings as the full scope.

A08i is owned by Codex on `codex/reusable-feature-builders` and depends on
[PR #207](https://github.com/TryUniCAD/Kit/pull/207). Delivery and acceptance are
maintained in the
[automation step register](../../../../Reference/Research/AutomationSteps.md).
