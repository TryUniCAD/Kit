# SOLIDWORKS 2026 principal-plane references

The part reader preserves the model-owned support plane of an ordinary sketch when a complete `19000` native handle appears within that sketch's resolved-feature record. It checks the archive plane ID, axis kind and basis against the decoded principal plane. Multiple complete candidates or an inconsistent basis raise a format error. Historical and unresolved-plane paths retain their existing behavior.

Use `open_document(path, include_brep=False)` to inspect the sketch's exact `support_plane_id` independently of the geometry cache. Independently authored SOLIDWORKS Top and Right fixtures resolved to plane IDs 3 and 4. Generated Front, Top and Right fixtures resolved to IDs 14, 15 and 16. Four older real part reader projections matched their previous hashes. [2026 handle record](../../../re/solidworks/records/PrincipalPlaneHandles2026.md) and [reader integration test](../../../tests/Convert/Solidworks/Core/Readers/SolidworksPrincipalTests.py).

The proven layout covers ordinary principal frames at the origin with a unit scale and the null optional reference. Other plane and transform layouts continue through their existing routes. [Creation-time field gotcha](../../Gotchas/Conversion/Solidworks/Model/PrincipalPlaneHandlesStoreCreationTimes.md).
