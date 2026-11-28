# A cache-free circle requires its own strict geometry route

The public circle writer produced a complete parametric native part and its history could be read with `include_brep=False`. Default strict reading still rejected that same part because the cache-free geometry dispatcher admitted prisms, circular cuts and revolves, but no standalone circular boss.

History-only success did not prove that the normal geometry entry worked. The repaired route validates complete circle/profile/boss/datum/parameter ownership and uses the shared analytic cylinder builder. It retains the two existing public writer profiles and refuses extra or unsupported state. Do not use history-only reads to claim whole-document geometry acceptance.

The [process receipt](../../../../../re/solidworks/measurements/2026/SdkColdCircleRead01.json) reproduces both original refusals and reads the exact unchanged outputs through the repaired default entry. [Detailed scope](../../../../../re/solidworks/records/SdkColdCircleRead2026.md).
