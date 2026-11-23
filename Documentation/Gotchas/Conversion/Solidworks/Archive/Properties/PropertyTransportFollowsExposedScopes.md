# Assembly property relationships follow exposed scopes

The ordinary SOLIDWORKS 2026 package declares the root application,
core and custom property targets. It stores configuration properties
and auxiliary XML separately, without a root relationship for every
XML member. The relationship row order differs from the numeric ID
order.

Generate type declarations and root relationships from the actual
supported property scope. Resolve every root target against its
emitted member. Keep application metadata separate from its root
relationship ID and from general assembly component references.
[Typed comparison and transport evidence](../../../../../../re/solidworks/records/ConcentricD01PropertyTransport2026.md)
