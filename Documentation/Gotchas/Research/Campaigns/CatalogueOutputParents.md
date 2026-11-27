# Catalogue output parents must exist

## Expectation

A nested `kit run --directory` path can appear to create missing parents.

## Observation

Three rim-fillet launches failed before submission because their parent directory did not exist.
The runner creates its selected leaf without creating ancestors.
[Preserved attempts](../../../../re/Fusion/RimFilletPack/Failures/AutomaticRuns.json) retain the original exits.

## Workaround

Create the parent first. Keep the selected leaf unused. Preserve the failed launch and retry only unsubmitted work.
