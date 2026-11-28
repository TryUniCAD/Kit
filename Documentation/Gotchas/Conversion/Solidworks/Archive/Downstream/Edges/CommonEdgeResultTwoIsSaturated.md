# Common-edge result 2 is saturated

**Expectation:** the initial downstream edge validator's classification 2 means exactly two common edges.

**Actual behavior:** both reviewed native paths map every count above one to 2. The active helper may also clear its output vector after encountering a third match. The validator's multiple-edge branch resolves its role-2/3 face conditions rather than testing an exact count of two.

**Workaround:** for the bounded ordinary prism, prove the one-edge branch: the output contains exactly one actual edge pointer and equals the current edge. Keep multi-match/seam cases outside that construction profile until their complete semantics are measured. Do not infer the original count from the classification.

The [source record](../../../../../../../re/solidworks/records/DownstreamEdgeValidation2026.md) pins the exact branches and source hashes. Earlier exactly-two prose is superseded by this narrower source distinction; predecessor receipts stay historical.
