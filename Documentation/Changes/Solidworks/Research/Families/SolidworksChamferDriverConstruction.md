# SOLIDWORKS angle-distance chamfer driver construction

PR #121 adds bounded model-only construction for the two editable drivers of an ordinary single-edge angle-distance chamfer. The constructor uses the modeled rectangular stock edge, signed annotation frame, two driver values and explicit label intent. The shared serializer writes both live display graphs, and the typed reader recovers their distinct D1 and D2 parameter owners and view membership.

Two independently authored neutral models produced deterministic exact readback in four guarded processes. Four separate disclosed reads corroborated the measured frame and witness rules, including the D2 label branch transition. Construction is restricted to the proved first-exterior D2 display and leaves whole-feature emission and public eligibility closed.

[Driver construction, limits and reproduction](../../../../../re/solidworks/records/ChamferDriverConstruction2026.md)
