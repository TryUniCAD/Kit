# Bulk comparison references, discovery and missing-input evidence

## Behavior

The bulk comparison follow-up corrects three independently inspected boundaries.
It extends [PR #273](https://github.com/TryUniCAD/Kit/pull/273) without changing either decoder.

The semantic graph treats these typed fields as dependency references:

| Record        | Fields                                               |
| ------------- | ---------------------------------------------------- |
| `FeatureStep` | `OutputBodyIds`                                      |
| `DistanceCut` | `TargetBodyIds`                                      |
| `FaceOffset`  | `TargetBodyId`, `FaceSelectionId`, `DistanceParamId` |

Independent source identifiers can therefore correspond through the graph instead of becoming literal field differences.
Changed targets remain observable through reference roles and endpoints.
Unknown references and unsupported domains remain unresolved.
The correspondence search algorithm and its existing candidate limits are unchanged.

Directory discovery uses streaming directory iteration.
It charges the input root and encountered entries before retaining further work.
The discovery and selected-file limits remain separate.
Linked directories, linked selected files and enumeration errors remain refusals.
The final relative-path pair roster remains sorted.

When a counterpart is absent, the report retains each present side's bounded plain-file fingerprint.
A missing pair does not deserialize the present document.
An invalid present-side file remains an input error.
The report does not invent a fingerprint for an absent file.

## Use and limitations

The existing [bulk command](../../../../Tasks/CompareDecodedDocuments.md) requires no new options.
Use an explicit manifest for independently named exports.
Use the documented selection pattern to exclude sidecars from matching directory layouts.

The owner's existing unresolved-priority and engine report-budget repairs remain intact.
These changes do not establish source custody, native acceptance, or complete feature coverage.
Full B-rep, meshes, retained payloads and assembly graphs retain their existing unresolved boundaries.

See the [typed-reference gotcha](../../../../Gotchas/Research/Comparison/TypedBodyReferences.md)
and [streaming-discovery gotcha](../../../../Gotchas/Research/Comparison/StreamingDiscoveryBounds.md).

## Verification

New integration cases invoke the actual bulk command through subprocesses and codec-authored documents.
They cover independent reidentification, changed reference targets, discovery refusals and missing-side fingerprints.
The cases use the existing complete-suite collection and merge-queue planner, shards and report.
No new workflow or job is introduced.

Local process tests and native applications have not run under the ordinary-PR execution policy.
Static validation and current-head remote results are recorded in the delivery PR.
Process acceptance, merge-group acceptance and rendered documentation usability remain unverified until their checks run.

## Ownership

| Field             | Value                                                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------------------------ |
| Task              | `A06g-BulkComparisonFollowups`                                                                                     |
| Owner             | This chat's implementation coordinator and three disjoint subagents                                                |
| Source dependency | PR #273 revision `3da3706b388a3bdf538fcb41f01e4f127c21ae26`                                                        |
| Delivery          | Separate follow-up PR from `codex/bulk-comparison-followups`, targeting `codex/bulk-semantic-comparison`           |
| Scope             | Typed references, streaming discovery bounds, missing-side hashes and process coverage                             |
| Exit              | Scoped commits, source-bound static checks, current-head CI/review and explicit deferred process/native acceptance |

Only the designated PR #273 owner integrates changes into its branch.
This follow-up does not complete A06b qualification or change the production conversion boundary.
