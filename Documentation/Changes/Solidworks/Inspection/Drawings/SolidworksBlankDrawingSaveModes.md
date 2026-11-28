# SOLIDWORKS blank drawing save-mode comparison

Run `InspectDrawingSaveModes.py` on a fresh staged blank-drawing pair
with the packet and observer hashes. The tool compares SaveAs before the
scale edit and Save3 after editing a disposable writable copy. It records
the saved bytes and validates each successful save in a fresh process.

In ten fresh SOLIDWORKS 2026 SP05.2 processes, both modes saved and reopened
the reduced native control. Both generated saves returned error 1. The
generated SaveAs target was empty and the in-place copy stayed identical.
The pristine bracketing controls also passed. This result covers the
disclosed blank drawing and leaves the held-out sources sealed.
[Command and evidence](../../../../../re/solidworks/records/DrawingSaveBoundary2026.md#save-modes)
