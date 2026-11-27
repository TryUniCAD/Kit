# Enterprise runtime planning must not depend on batching

Expected: the trusted Enterprise capacity marker enables duration-based Linux shard sizing.
Actual: the older selector also required live merge minimum one and zero batching wait.
With minimum two and ten minutes of wait, it emitted runtime target zero and used count-only sizing.

The [PR #375 candidate plan](https://github.com/TryUniCAD/Kit/actions/runs/46005349452/job/140527003598) used seven Linux shards after Enterprise capacity landed.
The live settings were read from ruleset 25490615 on 27 November 2026.

For resource marker version 5, select Linux runtime capacity independently of queue batching settings.
Keep the older activation guard for earlier markers and native platform expansion.
Do not change the owner's live queue policy to activate a compute-only optimization.
See [the change entry](../../../Changes/Ci/Scheduling/EnterpriseRuntimeActivation.md).
