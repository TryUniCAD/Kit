# Candidate history does not include separate research refs

## Expectation

Fetching the complete merge candidate history appears sufficient to run
a regression that names an exact research revision.

## Actual behavior

The Config-0 finish probe used a pinned full loader from the separate
SOLIDWORKS research branch. Its revision is outside the candidate's
ancestry. A candidate checkout can hold the two source saves and all
accepted codecs while lacking that Git object.
[Review finding](https://github.com/TryUniCAD/Kit/pull/227#discussion_r4656105560)

## Workaround

The queue decodes allocation tags and class descriptors from the tracked
saves at independently traced positions. It checks the resulting complete
slot directory against the separately pinned live-map proof. The original
full traversal remains a research command with explicit source revision
requirements.
[Finish map evidence](../../../re/solidworks/records/ConfigSurfaceFinish2026.md#physical-checkpoints-and-guarded-replay)
