# SDK circle bosses on principal supports with editable end conditions

This is the disclosed SDK continuation of the [complete circle boss](SdkCircleBoss2026.md)
and the pinned [end-condition field analysis](EndConditionConstruction2026.md).
It composes a real fixed-centre analytic circle and ordinary solid boss
from the neutral model. Current qualification covers these four disclosed
designs and the stated native and SDK read scopes.

| Owner or field | Classification and rule |
| --- | --- |
| Principal support | Input frame and actual support ownership. Compare the full neutral basis and origin. Retain local sketch `u,v` and their normal in the native support frame. |
| `moEndSpec_c.f08` | Derived single-end flag. One for blind and mid-plane, zero for two independent blind ends. |
| `f0c, f10, f88` | First type zero for blind and six for mid-plane. The second type is zero in the bounded blind profile. The independent flip field stays constructor-zero. |
| `f8c` | Input reversal encoded as an integer; independent of the principal support and the single-end flag. |
| `f18, f20` | Actual independently allocated distance displays and parameters. `D2` uses its own neutral length when active. The inactive constructor slot has the primary depth. |
| `f140`, draft and reference caches | Ordinary sketch-plane start, disabled draft and empty end-reference state. A native save may emit two empty arrays. Their content establishes that they carry no references. |
| `f150, f154` | Constructor-zero in the tested ordinary profile. These remain distinct from the unresolved variable fields in other vendor save contexts. |
| Keyword dimension rows | Derived from the live driving dimensions in presentation units. A second boss row belongs only to the active second direction. |

For local circle centre `(cx,cy)`, radius `r`, tangents `u,v` and normal
`n`, the centroid is `cx*u+cy*v+n*z`. A symmetric mid-plane uses `z=0`
and its driving length as the total height. The two-direction height is
`D1+D2`, with signed midpoint `(D1-D2)/2` before reversal. The independent
oracle computes volume and area from the analytic cylinder and checks the
frame, actual driving states and parameter ownership after each edit.

The [disclosed measurement](../measurements/2026/SdkCircleEndConditions01.json)
binds the guarded 4,877-file writer closure and 4,962-file reader closure.
The four parts open with one solid before explicit rebuild. Twelve candidate
phases and two healthy bracketing controls pass in distinct SOLIDWORKS 2026
SP05.2 processes. All 530 numeric comparisons agree at six significant
figures. Both front-plane baseline files keep their earlier exact hashes.

The SDK reads the original generated artifacts, first native saves and
edited fresh reopens in twelve isolated processes. The reader resolves the
actual centre and radial driver directly when legacy markers do not bind
them. It preserves the source end mode and live `D1` and applicable `D2`
owners. All 24 typed Config and Resolved re-emissions match their source
bytes. The [empty-reference gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Resolved/EmptyEndReferencesCanBePresent.md)
records the native save distinction.

The original curve and end-condition source cohorts remain sealed at this
disclosed checkpoint. Further shape, support, end and document-level
qualification uses independently locked sources.
