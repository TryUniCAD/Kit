# Resource holds invalidate active leases

An application resource hold is not merely a pause of new dispatch. It can invalidate a running controller lease while the already submitted external native request continues.

During the 2026-11-23 desktop pause, SOLIDWORKS batch 008 completed on the PC after its local worker was interrupted. The controller retained its failed attempt. The checkpointed request identifier allowed retrieval and strict decoding of the original three artifacts without a second native request.

Drain active work before applying a hold when possible. After an interrupted local worker, inspect its submitted-request checkpoint and the external result before retrying. Preserve the original controller failure separately from a recovered native success. See [recovery evidence](../../../../re/NativePlacement2026/RecoveryEvidence.json).
