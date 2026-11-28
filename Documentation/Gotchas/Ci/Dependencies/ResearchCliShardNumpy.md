# Research CLI shards had numpy only by co-scheduling

The retired `Research CLI compatibility` job added numpy with `uv run --with 'numpy<2.5'`, because file-driven research runs import it.
That seemed to be a pin the complete test suite lacked.

The queue shards sync with `--no-default-groups --extra dev`, which [does not provide numpy](OptionalDevIsNotDependencyGroup.md).
Before the job was retired, the extra `--group dev` sync ran only for shards that selected `tests/Research/Inference/` cases.
Research CLI cases still passed because every shard in the observed plans also held inference cases (merge-group run 45722431861: all seven shards).
A smaller plan or a reuse-heavy candidate could schedule research CLI cases without inference cases and lose numpy.

The shard dependency sync now runs when a shard selects either `tests/Research/Inference/` or `tests/CliResearch/` cases.
It uses the locked `dev` group, whose `numpy<2.5` constraint resolves to the version in `uv.lock`.
Select a dependency from the cases a shard actually holds, never from what other cases happen to share that shard.
See the [retirement entry](../../../Changes/Ci/ResearchCliRetirement.md).
