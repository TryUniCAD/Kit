# Editable SOLIDWORKS full ellipse boss

The SOLIDWORKS writer generates a single free full ellipse and a forward blind
boss on the canonical origin Front Plane. It preserves the signed ellipse
orientation, the actual centre and semiaxes, the editable sketch and the
driving depth D1. The admitted document contains one ordinary millimetre
sketch, one Default configuration and one body.

Both public SDK writer paths reproduced the two disclosed native-tested
archives byte for byte with zero runtime input reads. Two pre-writer locked
native cases passed cold open, depth edit, save and fresh reopen in the
SOLIDWORKS 2026 SP05.2 oracle. The typed archive reader recovers and replays
the linked configuration and feature streams in the measured ellipse context.
[Public SDK evidence](../../../../re/solidworks/measurements/2026/SdkColdEllipsePublic01.json)
[Protected native evidence](../../../../re/solidworks/measurements/2026/EllipseColdSealedNative01.json)
