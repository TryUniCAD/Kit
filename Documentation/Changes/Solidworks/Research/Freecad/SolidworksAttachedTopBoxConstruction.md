# Generate an attached Top-plane box for SOLIDWORKS

The research worker accepts a neutral FreeCAD AdditiveBox with a whole-plane XZ attachment, zero offset and the corresponding quarter-turn placement. The opt-in `attached_top` request uses the existing [FreeCAD box process](../../../../../re/tooling/sw2026/SdkFreecadBoxProcess.py). With `preserve_source_labels` enabled, the generated part keeps the source body name and the three named driving dimensions.

The shared construction uses the actual Top Plane, two positive sketch dimensions anchored at the origin and a reversed blind boss. The world bounds follow from the three source lengths. The original support identity and attachment mode are retained in the file properties.

The [source measurements](../../../../../re/solidworks/measurements/2026/AttachedTopBoxSourcesNative01.json) establish the native frame, constraint ownership and editable direction. They lock two independently authored holdouts before this implementation. The generated profile is restricted to the measured attachment and remains a research route pending target and held-out qualification.
