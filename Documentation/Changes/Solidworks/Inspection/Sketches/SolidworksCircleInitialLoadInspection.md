# Circle body and feature checks before explicit rebuild

`re/tooling/sw2026/InspectCircleSketch.py` now records native body count, rebuild-problem count and the complete feature tree immediately after opening each generated or saved circle candidate, before calling any explicit rebuild. It requires the requested sketch and blind boss to exist with their original names, native types and active suppression state. A blind boss must already have one solid body; a sketch-only input must have none.

The body query precedes feature and dimension traversal. These observations do not establish a rendered viewport or exclude internal work performed by the native open/query APIs. The existing explicit rebuild, geometry, frame, mass, editable radial/depth parameter, save, fresh-process reopen, healthy-control and input-immutability checks remain required. The inspector retains both the initial observations and rebuilt snapshot before rejecting an initial-state failure, so an explicit rebuild cannot conceal the initial condition.

Freeze the inspector and its imports from a committed revision, bind every unchanged generated input to its original remote generation receipt, choose an unused external job/output location and run through the existing host supervisor and reserved VM. Schema `kit.sw2026.circle-sketch-inspection.v4` distinguishes these observations from earlier measurements that began with explicit rebuild.

Verification at introduction: source/AST review only; no local tests or archive-schema execution. A new native batch is required before claiming initial-load body presence. This adds a research measurement boundary, not production writing or complete CAD acceptance. Held-out native payloads remain sealed.
