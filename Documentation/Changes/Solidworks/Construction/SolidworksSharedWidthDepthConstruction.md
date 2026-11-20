# Construct an anchored SOLIDWORKS boss with a local depth equation

The internal typed part constructor accepts one anchored Front Plane
rectangle with two driving sketch lengths and a derived blind-boss
depth. The explicit corner and dimension-presentation inputs accompany
the neutral document. The depth expression binds the actual width
parameter divided by two. The common part composer allocates the real
dimension handles before creating the two local equation wrappers and
writing Config-0 and ResolvedFeatures against one linked map.

The [guarded process proof](../../../../re/solidworks/measurements/2026/SharedWidthDepthConstruction01.json)
reproduces both disclosed model-generated containers with distinct
stream lengths and zero runtime input reads. One complete archive hash
matches the [previously measured native trial](../../../../re/solidworks/measurements/2026/WidthDepthSameLocatorNative01.json).
Both pass strict SDK readback with a solid and the actual dependency.
Six unsupported intents emit zero bytes. Public writer registration
and full native-source projection remain pending.
