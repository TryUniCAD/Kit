# Legacy bend-allowance scalar words do not count matrix entries

On SOLIDWORKS 2026 SP04.1, the mode-zero generation-19000 cover witness stores signed `+0x30` and `+0x34` values of 2003968329 and 0. The original provisional rule treated these words as array counts and refused a valid, otherwise aligned bend-allowance record at byte 17,775.

Read and retain the two words as signed members in this mode. The loader takes matrix loop bounds from separately allocated axes. Keep a refusal for any nonzero dynamic axis header until that content is understood. The cover and plate reproduce their complete embedded payloads with the separate guards. Both scalar meanings remain unresolved. [Loader and replay evidence](../../../../../re/solidworks/records/SheetMetalLegacyLinked2026.md)
