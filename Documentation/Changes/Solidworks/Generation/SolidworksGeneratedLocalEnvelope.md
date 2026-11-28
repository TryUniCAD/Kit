# SOLIDWORKS generated local body envelope

`EncodeLocalBody` builds the feature-owned LocalBodies group from a
printable Unicode feature storage key and ordered typed Parasolid nodes.
It generates the single-body count, key and record lengths from those
inputs. The input is the typed topology.

Six generated envelopes matched an independent encoder byte for byte,
including a Unicode key at the extended length boundary. The SDK reader
recovered every key from the generated group. Five unqualified inputs were
refused. The four earlier native-accepted containers and all 48 streams
were unchanged when the part composer switched to the shared writer.
Construction recorded zero runtime input reads.
[Generated envelope receipt](../../../../re/solidworks/measurements/2026/SdkGeneratedLocalEnvelope01.json)
