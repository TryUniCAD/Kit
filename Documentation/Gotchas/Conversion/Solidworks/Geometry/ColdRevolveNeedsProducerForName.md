# Cold revolve naming needs the typed producer

A complete cold revolve has enough history to bind its one computed
solid to the actual creating feature. The generated archive has an
empty atom manager and no saved native body name. The read result
previously used the generic `Body 1` label because the geometry builder
omitted the producer object after checking the revolve.

Carry the validated revolve object into the existing derived-name
binding. The binding requires the same complete B-rep, the actual
final feature, a real design-body link and an agreeing printable ASCII
feature name. Its provenance describes the creator. Saved body names
still come from the actual body and its typed kernel attributes.
[Evidence](../../../../../re/solidworks/records/SdkColdRevolveNames2026.md)
