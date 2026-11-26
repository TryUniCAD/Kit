# Registered Fusion commands can have unavailable control metadata

## Expectation

A registered command definition appears available for read-only metadata inspection.
That does not guarantee that every control getter succeeds in the current context.

## Observation

The Fusion `2706.1.17` snapshot collected 3,151 command identities on 2026-11-18.
The control-metadata read reported `RuntimeError` for 88 commands.
The capture retained their identities and recorded the unavailable field as `controlDefinition`.
No commands executed and no documents were created.

The report does not identify which native condition caused each failure.
Unavailable control metadata does not establish that a command or feature is absent.

## Workaround and evidence

Collect command identities independently from optional control metadata.
Retain getter failures as explicit gaps instead of inventing visibility or availability values.
Keep the current-context limitation when comparing captures.

The [source-bound snapshot](../../../re/Fusion/PlannerCatalog/Sources/Commands.json)
and [catalogue guide](../../Reference/Research/FusionPlannerCatalog.md) record the evidence and its limits.
