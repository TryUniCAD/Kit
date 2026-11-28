# History-only revolve reads can keep a generic body label

An ordinary generated square revolve read through the default geometry path names its body after the actual producer `OrdinaryBossRevolve`. With B-rep and tessellation disabled, the same file has the same final feature ID and a generic `Body 1` label. The history-only path does not run the geometry name reconstruction. [Cold producer name ownership](ColdRevolveNeedsProducerForName.md) · [Guarded square parity method](../../../../../re/solidworks/records/SquareRevolvePublicParity2026.md)

Compare the actual native body label through the default geometry path. In history-only readback, verify the body, its final feature and the live parameter and sketch owners.
