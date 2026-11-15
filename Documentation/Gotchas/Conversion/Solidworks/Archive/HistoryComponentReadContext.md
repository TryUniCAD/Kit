# Component history mutates read context without a wire flag

A history item can change archive state around a nested object without adding a serialized field. SOLIDWORKS 2026 `moHistoryCompItemData_c` at `sldmodu.dll!0x4b645080` first calls node-base helper `0x4b645260`, then handles its chain-component pointer at `+0x48`.

The writer emits that pointer directly. The reader, for versions after `0x17e5`, sets archive context member `+0x8a0` to 1 before reading the pointer and clears it to 0 afterward. Do not read or write an extra flag, apply the mutation on the writer, or replace the node base with a concept child list. Raw vtable slots confirm node lightweight `0x4c17adf0` and fieldless resolved `0x4b27e120`.

The archive schema models a read-side context scope and a typed chain-component pointer. [Remote job 132725623286](https://github.com/TryUniCAD/Kit/actions/runs/43685701362/job/132725623286) first exposed the unregistered history class after CMgr alignment was repaired. The [assembly finding](../../../../../re/solidworks/records/AssemblyArchive2026.md) records module ownership, native operands, and the pending reproduction of this additional grammar.
