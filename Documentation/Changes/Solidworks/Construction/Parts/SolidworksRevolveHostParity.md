# Revolve reproduction across runtimes

The guarded replay compares a previously evaluated revolve against
its exact native-tested bytes using the frozen released neutral intent.
The pinned current Windows worker reproduced all ten streams.
The two writer revisions produced identical files on macOS. The
macOS and Windows configurations differ within one logical stream.

Use the pinned earlier packet and its exact Windows candidate as the
reference. Four guarded workers reconstructed and read the model with
zero runtime input accesses. This replay contributes no new held-out
qualification. [Method and receipt](../../../../../re/solidworks/records/SdkLockedRevolveEvaluation2026.md#reproduction-across-runtimes)
