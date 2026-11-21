# Cylinder cache initialization skips orientation

The name `moAssembly_c::initRefWrapperCache` suggests it might refresh every active mate wrapper on open. In the pinned 2026 build it requires each wrapper's virtual `+0x140` predicate to return true before invoking update `+0x3b8`. The concrete cylinder predicate returns false. This function therefore cannot establish a cylinder's pre-solve refresh or orientation preservation.

The [bound native record](../../../../../../re/solidworks/records/ConcentricOrientationEnable2026.md) separately proves an explicit enable in the selected cylindrical face creation path. It also proves that the serializer reconstructs a present private state directly from wire presence and the loaded vector. These three lifecycle operations have different guards and owners.

Trace the actual cylinder geometry resolver/solver caller before claiming cold-open refresh. Preserve the loaded local orientation vector and actual state presence. Do not replace this gap with the world axis, a generic-cache assumption or an assertion that later updates are no-ops. No new native writer acceptance is established by this static finding.
