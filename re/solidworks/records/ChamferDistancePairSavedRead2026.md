# Read two saved SOLIDWORKS 2026 edge distance modes

The two disclosed SOLIDWORKS 2026 SP05.2 designs each use an ordinary
forward blind rectangular stock on Front, one selected convex axial edge,
one solid and the active `Default` configuration. Mode 18 has the shared
D1 distance, persistent ID 33, at 4.875 mm and 6.125 mm. Mode 2 has D1 at
4.875 mm and an independent D3, persistent ID 34, at 8.375 mm and 9.625 mm.
The four source pins come from the prior [linked archive replay](../measurements/2026/ChamferDistancePairArchive01.json)
and [selector inspection](../measurements/2026/ChamferDistancePairSelectors01.json).
The records cover two disclosed author/edit lifecycles on shared stock.

## Owned archive and geometry

The actual stock is the atom's creator and the distance chamfer is its
modifier. The part, stock and chamfer controllers select the actual four
typed states of the saved kernel rollback. The original states walk
13 → 11 → 3 → 1 and the edited states walk 21 → 19 → 3 → 1.
The stock and active solids share the transmit body slot, with the actual
body tag, atom and respective last-modifier/name owners. The original
rollback revives edge slot 222. The edits revive slot 221. Both reference
fragments bind the same ordered side 3, side 2, end 1 and end 0 roles.
The positive fin proves their exact physical ordering. The live bevel
carries the result keeper's producer, creation event and ordinal 1.
The other six physical faces retain the actual stock keys.

The original historical self files and both headers agree on an empty
path, nonempty document name, local file kind, default configuration and
epoch. The edited saves provide matching explicit local paths. The
historical self also aliases the file retained by the earlier stock
chooser. The reader performs all of those checks in memory.

The stock carries its live D1 alone in `moEndSpec_c.f18` and keeps the
two empty option arrays. The inactive end display pointers are null.
The earlier exact native dispatch proof classifies `f150/f154` as
surface-operation controls outside the ordinary solid branch.
The stock's saved line, relation, region and contour owners confirm the
same complete rectangle. The neutral first-creator guard now accepts
the sole exact direct terminal Chamfer while retaining the preceding
solid, profile and driver requirements. [Solid end dispatch evidence](SdkWarmNestedLeaf2026.md)

Strict readback uses the actual active B-rep from
`Contents/Config-0-Partition` and attaches its neutral body identity.
The independently rebuilt analytic boundary validates every oriented
ring. Actual trim endpoints, line and plane carriers, native face
ownership, and the six predecessor faces are verified separately.
A validated result has 7 faces, 15 edges and 10 vertices. The geometric
volume, area, center and bounds also match the independent cut triangle
calculation for each original and edit. The semantic-only route verifies
the same owners while omitting the B-rep and payloads. Raw extraction
keeps its established direct payload behavior.

The scoped read retains the typed drives, selectors, complete public row
order and existing source provenance. The existing native publication
restrictions still apply. The six saved calculation words are recognized
as retained option data. Their use in a regenerated archive, source
styles and whole native transfer have separate evidence requirements.
[Retained option authority](ChamferColdOwners2026.md#saved-options-array-starts-empty)

## Guarded replay

Run the [fresh-process verifier](../../tooling/sw2026/edge_chamfer_source/distance_pair/ProveWarmPairRead.py)
against the four read-only disclosed files. It accepts
`EqualOriginal.SLDPRT`, `EqualEdited.SLDPRT`, `UnequalOriginal.SLDPRT`
and `UnequalEdited.SLDPRT` and checks each hash before passing its bytes
to the worker.

```sh
python3.14 -E -B re/tooling/sw2026/edge_chamfer_source/distance_pair/ProveWarmPairRead.py \
  --folder /absolute/path/to/DisclosedWarmSources01 \
  --signed-trial /absolute/path/to/GeneratedChamferSigned01/Packet/Trial.json \
  --report /tmp/unused-ChamferDistancePairSavedRead01.json
```

The [receipt](../measurements/2026/ChamferDistancePairSavedRead01.json)
binds the exact four cases, native source authorities and changed reader
files. It covers both public read routes, the explicit raw extraction
control and guards for a missing partition, foreign live owner, foreign
rollback and history file, crossed selector keeper, physically stale
geometry and a false terminal scope owner. Two further guarded jobs
generate the existing signed-angle controls from their disclosed neutral
plans and match the previous complete archive and SDK document hashes.
The six workers perform zero external input reads. No new CAD oracle launches or protected files are involved.
