# Complete SDK circle boss construction

The internal SDK constructs an ordinary fixed-centre circle and forward blind
boss from a neutral document. The proven candidate scope is one circle, one
sketch, one Front Plane at the origin, one part body, one active configuration
and separately editable sketch and boss D1 parameters. The public writer is
qualified separately for its line-loop scope.

| Field or relationship | Classification and rule |
| --- | --- |
| Circle centre, radius and driver | Neutral sketch geometry in explicit document units. The radius or diameter relation references the actual full-circle entity and the owned driving parameter. |
| Centre and seam points | Input centre and derived seam at `(cx+r,cy)`. Seam allocation precedes centre allocation. The sketch point array stores centre then seam. |
| Closure, arc and orientation | The actual arc references the same seam point twice and the distinct centre. Compact indices come from the owning point array. The ordinary circle uses positive sketch orientation. |
| Origin frame and support | Shared profile construction registers the actual principal plane, local frame and allocated native feature. |
| Centre fix | One actual logical relation targets the centre. Its handle and the centre's relation-use count derive from that reference. The seam is free of extra constraints. |
| Radial value | The parameter length is the distance from centre to seam, doubled for diameter. It is checked against the neutral parameter value. The radial object targets the actual arc, and its allocated identity is distinct from the later boss and depth identities. |
| Display | The actual sketch value, owner, radial subtype, style and text node belong to one radial display. With no neutral annotation point, the ordinary text point is placed at `(cx+2r,cy+r)` and transformed by the profile frame. Leader direction, distance, radius offset and display cache are computed. |
| Feature and body | The standard boss composition uses the actual circle profile parent and the independent depth parameter. The generated file leaves the body cache absent, and the native initial query finds its solid. |
| File and attributes | The shared part recipe constructs all ten streams and the file container. Keywords contain separately owned sketch and boss D1 rows in the document presentation units. |

The [circle geometry record](CircleSketchSynthesis2026.md) and
[radial style and engine record](RadialStyleAndEngine2026.md) give the pinned
loader, constructor and style rules. The [preference ledger](SdkDefaultPartRecipe2026.md)
distinguishes the document density preference from the effective density of an
unassigned solid body.

## Process and native checks

`SdkCircleProof.py` constructs from neutral input in a fresh guarded process.
A second process decodes all ten streams, checks the actual geometry and
parameter owners against the neutral request, then re-emits the streams and
complete container byte for byte. The two output lengths are 8,403 and 8,421
bytes. Both pairs of processes deny runtime input-file reads and reach the
archive through SDK modules. Six malformed inputs per design reject.

The immutable [native receipt](../measurements/2026/SdkCircleNative01.json)
binds the 4,867-file source closure, both neutral requests and generated
files, observer tools, application build, six candidate phases and two
controls. The stored standalone self paths were absent in the VM. Both files
open with one solid body, 19 top-level rows, and an active sketch and boss before
an explicit rebuild. Each radial edit retains the original centre and each depth edit
keeps its own parameter owner. Reopen preserves both edits.

| Disclosed shape | Native sketch D1 | Native boss D1 |
| --- | --- | --- |
| Radius alpha | 8.725 → 10.775375 mm | 12.475 → 10.915625 mm |
| Diameter beta | 22.95 → 19.16325 mm | 17.825 → 21.122625 mm |

All 230 checks agree with the analytic cylinder predictions to six significant
figures. For profile radius `r` and forward depth `d`, volume is `πr²d`, area
is `2πr(r+d)`, and the centre of mass is `(cx,cy,d/2)`. The native API
reports effective unassigned-body density of 1 kg/m³ and document preference
of 1,000 kg/m³ at initial load, after edit and at fresh reopens. Both controls
remain healthy, all original files remain immutable, and the VM postflight
shows unchanged license processes and no remaining SOLIDWORKS instance.

This disclosed trial leaves original-source parity, held-out results, other
support frames, other end conditions and the public circle writer open.
