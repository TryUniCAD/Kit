# Skipped configurations keep their cache stream

The ordinary SOLIDWORKS 2026 part-save loop can leave the existing downstream stream untouched. It skips configurations that need a rebuild while noncurrent and configurations whose models are unopened. An eligible opened model with a missing or stale cache takes a separate removal branch.

Preserve this order when applying the save rule. Construct the stream name from the configuration's storage ID and suffix. Use the remove branch only after the configuration and opened-model checks pass. [Exact-build store evidence](../../../../../../re/solidworks/records/DownstreamStandaloneStore2026.md)
