# Zero opaque bytes is not generation

A typed field program with zero opaque bytes might appear to be generated from format rules.
The SOLIDWORKS programs under `src/convert/adapters/solidworks/programs/` have zero opaque bytes, but each is a recorded payload.
Each operation keeps the absolute offset and the value from one vendor save, and `ReplayResolved` rejects output whose length differs from that save.
A new sketch profile therefore needs another recording, and the values are donor data.

Before you report a program as generated, confirm that a different input can change its length and object count.
Confirm also that each value comes from the input, a rule, or a proven constant.
Run `tools/Donors/CheckReplays.py` to see the recorded payload debt.
See the [ratchet change entry](../../Changes/Solidworks/SolidworksRecordedPayloadRatchet.md).
