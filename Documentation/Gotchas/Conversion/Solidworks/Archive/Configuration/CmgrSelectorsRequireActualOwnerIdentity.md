# CMgr selectors require actual owner identity

## Expectation

Equal configuration names or numeric IDs establish that a directory row is the selected configuration, or that CMgr's active configuration is the Config stream's model.

## Actual behavior

The disclosed manager is native ID -1. Its distinct active configuration is ID 0, and the separate Config model is also ID 0. Only the actual configuration object is shared by CMgr's two selectors and its directory row. A copied configuration with the same name, class, fields and local ID is a different owner.

## Workaround

Retain typed object aliases. Validate both selectors against the actual directory object and validate the fresh factory's `PartSystem.ConfigValues` by identity. Keep same-archive stream custody outside matching-name checks. The event component rejects detached selector and directory copies without replacing any node.

[Source trace and process checks](../../../../../../re/solidworks/records/ThroughAllCmgrFeatureEvents2026.md)
