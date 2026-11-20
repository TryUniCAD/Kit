# Imported part warning survives authored ambient light

An explicitly authored ambient light clears load warning 32 in some
ordinary extrusion parts. The same constructor preserves warning 32 in all
four disclosed generated local-body parts. Each case exposes its actual
owned solid before and after rebuild, and all three controls pass.

Keep the imported part's zero-warning gate. Record the part and active
configuration update state independently of the local payload and environment.
[Imported part comparison](../../../../../../re/solidworks/measurements/2026/GeneratedLocalBodyPartAmbient01.json)
