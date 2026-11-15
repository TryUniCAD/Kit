# A valid pointer can identify the wrong object

Expected behavior: the first argument of the sketch-related function at model
address `0x4c5195d0` identifies `sgSketch`.

Observed behavior: the decompiled function takes a solver wrapper. It reads the
actual sketch pointer from wrapper `+0x8`. Reading sketch offsets directly from
the wrapper succeeded as memory access but returned unrelated values. The first
retained-control trace therefore cannot establish sketch state from those two
events. Its direct sketch-serialization events remain separate observations.

Workaround: recover the exact native signature and wrapper indirection before
interpreting memory fields. The corrected hook reads wrapper `+0x8` and records
both object identity and the wrapper. A successful read is not type evidence.
The [Tupni ledger](../../../../../re/solidworks/records/Tupni2026.md) records the
affected capture and the correction. A subsequent capture must verify it.
