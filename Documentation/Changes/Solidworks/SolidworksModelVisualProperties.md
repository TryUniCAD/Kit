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

The complete-file process checks inspect serialized model appearance and
ownership after decoding. Remote job `132812541055` passed 149 policy checks,
163 native checks and 158 existing skips. The independently generated replacement
now opens and rebuilds without errors or warnings between two healthy controls
on build `34.5.2.0604`; both locked inputs remain unchanged.

The [native report](../../../re/solidworks/measurements/2026/FreshPartModelAppearance.json)
also shows that the sketch and extrusion remain suppressed and no body exists.
This repairs the specific opening fault; generated-output acceptance remains
zero. Production SOLIDWORKS writing remains disabled.
