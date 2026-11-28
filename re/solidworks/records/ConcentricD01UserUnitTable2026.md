# Standalone user unit tables in ordinary assemblies

Task `B04-SW2026-MATES-CONCENTRIC/source-unit-table` in PR #121,
owner `assembly_frontier`, base
`9dca0bd65a4762962b0d71b896cdd354eb405a98`. The evidence uses the
already disclosed SOLIDWORKS 2026 SP05.2 `34.5.2.0604` assemblies
and the existing independently authored unit preference cases. The
scoped exit is complete construction of the standalone unit stream
from the actual neutral-generated assembly model.
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Prior bookkeeping result](ConcentricD01StampStreams2026.md)

## Confirmed stream and object ownership

All six D01/D02/D03 source and edited parents and four separate
native-authored assembly controls (A0, A1, A13, A14) have
`Contents/User Units Table`. The complete standalone stream is
an exact serialization of their own `moAssembly_c.f9b8` from
the linked Config-0 graph. Each case rebuilds the complete 1,487
bytes independently from both typed views. The standalone map
starts at 1 and ends at 36. The embedded table follows the actual
inherited Config-0 map. Each table has 16 ordered unit rows.
The primary length row owns an independent dual length object.
No analysis table is stored in this scoped model.

The assembler uses the same typed scalar, class and object
layouts as Config-0. A standalone archive owns fresh tags and
indices. It need only refer to the actual generated embedded
unit object. It takes no source stream, static offset, capture
mapping or separate copy of the unit values from its caller.
[Existing typed unit grammar](ConfigUnitTableSlice2026.md) ·
[Independent dual unit rule](RevolveSourceUnitOwners2026.json)

## System information XML and locale

The same ten assembly captures show `(4, 0, 0, 2, 1)` in the
binary ordered system, length, angle, force and density mass roles.
The corresponding XML integer properties read `(5, 0, 0, 3, 2)`.
The existing two-design native mass-unit experiments provide six
independent source states. Both designs show these declared system
and mass transitions.

| Authored settings | Binary system / mass | System XML system / mass |
| --- | --- | --- |
| MMGS with grams | 4 / 1 | 5 / 2 |
| Custom with grams | 3 / 1 | 4 / 2 |
| Custom with kilograms | 3 / 2 | 4 / 3 |

The two XML properties agree with their own distinct registered
2026 preference enums. The linear, angular and force observations
cover only the actual measured choices. As a result this proof
does not implement a general offset conversion between XML
and binary unit codes.
[Registered preference evidence](DocumentMassUnits2026.md)

The independently parsed short and long date properties describe
the same calendar dates with month/day/year and English weekday
and month names over November 14, 16 and 18 in the assembly
captures. Their History language words are all zero. Those zero
words supply no locale selector for generating the observed
date strings. A second native locale and an independent explicit
save date or time-zone contrast are needed to identify all locale
and clock inputs for system XML. No part archive code is changed.

## Guarded construction and exact source boundary

With the same neutral request as before, two isolated workers
construct identical 14,196-byte parents, SHA-256
`788755fe167bc6c125794b7dc668587909d319397cf580c226a9e5425e8e2609`.
All 20 earlier parent streams and the entire generated child
stay byte-identical. The only added stream is the 1,421-byte user
unit table, map 35, generated from the actual parent MMGS display
units at precision four. The new stream re-emits exactly against
the same parent's embedded map and values. This reproduces the
currently modeled generated display state.

The workers separately construct genuine IPS and MKS unit profiles
with explicit precisions three and seven. Their tables differ.
Each optional, independently generated dual length child advances
the map by one and grows its table by 66 bytes. The reused class
reference replaces the existing null tag of equal width, leaving
the complete added child body of 62 inherited bytes, two unit
bytes and a null child tag. The actual code chooses the opposite
metric or inch length role. A foreign mirror, trailing data,
a duplicate stream, an analysis alias and an unsupported optional
density length graph all fail closed. Generation observes zero
external file accesses, network requests or CAD launches.
[Guarded receipt](../measurements/2026/ConcentricD01UserUnitTable01.json)

```sh
python3.14 -I -B re/tooling/sw2026/para/concentric/ProveD01AssemblyUnitTable.py \
  --disclosures /absolute/path/to/Oracle121Takeover
```

The original's display state has precision two and a real inch
dual child. The shared dual constructor matches every field of
that child. A fresh MMGS table even at precision two still
differs at primary length `f18/f20/f28` and density `fcc`.
The first three fields require their own primary formatter
inputs or causal constructors. The density slot selector is
independent of the measured display units. Both volume slots
store the same code in this group. The current assembler
keeps its existing neutral-format values and adds their matching
mirror. It does not transfer the full source presentation.
[Primary formatter boundary](SdkRevolveSourcePreparation2026.md#implemented-boundaries)

The original assembly still refuses `CheckAsmRoot`. The modeled
parent now has 21 streams, with 22 saved source members still
outside the generated inventory. The full system XML, linked
document state and the other source conditions remain open.
Neither the original source nor the generated bundle gains public,
native or held-out qualification.

The [property transport proof](ConcentricD01PropertyTransport2026.md)
adds three streams from the actual generated property membership and
preserves this unit mirror and the other generated owners exactly.
