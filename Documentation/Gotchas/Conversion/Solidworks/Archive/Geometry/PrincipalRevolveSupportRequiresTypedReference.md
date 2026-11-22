# Principal revolve support requires a typed reference

The keyword-level sketch can report provisional support even when the
resolved sketch selects a different canonical plane. For the ordinary cold
principal revolve, the typed profile's `pd_f78` owns a
`moCompRefPlane_c` object. Its `ff0.f00` identifies the resolved datum,
`f100` agrees with that datum's canonical axis and `f58` belongs to
the active part. The profile's `pd_ff0` transform must agree with the
actual plane.

The typed reader publishes the linked datum as `plane-reference` only
after those checks. This lets ordinary source-support validation
inspect the resolved owner when republishing a measured readback. A
missing or contradicted reference keeps the strict reader closed.
[Measured reader and publication evidence](../../../../../../re/solidworks/records/MeasuredPrincipalRevolvePublication2026.md)
