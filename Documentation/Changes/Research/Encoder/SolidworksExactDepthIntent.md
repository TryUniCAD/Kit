# SOLIDWORKS exact saved depth intent

The research encoder can transfer the exact saved value of a verified blind-boss D1 into a matching authored geometry request. The prepared JSON records the driving parameter and the linked extrusion length in metres. The surrounding document and sketch remain in millimetres. The source archive hash and body observations stay in a separate evidence file.

Run `ExactDepthIntent.py prepare` with a pinned reader checkout, a disclosed authoring record and the matching authored geometry JSON. Run `ExactDepthIntent.py replay` in a fresh process with the prepared JSON, explicit locator and write epoch. [Commands and scope](../../../../re/solidworks/records/VendorBlindBossExactDepth.md)

The replay preserved all three native depth words, including two one-ULP differences from their nominal millimetre literals. Strict SDK readback retained the driving parameters and one solid with the expected ordered sketches and directed faces. The bridge qualifies this depth transfer for the disclosed cases. Vendor source admission and native acceptance retain their separate requirements. [Offline proof](../../../../re/solidworks/measurements/2026/VendorBlindBossExactDepth.json)
