# Signed depth qualification

Source revision: `2b7497e9e117781043bdac8a2c50354ecad30d82` plus the separately fingerprinted builder candidate in each receipt.
Task: `A08h-CutsRevolutions20261123`; owner: Codex; delivery: the campaign PR.

The existing `BuildFusion` entry point overwrote signed native depth parameters with positive magnitudes. P04 cuts consequently left stock unchanged; reversed P03 bosses grew on the wrong side. The candidate preserves the original sign only for `depth_mm` and `cut_depth_mm` while updating their magnitude.

Baseline acceptance reproduces the incorrect cut volume and reverse centroid. Candidate acceptance passes six native cases, including before/after positive controls, a cut parameter holdout and a reversed YZ parameter holdout. A separate request adds a reversed XY parameter holdout. The receipts record source hashes, native feature health, dimensions, body count, volume, centroid and export/reopen measurements. Reopening here occurs within each request's owned application session; it is not a fresh-process claim. Native jobs preserve interactive sessions and model advice stays disabled.

Four focused native inputs are retained in `Manifest.json`. The rest of the campaign remains outside the checkout. Holdouts vary parameters of the same generator; they are not independent authoring lineage. Baseline and candidate source fingerprints are distinct and retained.

Both reversed XY inputs are rejected by the base public reader with `Native reverse distance requires a wrapped millimeter literal`. The candidate accepts their measured plain negative millimeter literals, retains the original expression and signed parameter, and produces matching native volume and bounds. Existing wrapped literals remain accepted. Unit, positive-magnitude and numeric-consistency checks remain required; arbitrary formulas are outside this rule.

The reversed YZ case still fails `FusionSketchLinearDim.constraintType`. Both cut cases still fail the semantic entity-class boundary. They qualify source authoring only. Cross-format conversion of the newly decoded XY inputs still refuses `UnqualifiedGeometry`; no full semantic recovery or editable target conversion is established.

Public CLI integration coverage lives in `tests/Convert/Integration/Fusion/SignedDepth` and uses the existing complete-suite planner and merge-queue shards. Production code never reads these fixture archives or measured rows. No writer or donor replay is introduced.

The native API contract for updating expressions is documented in [ModelParameter.expression](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ModelParameter_expression.htm). Its formula support is broader than this evidence-qualified reader boundary.
