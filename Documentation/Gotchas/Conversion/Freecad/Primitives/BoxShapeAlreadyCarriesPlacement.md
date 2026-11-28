# Box shape already carries placement

The exact disclosed translated and oblique `Part::Box` Shape members decode in world coordinates. Applying the object placement again would move every observed corner twice. The oblique fixture also stores a nonunit rotation-axis vector. Its direction becomes unit length after normalization, before the Rodrigues rotation or the existing axis-angle restore.

Read Placement as the authored input. Compute world corners from the typed dimensions and placement, and compare those predictions to the hash-pinned source Shape after ordinary OCCT decoding. Keep the source member as read-side evidence. [Translated and oblique source proof](../../../../../re/solidworks/records/SdkFreecadPlacedStock2026.md)
