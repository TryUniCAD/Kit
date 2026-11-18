# Fusion planner catalogue collection

## Change

Research planners now have an indexed SQLite catalogue with CSV inspection exports.
The [guide](../../Reference/Research/FusionPlannerCatalog.md) explains collection, verification and SQL queries.
The saved bundle inventories installed Fusion API metadata, a fresh command snapshot and existing native/capture evidence.

The collector never imports the installed vendor API.
The separately invoked capture helper reads public command metadata in Fusion.
It executes no modelling commands and creates no documents.
Vendor software and documentation remain outside the retained bundle.

## Scope and evidence

| Task field     | Value                                                                               |
| -------------- | ----------------------------------------------------------------------------------- |
| ID             | FusionPlannerCatalog                                                                |
| Owner          | Codex, requested by Stephen316                                                      |
| Scope          | Research metadata collector and saved planner inputs                                |
| Dependencies   | Installed API definitions, native reflection snapshots and study evidence           |
| Delivery       | Separate PR from `codex/fusion-planner-catalog` to `main`                           |
| Exit condition | Source-bound SQLite/CSV bundle, independent readback and documented evidence limits |

The captured build is `2706.1.17`.
The command snapshot contains 3,151 registered commands, 38 workspace identities and 88 unavailable getter results.
Document counts were zero before and after capture.
The saved script digest identifies the exact capture source.
The [command metadata gotcha](../../Gotchas/Research/FusionCommandMetadataAvailability.md) explains unavailable optional fields.
The [documentation-mention gotcha](../../Gotchas/Research/FusionApiDocumentationMentions.md) separates textual markers from actual API availability.

The API inventory contains 2,037 classes, 6,696 properties and 2,144 class constants.
The evidence import retains 1,958 native metatypes and 494 initialized exact own schema/version pairs.
Missing lookups, uninitialized schemas and unverified historical captures remain explicit gaps.
All qualification states remain unverified.

Actual collection and independent bundle readback were performed.
The verifier checks file hashes, SQLite integrity, foreign keys, row fingerprints, CSV counts and unknown-schema handling.
Process-boundary integration coverage is registered under `tests/FusionCatalog/` for the shared acceptance suite.
All four focused process integration cases passed locally with pinned pytest `9.1.1`.
They cover fresh generation from independently authored metadata, bundle readback, tamper rejection and destination preservation.
The input definitions raise if executed, which checks that collection uses syntax rather than imports.
Complete merge-group acceptance and format qualification remain unexecuted.

## Limits

The catalogue is input for the [planner proposal](https://github.com/TryUniCAD/Kit/pull/162).
This PR does not implement planner scheduling or change current programme ownership.
Feature combinations, authoring success, decoder coverage, writer support and native acceptance need independent evidence.
The source-bound manifest is the inventory authority for exact counts and hashes.
