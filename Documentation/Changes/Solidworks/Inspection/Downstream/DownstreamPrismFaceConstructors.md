# SOLIDWORKS prism face constructor graphs

The [research projection](../../../../../re/solidworks/records/DownstreamPrismFaceConstructors2026.md) constructs typed face rows from the generated part's actual configuration, output body atom, sketch and linked kernel faces. It retains the six inline slots and initial role map for each face of an ordinary rectangular boss.

Run `downstream.CheckPrismFaceConstructors` with either of the two variants in the record. Four fresh guarded processes preserve the eleven generated part streams and produce byte-identical readback for twelve distinct face rows. The projection stops at construction. Native validation, the remaining cache collections and the complete linked drawing lifecycle remain open.
