# SOLIDWORKS aggregate reader regressions

The hosted run at `ec962c3955f104c2270b9c50638ba89393c32056` exposed
the conditions below. Scope is the SDK reader and its existing queue
coverage. The source observations used ordinary, disclosed tracked
archives and model-authored rectangular research pairs. [Hosted run](https://github.com/TryUniCAD/Kit/actions/runs/45056066090)

## Principal support conflicts

The native `19000` handle has separate plane ID, axis kind and
model frame owners. Changing the selected plane to another existing ID
while preserving the encoded frame crosses those owners. A strict read
continues to reject the conflict. An explicitly permissive read retains
the independently readable sketch and the rejected owner ID with an
`unresolved` support and no typed support-reference span. The
standalone P02 circle stays at sketch 26 and reports rejected plane 3.
The P01 rectangle stays at sketch 26 and reports rejected plane 2.
The P02 circle keeps its one fallback constraint and its unresolved
circular-sketch diagnostic. The existing ambiguous-handle refusal
keeps its original scope. [Handle grammar](PrincipalPlaneHandles2026.md) · [Circle and local-body hosted job](https://github.com/TryUniCAD/Kit/actions/runs/45056066090/job/137311742966) · [Plane boundary hosted job](https://github.com/TryUniCAD/Kit/actions/runs/45056066090/job/137311742981)

## Standalone circles and local bodies

The five native P02 circle inputs are hash-bound by their existing
capture receipt. Each exposes one closed circular profile and two
constraints, and its neutral JSON round trip is exact. CMgr reads from
slot 1 to next slot 17 and Config from slot 4 to next slot 106.
Their independent typed resolved traversal remains unsupported at
`moSimpleSurfIdRep_c` schema 1. The reader reports this boundary as
information alongside the existing unresolved text property notice.
The standalone profile reader continues to supply the proven circle,
origin, support and driving dimension.

For RectangularBare and ConcaveOwned, the imported feature is
`moBaseBody_c` ID 18 in ResolvedFeatures `[5086,5475)`. The
separate managed-body atom resides in Config-0 `[2129,2229)` and
`[2123,2223)` respectively. The LocalBodies streams span 1726 and
2717 bytes. Both neutral body records share the actual atom and
local-transmit provenance. Their final feature ID still links to the
resolved BaseBody record. The regression now checks both ownership
domains and retains the independent volume, area, centroid and
closed-topology assertions. [Local body names](SdkImportedLocalBodyNames2026.md)

## Rectangular sibling geometry

For all three generated comparison pairs, the SDK positively resolves
the complete geometry from both the cache-free child and the
independently generated stored partition. Their independent
boundary checks give the same counts, bounds, volume, area and centre
within the existing measurement tolerance. Linked and standalone
geometry match for each rail. The design-only and cached histories
agree. The full cold read identifies the first solid operation as a
create, and every other timeline, sketch and parameter field agrees.
An independent contrast with a present empty partition refuses with
the established missing-readable-payload error while preserving all
other streams. [Prism probe](PrismPartition2026.md) · [Hosted probe failure](https://github.com/TryUniCAD/Kit/actions/runs/45056066090/job/137311742957)

The hosted suite has yet to rerun the changes. The direct offline
observations add zero native launches, writer qualifications and
held-out results.
