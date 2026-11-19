# Observe raw Parasolid bodies in SOLIDWORKS

The [kernel probe](../../../../../re/tooling/sw2026/imported_body_source/ObserveKernelBodyRestore.py)
measures the versioned COM path from a raw Parasolid stream to a temporary
body and a native BaseBody feature. Native body Save-to-Restore controls
and a pristine part open bracket the run. The packet declares the file
hash, topology, vertex coordinates and mass properties of each supplied
body. The observer uses a fresh exact-build process for each lane.

This probe measures kernel reception and attachment through COM. Native
writer and archive acceptance require their own cold open, save and
fresh-reopen procedures. The first kernel observation is pending.
