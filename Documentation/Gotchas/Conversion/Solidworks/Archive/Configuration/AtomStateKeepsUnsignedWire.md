# Atom state keeps its unsigned wire word

The ordinary atom archive stores its state as an unsigned 32-bit word.
For words above one, the native read projects zero to runtime unless
archive condition `0x80` is set. Keep the original word and the runtime
projection separately.

The stored condition also affects the presence of the later stamp
words through the separate `0x400000` rule. Read those fields in the
owning archive context and keep their positions independent of state
normalization.

[Bounded atom evidence](../../../../../../re/solidworks/records/ConfigAtomSlice2026.md)
