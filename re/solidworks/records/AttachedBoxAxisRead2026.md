# Strict readback of the disclosed signed box with principal axes

This step of `B04-SW2026-FCSTD-BOX` covers the controlled FreeCAD 0.21.2
F14c comparison under PR #121. The strict SDK read opens the 10,707-byte
cold SLDPRT `0d4cba0b66e443e487793204dc82985d5206704a0646b63afb1a4c410b1c54cc`
and returns `Body`, its signed analytical solid and three `PlaneAxis`
features. Six independent neutral selections link the axes to their
actual ordered support planes. [Frozen construction](AttachedBoxAxisCandidate2026.md)
[Guarded SDK receipt](../measurements/2026/AttachedBoxAxesSdkRead01.json)

## Checked ownership

| FreeCAD owner | Linked SOLIDWORKS root | Ordered support roots | Portable signed extent in mm |
| --- | --- | --- | --- |
| `1778` `X_Axis` | `27` `X-axis` | `15` Top, `14` Front | X −1 to 21 |
| `1779` `Y_Axis` | `28` `Y-axis` | `14` Front, `16` Right | Y −10.5 to 0.5 |
| `1780` `Z_Axis` | `29` `Z-axis` | `16` Right, `15` Top | Z −1.5 to 31.5 |

Every `moRefAxis_c.f700` reaches one `moPlaneInterAxisData_c` and
owns two independent `moPlaneRef_w` wrappers through `f80` and `f88`.
The component references identify the actual principal datum, part
owner and creation stamp. The axes have matching creation records
in both headers and an allocator frontier agreed by CMgr. Each starts
at `f18`, ends at `f30` and follows the cross product of its ordered
support normals. Its signed stations agree with the axis words and
the first support rectangle computed from the box. The sized datum
centres, label anchors and four borders come from the signed physical
box, whose size allows only a short floating-point rounding budget.
The proof isolates 27 additional linked owners before the existing
prism inventory check so all other members still require a known role.

The signed origin box has bounds `(0, −10, 0)` to `(20, 0, 30)` mm,
volume 6,000 mm³, area 2,200 mm² and centroid `(10, −5, 15)` mm. The
full vertex, edge and face incidences agree with all three validated
FreeCAD shape owners. The source profile owns length 20 mm and width
30 mm. The reversed blind boss owns height 10 mm. The tested exact
archive returns all 22 native roots in linked source order and
preserves the six wrapper spans through ordinary neutral JSON.

## Process evidence

Two fresh isolated Python workers consume supplied bytes over stdin
with an input and process audit. Both runs agree, preserve the earlier
axis-free measured control and retain the ordinary history-only read
option. Crossed wrappers, shared component owners, an internally
consistent stale station, stale plane and wrapper borders, a hidden
axis and a foreign creation log each refuse. The top-level strict
rejection keeps the normal missing-geometry error. Unmeasured direct
and registry output requests preserve the caller's stream bytes and
position. The receipt binds the changed reader files, the three source
affected axis IDs and the independently observed initial native axes.

Trial02 completed on SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`.
The immutable terminal receipt SHA-256 is
`0ac0c750cd671a2f4c5dcc7e3459d79a51199c3c0cd7220ba8cc2dd6a953ac38`.
Two controls bracket the generated and fresh-reopen processes.
The compare checks 336 values in the generated process and 192 in
fresh reopen. The axes are positive and selectable with both real
parents on all measured native states. The host read compares actual
native initial and reopened axis observations against the exact cold
model and the original FreeCAD axis carriers.

The SDK path covers cold signed Top-origin rectangular parts with one
verified body and three ordered visible principal axes. SDK reading of
native-saved derivatives, viewport visibility, public intact-source
transfer accounting and historical corpus membership require separate
qualification. This step earns zero benchmark or held-out credits.

```sh
python3.14 -I -B re/tooling/sw2026/attached_top_box_source/VerifyAttachedAxisRead.py \
  /path/to/recipe-0.21.2-F14c.FCStd \
  /path/to/AttachedBoxAxesCandidate01/F14c.SLDPRT \
  /path/to/axis-free/F14c.SLDPRT \
  /path/to/AttachedBoxAxesTrial02Evidence/Result.json \
  /tmp/AttachedBoxAxesSdkRead01.json
```
