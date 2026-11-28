# Identify explicit part body and driver names in SOLIDWORKS archives

Two unrelated native rectangular designs preserve explicitly named bodies
and all three editable driver names through SOLIDWORKS 2026 SP05.2 save,
reopen and an independent depth edit. Six processes pass with healthy
controls. All four baseline and named partitions round-trip byte for byte
with typed kind-84 character values. The persisted body label belongs to
`SDL/TYSA_NAME`. The three driver names belong to their actual length
parameter holders.

This change extends research decoding of the observed ASCII character
values and preserves the native evidence. Public write support for these
names requires separate qualification.

[Native archive record](../../../../../re/solidworks/records/PartDriverAndBodyNames2026.md)
[Hash-bound receipt](../../../../../re/solidworks/measurements/2026/SdkPartNamingArchive01.json)
