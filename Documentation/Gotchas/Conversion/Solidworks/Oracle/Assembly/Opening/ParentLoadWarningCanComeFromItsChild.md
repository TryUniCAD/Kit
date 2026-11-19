# Parent load warning can come from its child

An assembly returned warning 32 in `OpenDoc6` even though the active mate and body geometry measured correctly. Two controlled opens used a byte-identical generated parent at the same path. Replacing its generated child with the version that contains its authored ambient light changed the parent's warning from 32 to 0. Both controls passed and both assemblies rebuilt with two solids and the same concentric mate.

Check the actual loaded child and vary its suspected state while holding the parent bytes and paths fixed. In this case the warning cleared while authored occurrence names still failed their own check. [Native comparison](../../../../../../../re/solidworks/measurements/2026/ConcentricParentAmbientNative01.json)
