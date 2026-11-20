# A thread Boolean retains its signed wire word

The ordinary thread reference manager's `f1a0` runtime Boolean comes
from a signed 32-bit wire word. Native load treats every nonzero word
as true. The typed read keeps the original under `f1a0#wire` and the
normalized value under `f1a0`.

For a concrete manager, read the map before reading the word. An
absent manager consumes the nullable object tag and carries no
Boolean field. Keep both values of the concrete record for typed
wire inspection. [Exact serializer and fixture evidence](../../../../../../re/solidworks/records/ConfigThreadMarkSlice2026.md)
