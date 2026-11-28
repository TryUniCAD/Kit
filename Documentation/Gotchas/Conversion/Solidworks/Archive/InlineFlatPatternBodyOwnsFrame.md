# The inline flat-pattern body uses a separate native archive frame

The disclosed SOLIDWORKS 2026 SP04.1 cover stores a present flat-pattern body even though its mode-zero plate contrast omits that body. The loader reads a signed extent and kernel selector before the native compressed chain. Starting a body decoder at the presence field or giving it the compressed packet leaves the geometry unresolved.

Bound the packet with the native helper's extent, verify the kernel-zero wrapper and exact chain end, then inflate and read the typed geometry before resuming the enclosing feature. This consumes the cover's entire linked stream. The typed geometry encoder generates a different kernel representation and frame length. Keep exact store gated until the native representation can be synthesized. [Loader and replay evidence](../../../../../re/solidworks/records/SheetMetalLegacyLinked2026.md#typed-flat-pattern-cache-read)
