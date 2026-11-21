# The replay profile can change the complete carrier metadata

A strict reread of the exact 1.0.2 and 1.1.4 F14a archives adds `freecad.replay_sketch_profile=explicit-suppression` on the native document payload compared with the earlier neutral lock. These inputs have no sketches. Every source payload byte, the source verification digest and the rest of the neutral model still agree after the locator comparison. The new marker comes from the current replay digest owner. [Replay setter](../../../../src/convert/adapters/freecad/Replay/SetReplayDigest.py) · [Existing replay migration rule](LegacySketchReplayDigests.md)

Verify the original file, then compare the full neutral model under the pinned reader revision. Record the measured metadata delta when checking an older lock and keep the current profile on the actual model. [Intact source evidence](../../../../re/solidworks/records/FreecadF14aIntactSource2026.md)
