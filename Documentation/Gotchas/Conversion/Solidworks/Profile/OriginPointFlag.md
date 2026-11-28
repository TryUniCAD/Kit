# Origin identity is separate from point type

## Expectation

Setting an origin point's type to one also makes the native point report that it is the origin

## Actual behavior

Native initializer `sldmodu 0x4c49b980` sets both point type one and a separate runtime integer at point `+0x148`
The latter write appears as `local_40=1` in the decompile, but instructions `0x4c49b9b6` and `0x4c49b9c4` place it inside the point object at stack offsets `+0x160` and `+0x2a8`
Serializer instruction `0x4c58f98b` encodes that integer in packed point flag bit zero; loader instructions `0x4c5902ae` through `0x4c5902b7` restore it
The native origin getter at `0x4b340ec0` tests this integer, rather than the separate point type at `+0xe4`

## Workaround

Generate packed flag bit zero from the semantic document-origin operation
Keep the bit clear for ordinary polygon points
Do not treat overlapping decompiler locals as independent objects without checking their stack offsets
This rule supplies origin identity and does not establish post-solver status or complete generated-file acceptance

See [the origin construction evidence](../../../../../re/solidworks/records/ProfileConstruction2026.md#origin-profile-construction) for the locked binary binding
