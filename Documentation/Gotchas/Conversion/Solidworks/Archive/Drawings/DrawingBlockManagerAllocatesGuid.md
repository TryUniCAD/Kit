# Drawing block managers allocate their own GUID

The empty sketch-block manager has a 16-byte identity even when all its maps are empty. The three disclosed drawings share that value because they were created from one native template. Repeated bytes across those sources can look like a schema constant.

The fresh SOLIDWORKS 2026 constructor calls `CoCreateGuid` on that member. Allocate a new UUID4 for a fresh drawing's block manager and emit its Windows little-endian wire fields. [Pinned constructor and archive evidence](../../../../../../re/solidworks/records/DrawingEmptyManagers2026.md)
