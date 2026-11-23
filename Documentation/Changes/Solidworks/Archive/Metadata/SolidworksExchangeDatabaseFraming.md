# SOLIDWORKS exchange database framing

The shared writer computes the pager header, initial bucket map,
key hashes, cell sizes and free page space for the observed single
bucket layout. The reader recovers live records from assemblies whose
saved updates moved cells across the page. Twenty-four disclosed
databases and an independent UnQLite reader verify the physical format.
Twelve complete saved configuration-header databases reproduce exactly.

[Field rules and proof](../../../../../re/solidworks/records/UnqliteExchangeStore2026.md)
