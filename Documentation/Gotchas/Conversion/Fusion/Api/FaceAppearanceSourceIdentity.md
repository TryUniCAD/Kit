# Face appearance IDs can alias the inherited finish

In Fusion 2706.1.17 a copied appearance and the body's inherited finish
reported the same `Appearance.id`. After a primary-color assignment, only
the cuboid's positive-Z face changed from RGBA `[159, 159, 159, 255]` to
`[226, 29, 41, 255]`. The five other faces kept their original color and
material source. The selected face reported the changed color immediately
and after processing events. It reported `FaceAppearanceSource` (3).
The first two comparison attempts rejected the shared ID and the reported
source type, respectively. The latter attempt retained the full face
observations and an unqualified diagnostic save.

Match each face by outward normal and plane, then measure the primary
RGBA and source type before and after assignment. Keep the internal ID
as an observation. This verifies the intended face independently of
the appearance-ID alias. Inspect render and picking separately.

Diagnostic capture receipt SHA-256
`6dac92949a62f5111e642d48760a7ac5a67c005b4472976e7f07f01db877d7d5`.
Unqualified top-face archive SHA-256
`6e5b1f808c3961bba2d9d52fc78074712f41c6dc9ff2d45e2afea7b9a7473e3e`.

[Face appearance API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_BRepFace_appearance.htm)
· [Appearance source types](https://autodeskfusion360.github.io/FusionAPIReference/Fusion_API_Documentation/files/AppearanceSourceTypes.htm)
