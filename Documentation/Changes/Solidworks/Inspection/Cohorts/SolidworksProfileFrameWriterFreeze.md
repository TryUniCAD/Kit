# Freeze the corrected writer before unseen frame predictions

The [corrected source inventory](../../../../../re/solidworks/v2026/heldout/FrameWriterFreeze.json)
binds 3,452 files to the exact writer commit tested in remote format CI. It
includes Git object identity, SHA-256 and length for all 3,154 source Python
files, research tools and helpers, test package initializers and the lock file.
It contains no vendor payloads or private reference measurements.

The [earlier source lock](../../../../../re/solidworks/v2026/heldout/FrameSourceLock.json)
reserved a Top-plane source and a Right-plane source before the correction.
The [discovery process receipt](../../../../../re/solidworks/measurements/2026/ProfileFrameDiscoveryProcesses6fc.json)
records the current transform check and the unchanged historical hashes for
eight previous sources. Those are regression results. New predictions will
use only the two public neutral requests and this writer snapshot. Detailed
native source observations stay sealed until the predictions are committed.
