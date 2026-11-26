# Missing P03 Parasolid data can still refuse analytic fallback

A generated archive with no recognized Parasolid payload might appear eligible for the SOLIDWORKS reader's analytic no-cache route. The exact 32-member P03 candidate contains no recognized partition but has 19 members outside the pinned reader's narrow archive-member allowlist. That reader refuses default strict opening with `SLDPRT contains no readable Parasolid payload`. Strict design-only still returns the sketch and Boss without B-rep.

Retain the default refusal and the explicit design-only result separately. Use the complete saved member inventory when diagnosing the no-cache predicate. It also checks archive version and uniqueness. Keep the existing predicate and typed ownership guards in place until the additional members and derived geometry are understood. [Exact readback findings](../../../../Changes/Research/Encoder/ConstrainedBossSdkReadback.md)
