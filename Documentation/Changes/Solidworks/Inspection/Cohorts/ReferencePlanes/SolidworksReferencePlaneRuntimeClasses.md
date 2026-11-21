# Reference-plane runtime-class publication

[ReferencePlaneRuntimeClass.py](../../../../../../re/tooling/sw2026/ReferencePlaneRuntimeClass.py) independently follows the pinned model's selected runtime-class accessors and verifies the ordinary archive's actual class-publication call. It distinguishes the concrete default constrained-plane RTTI type from its published base archive name, while the distance geometry retains its own name.

Use the tool with original external `sldmodu.dll`, `swccu.dll`, the checked-in 2026 serializer map and an unused receipt output, with `pefile==2024.8.26`. It records only identities, names, addresses and hashes; no target executes and no vendor listing is emitted. The serializer-map interface and existing shared writer/SDK bytes remain unchanged.

The [rule record](../../../../../../re/solidworks/records/ReferencePlaneRuntimePublication2026.md), [receipt](../../../../../../re/solidworks/measurements/2026/ReferencePlaneRuntimeClassPublication01.json) and [gotcha](../../../../../Gotchas/Conversion/Solidworks/Model/ReferencePlanes/RttiClassNamesCanDifferFromArchiveTags.md) bind the exact construction/load boundary. The real offline PE inspection passed for default, base and distance owners. The prepared typed audit was corrected before any native source file was decoded; source correlation and generated native acceptance remain pending.
