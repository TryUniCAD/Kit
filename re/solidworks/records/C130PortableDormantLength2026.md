# Portable dormant length for the C130 named equation

Strict default and design-only reads now expose the named corner's independently
stored 10 mm dormant length on the existing portable extrusion and its actual
Pad-owned parameter. Both modes preserve the one-direction blind end and
the same equation operands. JSON reconstruction keeps the parameter and
feature graph exactly. [Guarded receipt](../measurements/2026/SdkC130PortableDormant01.json)

Task `B04-SW2026-CORPUS/C130-PORTABLE-DORMANT`, owner `/root/release_path`,
integration `/root`, delivery PR #121. Its exit is strict semantic transfer of
the verified independent length from the C130 source through the shared
generated archive and ordinary public reader. This step depends on the
[original source owner](SdkC130SourceOwners2026.md), [distinct dormant native
slot](SdkBlindDormantDepth2026.md) and [named equation reader](SdkNamedWidthDepth2026.md).

The actual 0.21.2 N10a source parameter is `freecad:parameter:Pad:Length2`,
owned by `freecad:feature:Pad`. Its value is also the source extrusion's
`second_length`, and the source has no `second_end_condition`. The
neutral plan uses the original name, parameter and value. The active
`Length` remains the derived 20 mm result of half the actual sketch width.

At target readback, the existing linked archive checks distinguish
`moEndSpec_c.f18` from `f20` and verify the separate ResolvedFeatures
display, handle, dimension and parameter. The actual dormant dimension
has native ID 23 and an independently owned value. The ordinary reader
binds it as `sldprt:parameter:21:D2` on `sldprt:feature:21` and sets the
same stored length on the extrusion. Its archive provenance follows that
actual parameter. This projection occurs after source graph and geometry
selection. It leaves the second end absent and does not take its value
from metadata or a display cache.

The exact 9,080-byte C130 model-generated archive remains
`5380e278a2bfd9745ddb5557b4f3584c21a96a2f26c5f243ce8b4065783093f9`,
including every prior stream hash. The linked solid retains the named body,
six faces, twelve edges and eight vertices, 16,000 mm³ volume and
4,000 mm² area. An additional model-only 7.5 mm dormant input changes the
emitted bytes and the recovered parameter while the active body geometry
and owner stay identical. An active second end, crossed dormant owner,
duplicate dimension ID, unowned expression reference and alternate
sketch operand retain their existing strict refusals.

The independent canonical control still reproduces
`5783b3944d76563ae8143b8789a923f1b07fb4eb94f4b59fef50b6b80ac696b6`,
the previously native-measured Reference candidate with healthy controls.
Its complete full and design-only neutral documents remain byte-identical to
the frozen baseline. The earlier pre-writer lock qualifies the canonical
`D1` local-reference family. Target `width`/ `Length` naming, the
independent `Length2` transfer and the exact C130 output still require
their own native measurements. Both ordinary public write entry points
continue to refuse intact C130 and its named native readback. This step
earns zero C130 native publication or benchmark credit. [Measured
canonical control](../measurements/2026/SdkWidthDepthPreparationNative01.json) ·
[Locked canonical lifecycle](WidthDepthLockedEvaluation2026.md)

## Reproduction

Use the exact disclosed C130 census manifest and ordinary equation request.
The two controllers use the frozen baseline and eight fresh guarded SDK
processes. They emit machine-readable digests, owner joins and exact
refusals, with zero runtime data reads after input intake.

```sh
python3.14 -I -B re/tooling/sw2026/freecad_census/owned_pad/ProveC130Owners.py --inventory /path/to/VerifiedInputs01.json --equation /path/to/WidthDepthSameLocator04/Neutral.json
python3.14 -I -B re/tooling/sw2026/equations/ProveNamedWidthDepth.py --inventory /path/to/VerifiedInputs01.json --equation /path/to/WidthDepthSameLocator04/Neutral.json
```
