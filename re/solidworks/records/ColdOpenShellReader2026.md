# Fresh SOLIDWORKS 2026 inward open-shell readback

The #121 takeover owns this strict SDK reader slice on
`codex/solidworks-cold-open-shell-read`. Its local base combines the
neutral shell constructor from [#252](https://github.com/TryUniCAD/Kit/pull/252)
at `4fdb5e89f3b93ea1d78a188ee2117d82a98efd00` and saved strict readback
from [#255](https://github.com/TryUniCAD/Kit/pull/255) at
`15749182cdb3142fcab0fbe9719bea21d4a44ee7`. The separate delivery PR and
shared queue acceptance are pending. The reader exit condition is
independent guarded SDK readback with unchanged saved and ordinary
controls. Native generation still has its own output lifecycle and
held-out exit conditions.

The cold branch requires the ordinary cache-free inventory, one
`Default` configuration descriptor shared by CMgr `f360`, `f368` and the
unique `f370` row, and no saved `f450` association or activation marker.
The actual stock output and shell's `f538` alias the sole Config-0 atom.
The atom retains both feature identities with zero saved body stamps.
The stock and shell carry fresh body states without partition marks.

The stock is a free four-line local Front rectangle with a positive
forward blind driver. The shell's `f828` selects the earlier terminal
cap. Its four side references and the ordered `f848` auxiliary
reference resolve the real sketch segments, common file and stock
creation event. The auxiliary reference contributes no second removal.
The thickness comes from the independent `ThreeDRadiusDim_c.f28` live
parameter and matches the linked display value. The twenty ordered
public feature roots come from the typed graph. The fresh sketch
retains its actual unconstrained state.

The stock prism and inset cavity share the proved stock bounds and
wall thickness. The outer terminal cap takes the reversed cavity loop
as its inner rim. The inner floor and walls reverse their face uses.
The reader checks the resulting boundary, signed volume, surface area
and centroid against the inward offset. Full reads bind the result to
the actual design body without a fabricated native payload or kernel
identity. Design-only mode retains the same drivers, cap, feature
ordering and measured summary.

| Guarded case | File bytes | Stock and shell D1, mm | Volume, mm³ | Area, mm² | Centre Z, mm |
| --- | ---: | --- | ---: | ---: | ---: |
| Calibration | 8,885 | 28 and 2.8 | 18,559.408 | 13,783.12 | 10.810327743 |
| Translated | 8,919 | 36 and 4.15 | 34,018.7535 | 17,224.58 | 14.901582932 |
| Distinct | 8,914 | 23 and 1.875 | 14,392.1484375 | 15,775.375 | 7.852969046 |
| Independent synthetic neutral | 8,949 | 33.25 and 3.1 | 28,355.824 | 18,971.43 | 12.843963607 |

The [guarded process proof](../../tooling/sw2026/shell_source/CheckColdShellRead.py)
rebuilds each neutral request in memory. It checks all three disclosed
whole archives against the [prior typed owner receipt](../measurements/2026/GeneratedOpenShellOwners01.json)
and independently repeats the synthetic request. Both strict modes and
ordinary neutral JSON round trips pass. Eight transient contrasts each
refuse in both strict modes and stay native-only in permissive
inspection. The guarded workers have zero runtime data reads and launch
no CAD processes. Both direct and public registry publication refuse
without writing to their sinks. The [shared queue integration](../../../tests/Convert/Solidworks/Partition/ShellCacheTests.py)
uses the independent synthetic case.

```sh
python3.14 -I -B re/tooling/sw2026/shell_source/CheckColdShellRead.py \
  --generated /path/to/disclosed-generated-archives --output /tmp/KitColdShellRead.json
python3.14 -I -B re/tooling/sw2026/shell_source/CheckColdShellRead.py --model
```

The [two saved shell and L1 control runs](../measurements/2026/SdkSavedOpenShellRead02.json)
regenerate the same receipt, including the crossed active and rollback
contrast. The ordinary measured chamfer comparison keeps its exact
archives and strict typed round trips. Four disclosed warm chamfer
controls continue to refuse unqualified strict history and retain
their permissive boundary and exact native payload hashes. These
comparisons reuse earlier measured cases. A native lifecycle and
independent held-out qualification remain separate work.
[SDK proof](../measurements/2026/SdkColdOpenShellRead01.json)
