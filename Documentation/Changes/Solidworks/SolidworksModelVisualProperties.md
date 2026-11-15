# Generate the model's owned visual properties

The shared research model constructor now creates its owned visual-properties
record and mandatory embedded material from SOLIDWORKS 2026 constructor rules.
It applies the native part constructor's default-appearance flag after the
generic visual constructor.
It previously inherited the general concept's null optional appearance, which
reached a native visual copy constructor as a null source during initial update.

`re/tooling/sw2026/builders/Visual.py` supplies fresh records without reading a
saved file. The active registry's explicit presence flags describe constructor-null
texture and shader children. Field order, constants and derived empty collections
are documented in the [visual construction record](../../../re/solidworks/records/VisualConstruction2026.md).

The existing complete-file process checks now inspect serialized model appearance
and ownership after decoding. They run in remote PR CI only. The prior fault is
captured with a healthy control; remote construction and native remeasurement of
this revision remain pending. Production SOLIDWORKS writing remains disabled.
