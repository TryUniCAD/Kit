# Native compute can pause in an informational dialog

A dispatched Fusion Python call can stop advancing while the process remains responsive and nearly idle. In the mesh-shell control, `Design.computeAll()` entered `MeshGeometryInterface::hollow`, polled `QTApplication::canceled`, then synchronously displayed a personal-offering information dialog through `RestrictionsWelcomeDialogTimer::showDialog` and `QDialog::exec`. This was not a failed persistence decode or a completed computation.

The observed dialog was titled “About Your Fusion Documents” and explained editable-document limits. Clicking its existing “Ok. Got it.” button allowed the same call to continue. No subscription, entitlement, editable-document state or access setting was changed. Both source/reconstructed mesh candidates subsequently passed native rebuild, edit, save and reopen.

When a native call stalls, preserve its checkpoint and inspect the live stack and actual dialog before retrying the script or terminating the application. A timeout alone does not identify a malformed file. [The bounded runtime evidence](../../../../../re/Fusion/LocalOracle/ParaMesh/RuntimeDialog.json) records the sample digest, relevant call path, observed dialog and action; [native acceptance](../../../../../re/Fusion/LocalOracle/ParaMesh/NativeAcceptance.json) records the completed result.
