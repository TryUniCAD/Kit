# SOLIDWORKS 2026 open-shell source lock

SOLIDWORKS authored three independent inward shells from rectangular Front
Plane stocks. Each source removes the stock's actual top planar cap. The
native history has a sketch, a blind stock extrusion, and an editable shell
thickness. This profile establishes the uniform inward, single opening case.

The [source receipt](../measurements/2026/OpenShellSourceLock01.json) records
the draft requests, original saves, and edited saves by SHA-256. Two requests
used independently sampled dimensions in disjoint intervals. The guest
created and hashed their requests before opening the application. Their
requests and six native phase records remain in Windows custody. The
macOS export includes only the disclosed request, its authored results, and
the receipt. The shell constructor and writer had no access to the sealed
case data.

## Native observation

| Evidence | Disclosed native result |
| --- | --- |
| Input stock width, depth and height | 53, 41 and 28 mm |
| Cap owner | One planar face of `ShellStockBoss` with z = 28 mm |
| Selection | Exactly one face, mark 1, with matching persistent reference |
| Feature type | `Shell` |
| Thickness driver | `D1@OpenShell`, driving and editable |
| Thickness before and after | 2.8 and 3.53 mm |
| Solid count | 1 in both states |
| Volume before and after | 18,559.408 and 22,690.287908 mm³ |
| Area before and after | 13,783.12 and 13,519.3272 mm² |
| Centroid z before and after | 10.810327743 and 11.032153046 mm |

If the outer dimensions are `w, d, h` and thickness is `t`, the inner
dimensions are `w-2t, d-2t, h-t`. The shell volume is outer volume minus
inner volume. The bottom, external walls, top rim, inner floor and inner
walls give area
`2 * (w*d + h*(w+d) + (h-t)*(w+d-4t))`. Subtract the mass moment of the
rectangular cavity, centered at `(h+t)/2`, from the outer prism's moment
about the sketch plane to obtain centroid z. The source passed these
comparisons both in its authoring process and in distinct fresh reopen
processes.

All three requests passed zero-error, zero-warning rebuild, actual
thickness edit, save, and new-process reopen. Two unchanged controls
bracketed nine candidate lifetimes. The oracle was SOLIDWORKS 2026 SP05.2
`sldworks.exe` 34.5.2.0604, x64 under Parallels Windows 11 ARM64, using
`SldWorks.Application.34`. The [disclosed phase comparison](../measurements/2026/OpenShellSourceDisclosed01.json)
preserves the native values and both controls.

## Linked archive fields

The [archive observation](../measurements/2026/OpenShellArchiveObservation01.json)
reproduces all fifteen modeled streams in each disclosed save. Both
Config-0 maps start at 4 and hand the actual object table at count 109
to ResolvedFeatures. ResolvedFeatures ends at count 313 with 20 roots.
The replay consumes every byte of each of those streams. It also records
the existing raw schema operations in Definition and the saved dimension
arrays. Generating those data from inputs remains separate work.

| Field | Observed role | Original and edited evidence |
| --- | --- | --- |
| `moShell_c.f828` | Input cap selection, with derived stock incidence | One actual `moCompFace_c`, four ordered side carriers, one end carrier with role 1 and terminal null. The component and all five carriers resolve to the prior stock. |
| `moShell_c.f818` | Input thickness and derived dimension display | A single `moDisplayDistanceDim_c` and `moFeatureDimHandle_c` carry the same `D1` before and after editing. The stored scalar and two display-vector x coordinates track the thickness. The display point is at the center of the selected cap. |
| `moShell_c.f820` | Observed inward mode value | Zero in both inward states. A direction contrast is still needed to classify outward behavior. |
| `moShell_c.f830`, `f838` | Observed empty optional lists | Each is a concrete `suObList` with count zero in this uniform case. Nonempty cases are unclassified. |
| `moShell_c.f848` | Auxiliary edge reference | A `moCompEdge_c` refers to the same historical stock and its role-0 end. The selected cap list contains only `f828`. |
| `moShell_c.f850` | Observed null optional body selector | Both saves omit this selector. |
| `moShell_c.f538` | Derived solved-body ownership | The same inherited atom 101 links prior feature 32 and result feature 34. The stock's single `f538` is null after the shell owns the atom. |
| Reference tags and body event | Changed during the edit | The cap and edge tags advance with the atom and shell event. Two snapshots establish the change without determining a generation rule. |

The stock and shell retain the same persistent identities across both
saves. The legacy SDK reads the correct driving `D1` but exposes two
face selections because it also reads the auxiliary `f848` edge as a
selected face. The one-cap native observation is the reader reference.

## Reproduction

Use [the pinned author](../../tooling/sw2026/shell_source/AuthorOpenShell.py)
and [the guest launcher](../../tooling/sw2026/shell_source/RunOpenShellSource.ps1).
The latter verifies `InspectFresh.py`, `OracleIdentity.py` and `Swapp.py` from
development revision `0167c3e33a045b82fb9ac17a5aa10560b2070ba8`. Place
those three utilities and the author in the shared packet, then run the
launcher through macOS `prlctl exec --current-user "Windows 11"`. Use
fresh guest tool and capture directories. The first attempt rejected the
stock before shell creation because its expected COM type was `Boss`.
The confirmed type is `Extrusion`.

The sealed files qualify as pre-writer source locks. Generated shell
output, held-out output acceptance, and historical corpus coverage are
still pending.

[SOLIDWORKS 2026 COM shell authoring example](https://help.solidworks.com/2026/english/api/sldworksapi/Create_Shell_Feature_Example_VBNET.htm)
