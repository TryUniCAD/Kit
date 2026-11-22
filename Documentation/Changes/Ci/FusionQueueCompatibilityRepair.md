# Fusion merge-queue compatibility repair

The [merge-group acceptance run](https://github.com/TryUniCAD/Kit/actions/runs/45034560056) rejected PR 241's candidate. Its test shards reported 14 failures and CodeQL reported 19 import-cycle findings. Green PR checks had deferred these heavy checks; they did not establish queue acceptance.

Document JSON and mapping IO now invokes the existing late-bound validation registry instead of importing policy modules that depend on the composed document class. The same source-topology and file-write guards remain mandatory and fail closed when unbound. Public signatures, refusal messages and validation order stay unchanged.

Compatibility replays now include DistanceCut and FaceOffset in the exact wire registry. Circular-span CLI coverage distinguishes the unchanged healthy bracket controls from the new inspection-only journal spans; new spans still require exactly the read-only metadata and no captured native payload. The malformed-label archive replay resolves one untagged planar sketch sheet sharing a physical cap station, allowing unrelated sheet bodies while refusing ambiguous matches.

Historical rectangle and circle fingerprints continue to compare the complete previous serialization. The replay first requires the newly added output_body_ids field to be empty on every legacy feature, then removes only that empty field to compare against the original pinned digest. Source archive hashes and all remaining wire fields stay pinned.

The 714-source census records six newly strict signed, symmetric, two-sided or journal-distance controls and eight more specific refusal diagnostics. These are the exact changes observed in the failed remote candidate; source hashes, inventory size, rejection outcomes and portable-completeness status remain unchanged. The older P04 cut-state replay now expects the semantic-class refusal reached by the new bounded-cut dispatcher; it still requires strict read and public export refusal.

No tests were executed locally. Static policy and type checks validate the patch locally; runtime compatibility and CodeQL must pass remotely, and heavy acceptance must pass on a fresh merge-group candidate. This repair does not establish native output loadability, parametric editing or conversion acceptance.
