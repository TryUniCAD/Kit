# Computed prism geometry has no native Parasolid payload

A default strict geometry read can succeed without a stored native Parasolid cache for the bounded ordinary typed rectangle profile. The result contains a validated neutral `document.brep`; it still contains zero `brep_payloads`. The informational reconstruction diagnostic records this distinction and the actual input owners.

The initial F14a file contains no partition and loads correctly in SOLIDWORKS. Its saved derivative contains three native payloads. Both yield the same complete live driver/constraint/text representation; their depths differ because the saved derivative retains the measured 14 mm edit. The computed initial B-rep is derived from its 10 mm live depth and actual four-line contour.

Use `document.brep` when consuming the computed neutral topology. `extract_brep` exports stored native payload records and cannot supply absent source bytes. Do not attach the generic or current experimental generated partition merely to satisfy payload presence: the independently measured native attachment still opens with warning 32 and zero initial bodies. Cached, corrupt and unsupported inputs retain their existing reader behavior, and unsupported no-cache shapes still reject strictly.

`include_tessellation=True` does not synthesize a mesh on this part path. Changing it leaves the computed B-rep unchanged. The added B-rep capability and semantic fingerprint reflect the newly available neutral geometry and do not constitute new vendor acceptance flags.

[Scoped reader construction](../../../../../../re/solidworks/records/SdkNoCachePrismRead2026.md) · [Controlled source-only evidence](../../../../../../re/solidworks/measurements/2026/SdkNoCachePrismRead01.json)
