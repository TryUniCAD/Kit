# Exact SOLIDWORKS saved circle readback

The ordinary version-19000 reader keeps the live diameter and depth on a
saved forward Front-plane blind circle boss. It follows the actual sketch,
fixed center, datum, creating feature and two driving dimension handles.
The separate inactive second-end length remains visible in the boss step's
`solidworks.inactive_blind_depth` attribute. The attribute retains its
typed owner and value in metres. The active extrusion still has one depth
driver.

Strict reads with B-rep verify the saved cylinder and both cap stations
against the linked model. The partition's shell must own the same live body
atom as the boss and configuration. The reader keeps the original topology
and uses those checked dimensions for body measurements. A permissive read
can retain raw physical geometry after a mismatch. Its body remains
unassociated with the boss and has no attributed measurements. Use
`include_brep=False` when only the editable history is needed.

Three archived native saves retain their exact live dimension words and match
their measured body volume, area and centroid. Nine complete manager,
configuration and resolved stream replays compare byte-for-byte. A crossed
producer and an unchanged partition paired with edited features both fail
the applicable checks. For the physical mismatch control, both stored
logical atom claims agree with one another and differ from the raw shell.

Other saved modes remain outside this typed route. Publication still
requires an exact independently measured archive.

[Verification and boundaries](../../../../../re/solidworks/records/SdkSavedCircleMainRead2026.md)
