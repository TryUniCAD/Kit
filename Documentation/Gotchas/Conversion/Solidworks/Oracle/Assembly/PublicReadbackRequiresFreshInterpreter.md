# Public readback requires a fresh interpreter

The public SOLIDWORKS readback checks all imported Python modules for CAD runtime dependencies. Closing the native CAD application leaves the observer's COM modules loaded in the Python interpreter. Calling the public read helper directly from that interpreter can therefore reject a cleanly saved assembly.

The first ordinary planar registry batch recorded a clean native reopen and matching analytics, followed by the exact error `ValueError('public native read imported a CAD runtime dependency')`. Keep that first result. Run the existing strict reader entry in a fresh isolated Python subprocess, verify the saved file hashes and require the empty CAD import list. Also verify the original native record, controls and process identities separately. [Measured recovery](../../../../../../re/solidworks/records/SdkPlanarRegistryReadbackRecovery2026.md)
