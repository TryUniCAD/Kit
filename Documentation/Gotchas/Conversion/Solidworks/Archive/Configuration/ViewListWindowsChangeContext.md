# View list windows change archive context

The ordinary schema-one view reads two optional lists while `ctx87c`
is set. That state changes at field boundaries even when both lists
are absent. Entering with `ctx3d0` also sets condition bit `0x200`
for the two windows and clears it before the trailing view fields.

Keep those changes in the archive context and leave the view's wire
position untouched. A cleared condition bit leaves unrelated bits in
place. The stored list flags still consume their signed words.

[Native boundaries and authored state contrast](../../../../../../re/solidworks/records/ConfigViewSlice2026.md)
