# Saved Standard sweep replay against the scoped SDK

PR #121 task B04-SW2026-MEASURED-SWEEP. This disclosed archive replay covers
the two previously authored Standard sweep parts and their four native
Section or Path edit saves. The original SOLIDWORKS 2026 SP05.2 lock
`563aef5da24478ab83b881092561dd09066ad9b8e3999ca1da106e00e22420ca`
binds the six files to build `34.5.2.0604`, ten source phases and two
healthy bracket controls. All six file digests and the prior exact
replay receipt are checked before the new decoder reads any source.
[Existing source scope](ScopedSweepReadback2026.md) ·
[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Corpus correlation](../../Playbook/CorpusCorrelation.md)

## What replays

Six fresh SDK processes reproduced the four complete uncompressed
archive streams below. Each used the scoped SDK source at
`ab4c5b98b5fdb7b49146601ffc5731aa0b6a095d` in a temporary directory
and the source-only shared archive closure from
`f59507fccdd5907954634489f54ab1364f44580e`. The receipt lists the 17
overlaid archive source hashes. The preceding aggregate comparison is
`daebc428bffb80ab45ca6f2ddb17984c8f155f7a`. The `Config-0` and
`ResolvedFeatures` stream digests match that earlier replay.

| Stream | Verified boundary |
| --- | --- |
| `Contents/Config-0-ModelHeader` | Standalone typed header with the actual file, time and feature creation references |
| `Contents/Config-0` | Map next slot 110 and one live `moAtom_c` at slot 58. Ghost definitions remain in the actual configuration |
| `Contents/CMgr` | Independent map next slot 19. `f658=1` and `moLinkedAtomIdNode_c` at slot 10 refers to the same atom ID 101 |
| `Contents/Config-0-ResolvedFeatures` | Inherits 110 and extends to 278. Twenty roots followed by the manager-driven zero-entry `fcd8` array |

The history folder owns three `moHistoryFeatItemData_c` children at
slots 120, 124 and 127. Each `f48` links a local `moCompFeature_c`
at slot 122, 125 or 128. Their feature identities and creation-log
values resolve to the actual Section 26, Path 28 and sweep 31. Both
radial displays reach a positive `moDisplayItem_c.f2b0` array with
one signed word. The stored display values 200 and 201 are observations.

The sweep owns its actual `f4a8` chooser and that chooser points back
to the sweep. Its two face references link to distinct
`moSweepSideSurfIdRep_c` objects at slots 243 and 259.
Each uses the traced shared entity-representation base and two signed
words. Their component references identify sweep 31. `f528` aliases
the real configuration atom and `f498` refers to 101. The Section and
Path pick their actual earlier sketch roots and distinct ghost IDs.
Their live diameter and radius `D1` values match the locked inputs
exactly, with persistent dimension IDs 27 and 29.

Saved `f2b4/f2b8` are both one. The embedded Section sheet retains
ten resident kernel nodes and `BODY.next=2`, with no resident
node 2. Its raw and compressed frames re-emit from those typed nodes.
The meaning or generative allocation of that saved sibling remains
open. The temporary context enables the existing declarations before
loading data and uses the measured `f658=1` for actual parsing.

## Next reader boundary

The ordinary Parasolid geometry reader extracts the closed saved solid
with two planar caps and one torus. The raw shell confirms shell 7,
owner 3, region 38 and body atom 101 in each source. The torus radii
agree with the live drivers within one binary64 step in millimetres.
The extracted model has four coedges and no exposed pcurves. The full
typed kernel reader consumes 49 records and stops at class 54. The
kind occupies bytes `[2519,2521)` of the uncompressed transmit in all
six saves. A full physical result
replay or portable trim projection remains open.

The two Section-edit sources retain their actual rotated seam point and
trigger the cold-only incidence restriction. The other four Section
sketches and all Path sketches match that restriction. A saved profile
reader needs to preserve the actual seam and validate the result
trim/owner linkage before exposing the full portable result. The
public saved sweep refusal remains in place.

## Reproduce

```sh
python3.14 -I -B re/tooling/sw2026/sweep_source/AuditSavedSweepMain.py \
  --disclosed /path/to/SweepBossSource07/DisclosedNative
```

The capture and original replay use the existing disclosed source
lock. The external-input tool handles the scoped SDK overlay that the
tracked-asset research command cannot express. Each worker loads the
checked bytes before enabling the file, process and network guard.
It returns only identities, spans, digests and numeric observations.
The receipt records the Python and zlib versions used for frame replay.
The receipt records zero runtime accesses, new native launches,
written archives and held-out credit.

[Six-process receipt](../measurements/2026/ScopedSavedSweepReplay01.json)
