# A linear-pattern datum uses its own component occurrence

A local pattern's direction line references a plane wrapper. In both disclosed 2026 parts and each edit derivative, that plane wrapper owns a distinct `moUnitComponent_c`. Its owner is the actual inherited Config-0 part. The part's `f990` component is a separate object. The line's own `f60` is null. [Typed evidence](../../../../../../re/solidworks/records/LocalLinearPatternTypedArchive2026.md)

Follow the actual plane wrapper to recover the part and datum identities. When constructing a local datum reference, reuse the existing `CompRefFields` component allocation rule so the references retain their distinct vertices.
