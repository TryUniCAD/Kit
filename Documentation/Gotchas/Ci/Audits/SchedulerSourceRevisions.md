# Scheduler source revisions

A manual audit can use a newer workflow with an older `audit_sha` source checkout.
New scheduling scripts, modules, and command options might be absent from that source.
Calling them unconditionally prevents collection results from reaching the shard matrix.

Keep historical audits on the existing count-based planner and modulo platform selection.
Fetch new duration hints and enable new sizing options only for merge-group candidates.
Keep collection and execution pinned to `audit_sha`.
The reporting harness can still come from the workflow revision.
See [runtime scheduling](../../../Changes/Ci/QueueRuntimeScheduling.md).
