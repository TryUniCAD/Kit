# SOLIDWORKS configuration header handoff

The internal `ReadPartStart` reader takes an in-memory current part
archive. It loads the complete named `Contents/Config-0-ModelHeader`,
allocates the schema-one part root and checks the bounds of the first
section. It then inserts the header's original object identities at
the lightweight boundary. The result exposes the part's incoming map
and cursor position for further native body reads.

Six disclosed parts verify distinct header indices and section bounds
in fresh processes. Twelve malformed cases cover the named roles,
container format, part descriptor and section extent. An independently
authored format-4 pair verifies the self file and ordered directory
aliases and checks refusal of logical archive version 18900.
The version-order process counts typed decoder entries. The wrong
version reaches neither decoder, and the matching-version contrasts
exercise both counters.
Queue execution and complete physical configuration admission are pending.
[Source record and process commands](../../../../../re/solidworks/records/ConfigHeaderLinkSlice2026.md)
· [Header alias index gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Configuration/HeaderAliasesKeepSourceIndex.md)
