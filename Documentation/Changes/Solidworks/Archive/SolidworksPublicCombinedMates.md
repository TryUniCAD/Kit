# Read ordered groups of planar assembly mates

The normal SOLIDWORKS 2026 assembly reader now decodes complete ordered
lists of ordinary aligned coincident, parallel and positive driving distance
mates. The supported profile uses one configuration and resolved direct part
occurrences. Each endpoint follows its native occurrence and child datum.

Wrapper IDs belong to the containing assembly. Endpoint order restarts for
each mate. The reader validates bounds against the actual wrapper allocator,
rejects duplicates across the list, and verifies that mate and distance
dimension IDs do not collide with other persistent owners. The previous
single-mate profile keeps its existing neutral IDs and metadata.

Real process checks cover generated groups of two and three mates and a
physically malformed group with a reused wrapper ID. The new projection also
reads the independently native-authored disclosed assembly and two generated
candidates with complete endpoints. All three retain exact MatesList
round-trip bytes. The [receipt](../../../../re/solidworks/measurements/2026/PublicCombinedMates01.json)
records each archive map and allocator relationship.
