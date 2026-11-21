# Construct a typed part chronology

## Purpose

Use these internal APIs to construct a Header component from explicit semantic intentions. They do not provide complete source conversion.

## Before you start

Use the qualified version-19000 part graph and its actual persistent allocator. Keep each feature's real `owner` pointer bound to that part.

Read the [field and evidence record](../../../../../re/solidworks/records/PartChronologyConstruction2026.md). Keep unsupported original state outside this constructor.

## Procedure

1. Create `RevisionEvent` values with operation, user, company, wall seconds and comment.
2. Create `RevisionLog` values with actual owner nodes, explicit captions and ordered events.
3. Create `RevisionBook` with explicit ordered attribution tables and those logs.
4. Create `HeaderClocks` with separate creation, archive and update times.
5. Call `MakeIntentHead` for each actual Header role.
6. Compose the real self file with the existing `MakeSelfFile` operation.
7. Share that one self object between the generated Header roles.
8. Supply the manager save and version-history event through their existing separate constructors.
9. Serialize through the shared Header, Config, Resolved and History codecs.

The attribution tables must contain unique names. Event references use those semantic names. The constructor computes their numeric indices.

`FeatureInstant` and `MakeFeatTime` encode an explicit precise feature moment. They do not perform a native rebuild or revision operation. Keep zero stored FILETIME separate from Unix epoch zero.

The caller must derive every dependent feature reference from its emitted first log event. Adding profile logs without updating those references is outside the qualified complete composer.

## Expected result

The two Header roles have independent stamp graphs and one shared self identity. Clock values retain their declared owners. Counts, IDs and indices follow the actual constructed graph.

The measured coupled profile preserves four previous native-qualified artifact hashes. The split-clock host profile changes only its four declared metadata streams. New native acceptance remains pending.

## Replay

Use the exact frozen source, tool and input manifests supplied with the private handoff. Choose an unused output directory.

```sh
/absolute/path/to/Kit/.venv/bin/python -B /absolute/path/to/SdkPartChronology01/RunCombinedChronology02.py \
  --root /absolute/path/to/SdkPartChronology01 \
  --output /absolute/path/to/unused/ChronologyReplay
```

The independent combined replay passes thirty chronology workers and two
lower self-owner workers. It produces passing `Chronology/Replay.json`,
`Identity/Replay.json` and `Combined.json`. The first private wrapper
failed to import its sibling in isolated Python. The corrected wrapper
sets up that research import explicitly.

## If the task fails

Preserve the failed report and exact source/tool hashes. Fix observer prerequisites in a new frozen packet. Keep source clocks, native flags and geometry decisions unchanged.

The ordinary preparer still refuses a destination stem that differs from the model name. The lower self-owner experiment records that refusal. It does not authorize broader public writing.

## Related information

- [Process receipt](../../../../../re/solidworks/measurements/2026/PartChronologyConstruction01.json)
- [Header clocks](../../../../../re/solidworks/records/DrawingSourceEpochOwnership2026.md)
- [Native split epochs](../../../../../re/solidworks/records/DrawingSourceEpochNativeLifecycle2026.md)
- [Reference creation times](../../../../Gotchas/Conversion/Solidworks/FeatureReferenceCreationTimes.md)
- [Actual self name](../../../../Gotchas/Conversion/Solidworks/Archive/ExternalReferences/ExternalSelfReferenceUsesModelName.md)
