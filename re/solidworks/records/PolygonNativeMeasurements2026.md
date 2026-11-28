# Generated polygon geometry, depth edits and reopening

Status: all three locked polygon cases pass this measured procedure. This is
research evidence for the straight-edge polygon/blind-extrusion subset, not
production writer support or completion of the broader SOLIDWORKS goal.

The [full report](../measurements/2026/PolygonDepthEdits.json) records the fresh
process sequence, native feature trees, exact executable identities, dimensions,
geometry, error queries and hashes. Its raw report SHA-256 is
`b81763cc263fe4dc124d967329a480f039822f106106d5df4adf7f53c4705759`.

## Provenance and source separation

The [source lock](../v2026/heldout/polygon/Lock.json) predates the polygon emitter
and retains three 2026-authored native source hashes and neutral specifications.
The writer consumes only those neutral specifications. The locked native streams
were not inspected to build these outputs and are never writer inputs.

Remote process job `132815940695`, run `43715472183`, produced artifact
`14162162423` from writer head `0212d3ce3b391ebfdaac133a33ed049407c287cd`.
Follow-up artifact `14162499059`, job `132819239580`, run `43716549792`, from
head `01ab460e96433cd936dd4158f3a3f6e0a09d30b6`, independently regenerates all
five files to identical bytes. Its synthetic merge
`d7c9fb2dc2dbd639390dfbf609d7ebc199ea3b8f` has that source head as a parent.
The report also hashes the unchanged writer builder files.

| Generated case        | Original generated SHA-256                                         |
| --------------------- | ------------------------------------------------------------------ |
| H3 scalene triangle   | `f3318f14461e16d410125aef041e68c293becbbb3a8ddc0cff544cee13d2409a` |
| H5 irregular pentagon | `d63afd3c9df32bf95a4349b17dd1725e0ddcf700f51e69dcc762d995376ad4c9` |
| H7 irregular heptagon | `dc67dd90374e91fa023eff8faab79c7fbe3620556eb6640371b338345ccc4cfc` |

The generated before/after rectangular candidates were also byte-identical
across those remote runs. They are not the original native oracle controls and
are not counted as additional held-out cases in this measurement.

## Controlled native sequence

Committed inspector head `0af3042a34e2549670cbad69eca7a90a3132d272` ran through
Parallels current-user execution and COM `SldWorks.Application.34`. Every phase
verified executable version `34.5.2.0604`, SHA-256
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.
Every phase starts a fresh SOLIDWORKS process, so the batch never accumulates
twenty document launches in one process.

An original native L1 control passed before the cases. Each generated input then
opened and rebuilt without intervention. A fresh process changed its live
`D1@Boss-Extrude1` depth, rebuilt and saved to a distinct new native copy. Another
fresh process reopened that copy. The original control passed again afterward.
Every original generated input and the control retained its input hash.

All native open, feature and save errors and warnings are zero. Each baseline,
edited model and reopened copy has one body. There are no dialogs or cleanup
errors. The unedited geometry matches the locked source measurements. Edited
expectations come from the neutral polygon's area, perimeter and centroid:
`volume = area × depth`, `surface area = 2 × area + perimeter × depth`, with
the unchanged in-plane centroid and `depth / 2` along the normal.

Comparison uses relative tolerance `5e-7` and absolute tolerance `1e-15` for
near-zero coordinates. Each baseline, edit and reopen comparison passes.

| Case | Original depth (m) | Edited depth (m) | Original volume (m³) | Edited/reopened volume (m³) |
| ---- | -----------------: | ---------------: | -------------------: | --------------------------: |
| H3   |              0.013 |          0.01625 |          0.000009932 |                 0.000012415 |
| H5   |              0.007 |          0.00875 |         0.0000131635 |              0.000016454375 |
| H7   |              0.017 |          0.02125 |         0.0000537965 |              0.000067245625 |

The full report retains every measured area and center of mass, parameter
readback, original source hash and edited-copy hash. Edited native copies are
verification outputs only and are not used by any writer.

## Limits and next work

This procedure does not establish all sketch curves, construction geometry,
relations, dimensions, placements, end conditions, advanced features,
configurations, assemblies, source round trips or the 165-part FCStd target.
It does not enable `SldprtAdapter` writing. The subsequent
[viewport inspection](../measurements/2026/PolygonViewports.json) finds visible
models but incorrect standard-view orientation: isometric selection still shows
the generated front faces. Native null-view fallback does not reconstruct the
indexed orientation constructor. Generated view records and broader field/feature
acceptance remain work before any product claim.
