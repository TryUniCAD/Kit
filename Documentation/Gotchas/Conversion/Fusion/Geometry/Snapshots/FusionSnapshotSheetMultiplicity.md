# Fusion snapshots can contain coincident sketch sheets

The DiscFlip source snapshot contains more than one single-face sheet body. Requiring exactly one sheet, or exactly one coincident sheet-cap pair, prevents a malformed-label fixture from reaching the production label guard. The [queue report](https://github.com/TryUniCAD/Kit/actions/runs/45038401602/job/137257441148) showed this failure before the public CLI was invoked.

Select a deterministic eligible pair by stable entity references. Require an untagged planar sheet, a physical cap at the same axial station, and a standalone label chain owned by that cap. Moving the cap label onto any such sheet preserves the attack: an untagged physical solid face cannot be rescued by labels attached to sketch geometry. Keep production physical-label validation enabled; sheet multiplicity does not relax it.
