# Read the cold chamfer before running legacy geometry discovery

A generated two-step chamfer file contains the stock sketch and an
extrusion, so the legacy rectangle reader attempts its usual setup.
On this profile it reads the packaged legacy `Config/RootLayout.json`
before the scoped typed decoder can resolve the feature. That happened
during the first guarded read of both disclosed archives.

Read the physical manager, configuration and ResolvedFeatures through
the chamfer layout immediately after native root discovery. The scoped
owner checks validate the actual stock, retained signed picks and each
dimension view before the analytic projection. Other profiles continue
through the existing refinements. The generated chamfer path consumes
only its supplied archive bytes.
[Guarded release proof](../../../../../re/solidworks/records/ChamferDistanceMain2026.md)
