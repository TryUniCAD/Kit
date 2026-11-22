# Strict SDK projection of the saved Standard sweep

PR #121 task B04-SW2026-MEASURED-SWEEP. This read-side follow-up to
the [measured cold delivery](ScopedSweepReadback2026.md) uses exact
configuration and result ownership from the
[linked archive replay](ScopedSavedSweepReplay2026.md) and
[typed result audit](ScopedSavedSweepTopology2026.md). The two original
parts and four independent Section or Path edit saves are the same
disclosed sources in lock `563aef5da24478ab83b881092561dd09066ad9b8e3999ca1da106e00e22420ca`.
The original SOLIDWORKS 2026 SP05.2 `34.5.2.0604` batch had ten passing
source phases and both healthy controls.

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Corpus correlation](../../Playbook/CorpusCorrelation.md)

## Portable ownership

The current reader uses the actual Config-0 and CMgr context to read the
resolved graph and its empty body-mapping suffix. It uses the shared
current native layouts for saved body references, history and displayed
dimensions. The reusable layout source is pinned at `f59507fcc` and the
kernel label and atom helpers at `4cd5aee92`. The reader preserves the
completed cold sweep context at `b05889d99`. The physical selected lane,
native configuration and header
file entry agree. The source-author originals store the name `Part1`
and an empty self path. The edited saves carry their actual stored native
self file entry. The source hash remains the whole supplied archive.

The `moHistoryFolder_c` members bind the two earlier local sketches and
the single active `moSweep_c`. Independent D1 values come from their
actual `moLengthParameter_c.f58` nodes. The selected Section transport
and both physical ghosts must agree with the live profiles. The neutral
Section circle retains its exact shared start/end position in
`SketchEntity.attributes["periodic_seam"]`, with the local millimetre
point, centre index, shared start/end index and actual persistent point
marks. Each Section edit rotates that point by 17 degrees. Each Path
edit retains its original orientation and changes its own radius.

The physical partition owns one solid, three faces and two periodic
edges with zero native vertices. Both shell sides and all reciprocal
FIN links are checked before geometry is exposed. The body label and
appearance come from their typed kernel attributes. The active body
binds to the same Config-0 result atom and CMgr feature link. The body
density matches the configuration's actual density parameter. The
retained chooser references, face stamps and manager stamp words bind
to the same concrete creator. The configuration property reader also
checks the compatible empty binary owner and applies the actual literal
summary, document and configuration property scopes.

The B-rep uses the shared analytic geometry decoder to retain the saved
carrier frames. Its periodic seam anchors represent closed neutral
edges. The trim projection derives two planar circle and two toroidal
line pcurves from the actual rims and their opposite FIN incidences.
Each wall pcurve follows the raw circle's `dv/dθ=-1`; actual coedge
orientation gives `(-1,+1)` across the two walls and caps in each saved
chart. Parameter curves follow the native kernel rim phase, independent
of the movable Section sketch point.

[Signed manager stamp](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/SavedSweepManagerStamp.md) ·
[Independent sketch and rim seams](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Partition/SavedSweepSectionAndRimSeams.md)

## Verification and remaining scope

The offline supervisor runs six fresh SDK processes. Each process verifies
the locked whole file digest and reads through both normal SDK routes.
It checks explicit Default, design-only readback, exact neutral JSON
round-trip, owner linkage and the independent saved native volume, area,
mass and centre. It checks four chart positions on each rim. Cross-model
physical result and ghost substitutions, a traced wrong trim frame and
a wrong density owner are refused. The guard observes zero runtime file,
process or network access after initialization. The external-input
research command supplies the disclosed sources by hash. The general
tracked-asset pipeline lacks this exact external-input supervisor.

The pinned cold control runner independently checks both complete
generated native archives and their 22 physical streams, strict neutral
projections, exact attested re-export and rejected public requests. Its
reproduced receipt SHA-256 is
`996e1d0fbebb38f97cd32eec7d81fe84da2032552c1a2c2c45216a8162888222`.
The six-process saved receipt SHA-256 is
`f99827c82500e6adbec197f83def500d011216b365a6ebbdee2c891f2178ec56`.
The saved source models fail cold writer eligibility. These source readback
observations supply zero new native publication, held-out, or wider
sweep credits. Other result layouts, custom contours, wider assembly
context and delta generation remain outside this evidence.

```sh
python3.14 -I -B re/tooling/sw2026/sweep_source/CheckSavedSweepSdk.py \
  --disclosed /path/to/SweepBossSource07/DisclosedNative
python3.14 -I -B re/tooling/sw2026/CheckScopedSweep.py \
  --native /path/to/SdkSweepColdDisclosed02
```

[Six-process source read receipt](../measurements/2026/ScopedSavedSweepSdk01.json)
