# A saved face texture can replace the face's legacy optics

On SOLIDWORKS 2026 build `34.4.1.1011`, a two-solid part stored distinct
part and left-body colors. The top face of that body was assigned both a
legacy color and the installed checker texture. A fresh read-only process
returned the checker texture on only that face. Its face-level legacy RGB
was white. All eleven untouched faces returned the nine-minus-one
sentinel and no texture. The right body's legacy getter returned null.

The reopened face texture reported scale `0.7300000190734863`, angle `0`
and `BlendColor=True`. The `CreateTexture` call requested scale `0.73`, angle
`0.31` and `BlendColor=False`. Record the saved getter values separately
from the requested inputs. The single observation does not establish how
SOLIDWORKS maps angle or blend settings.

Classical render appearances joined by native COM identity to the part
(`[5,0]`), left body (`[6,0]`), and left-body top face (`[8,0]`). The
face's renderer resource was `texture.p2m` and its texture filename pointed
to `checker pattern.p2m`. A strict SDK read at
`50b7466c3b922f56c632677d17ff43fd8c0d5031` found the measured part RGB
`(45,79,124)` in the leading Config-0 visual and no primary texture there.
The checker text appeared in other saved records. The SDK also projected
one body in both read modes where SOLIDWORKS measured two. The observed
owner identities cannot safely be attached to that neutral body.

The fresh process (`35564`) and both healthy stock controls exited. The
earlier authoring process wrote the file, then required owned-process
recovery before the closing stock control. The retained exact identities
are listed below. This is discovery evidence for the reopen and
ownership observations. A one-variable archive contrast and an
independently authored holdout are still needed.

| Retained record | SHA-256 |
| --- | --- |
| AppearanceContrast.SLDPRT | `515d70a73467b17bae1563cf7fa8c782d0ca64bc0925bb1eb2c66d21e4f4c5d5` |
| Read-only reopen result | `5671b11f3829779f27236775ea456ecf17943e811afa83fbadcc21f49cf5e3ee` |
| Read-only reopen bracket receipt | `aa56c4dfdd579c39ab720704f5924e8d591b220c1f49058b090eb0ffd1e9bff9` |

See [stored part appearance](../../../../Changes/Solidworks/Inspection/Parts/SolidworksStoredPartAppearance.md).
