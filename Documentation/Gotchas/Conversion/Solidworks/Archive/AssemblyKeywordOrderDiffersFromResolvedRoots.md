# The assembly keyword index has a separate feature order

An empty assembly has 16 roots in the resolved-feature archive. The native
keyword index also includes entries for lights, exploded views and nested
annotation nodes, and orders them differently. A repeated inserted part adds
a separate `Reference` element for each occurrence, even though the
occurrences resolve to the same document.

This is the observed shape in the three
[ordinary discovery assemblies](../../../../../re/solidworks/v2026/corpus/assembly-synchronized/Manifest.json).
Do not project the resolved root order onto this index. Its feature and
occurrence projection needs a separate construction rule. The reduced empty
assembly experiment omits the index. Two generated empty assemblies
[passed the native comparison](../../../../../re/solidworks/measurements/2026/EmptyAssemblyNative01.json)
with that omission and 31 other absent streams; this does not establish
the keyword index's behavior for populated assemblies.
