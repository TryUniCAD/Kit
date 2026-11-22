# Attached FreeCAD box and its origin axes

The measured F14c part has one closed, editable solid and three live
drivers. It lacks three independently selectable origin axes that the
intact FreeCAD source defines. Public export still refuses before output.
This slice of `B04-SW2026-FCSTD-BOX` belongs to `/root/assembly_frontier`
for PR #121. It extends the authenticated [intact-source planner](OriginalFcstdAttachedBoxOwners2026.md#intact-neutral-planning).

## Source ownership

`Body.Origin` selects App::Origin record 1777. Its ordered
`OriginFeatures` list owns three App::Line records followed by three
App::Plane records. The box itself selects the whole XZ plane. The
axis carriers are local X lines transformed by their own placements.
Their origin is `(0, 0, 0)` mm. All four origin and line model
visibility records are true on this exact archive.
[FreeCAD origin implementation](https://github.com/FreeCAD/FreeCAD/blob/0.21.2/src/App/Origin.cpp#L53-L78)
[Line view implementation](https://github.com/FreeCAD/FreeCAD/blob/0.21.2/src/Gui/ViewProviderLine.cpp#L49-L67)

| Role | Native object ID | Display label | Signed carrier |
| --- | --- | --- | --- |
| `X_Axis` | 1778 | `X-axis` | +X |
| `Y_Axis` | 1779 | `Y-axis` | +Y |
| `Z_Axis` | 1780 | `Z-axis` | +Z |

FreeCAD 0.21.2 placement restoration selects the axis-angle fields
when `A` is present. Its save writes the quaternion too. The scoped
projector validates agreement between both forms and computes the
actual native frame from axis-angle. A probe that changes only `A`
keeps the quaternion unchanged and correctly refuses. The original
contains no saved `GuiDocument.xml` and each App::Line owns placement,
role, label and visibility fields without an extent. The GUI provider
derives displayed length from the origin size and initializes the
origin provider hidden. The App visibility fields therefore do not
establish effective viewport visibility. The plan retains them as model
properties and leaves view extent and viewport state unqualified.
[Placement restore](https://github.com/FreeCAD/FreeCAD/blob/0.21.2/src/App/PropertyGeo.cpp#L774-L821)
[Origin view implementation](https://github.com/FreeCAD/FreeCAD/blob/0.21.2/src/Gui/ViewProviderOrigin.cpp#L44-L61)
[Derived display size](https://github.com/FreeCAD/FreeCAD/blob/0.21.2/src/Gui/ViewProviderOrigin.cpp#L137-L177)

## Transfer accounting

| Source field or owner | What the measured part establishes |
| --- | --- |
| Body, primitive, dimensions, support, transforms and constraints | Native reversed blind boss on its actual Top Plane, origin-coincident profile, three live named drivers, one matching B-rep and named Body. |
| Standard origin and principal planes | One actual native Origin and three canonical native planes with their checked frames. |
| Three separately addressable principal axes and model visibility | The plan now retains each typed axis owner, label, direction and stored flag. The measured target owns zero `moRefAxis_c` records and none of the three corresponding named history objects. |
| Body and primitive model visibility, summary and authored literal text | The source guards require the two model visibility flags true, reject unowned extra state and map the confirmed summary and document properties. Prior native proof establishes the physical body and literal property transfer. It does not establish full viewport parity. |
| Source archive, SHA verification binding, raw member offsets and native record numbers | These establish ancestry of the decoded original. Their original byte representation belongs to source evidence. Target identities come from the generated graph and should be reported with their source associations. |
| Three stored FreeCAD shape members | Their independently validated geometry agrees with the generated native solid. These are source boundary evidence, and their native FCStd bytes do not need to be copied to preserve their geometry. |

The current public result schema distinguishes native transfer from
reversible carrier transfer. Neither mode represents source envelope
attribution alone. Any future route needs truthful accounting for
retained source evidence and native semantics. It must keep the
existing refusal for uncovered functional owner roles and the exact
native artifact acceptance gate. The measured archive cannot qualify
the missing axes because a file with those owners has a different
feature graph and SHA. The existing two-plane hinge writer supplies a
finite, stock-derived Z-axis profile. That profile by itself does not
establish the ordinary XYZ origin-axis construction, order, size or
visibility rules.

## Guarded evidence

The host-only proof reopens the exact FreeCAD original, round-trips the
ordinary neutral document, joins the actual three axis IDs and runs the
shared composer. It reproduces the native-measured 10,189-byte file and
all 12 streams, with zero guarded runtime data-file reads. The published
native observation is unchanged. It compared edits at 27, 36.9 and 15 mm
across four native reopen snapshots in a healthy, eight-process batch.
[Prior native result](../measurements/2026/AttachedTopBoxGeneratedNative01.json)

The independent SDK projection retains an alternate model visibility and
custom axis label in a typed contrast. The actual intact plan rejects
that unverified edit. A duplicate owner ID, crossed role, malformed
visibility, contradictory rotation forms and coherent placement for the
wrong axis all refuse. The exact old shared build remains a geometry
and driver comparison. Its strict output reader confirms the missing
axes in the actual linked graph.

Inferred SDK export finds no writer. Explicit registry and direct adapter
path and stream calls report the actual native AdditiveBox. The ordinary
CLI stops at `CapturedObjects` before reading the passed measurement
path. These refusals preserve an existing path and stream without staged
entries. The result adds zero native observations and zero roster credit.
The task exit requires native generation and measurement of the three
selectable axes, model visibility and all prior editable body semantics,
followed by a closed public transfer report.
[Process evidence](../measurements/2026/AttachedBoxAxes01.json)

```sh
python3.14 -I -B re/tooling/sw2026/attached_top_box_source/VerifyAttachedBoxAxes.py \
  /path/to/recipe-0.21.2-F14c.FCStd /path/to/measured/F14c.SLDPRT \
  /tmp/AttachedBoxAxes01.json
```
