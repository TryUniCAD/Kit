# Conditional concentric orientation refresh

The [native knowledge supplement](../../../../../re/solidworks/records/ConcentricConditionalRefresh2026.md) binds the ordinary `f4c4=-1` concentric solver-map route to actual mate wrappers and a conditional cylinder getter. It distinguishes that route from misalignment-only cylinder-pair handling and records the exact readiness and persistence guards.

The concrete cylinder change check restores its world geometry caches after resolving the cylinder, but does not restore the separate optional orientation state. See [the specific side-effect gotcha](../../../../Gotchas/Conversion/Solidworks/Assembly/Mates/CylinderChangeCheckRetainsOrientationSideEffects.md).

[Exact numeric proof](../../../../../re/solidworks/records/ConcentricConditionalRefresh2026.json) covers 11 complete native functions or leaves, ten unwind fragments, 11 instruction windows, nine direct calls, three concrete RTTI tables and six virtual cells. Verification was static original-PE inspection only. No VM, CAD, COM, schema, codec or product test execution occurred. No source or writer implementation changed. Mandatory cold-open scheduling, downstream entity transport and native/held-out writer qualification remain open.
