# Assembly dependency labels can omit the file extension

For the measured SOLIDWORKS 2026 SP05.2 assembly, `GetDocumentDependencies2`
returns the bare child display name in its first field and the full stored
locator, including `.SLDPRT`, in its second field. Requiring the filename
extension on both fields refused a valid, exact dependency while both native
controls passed.

Accept the documented display label for the first field. Establish file
ownership with the resolved second field, actual file identity and hash.
[Controlled authoring record](../../../../../re/solidworks/records/ConcentricDisplayOraclePlan2026.md)
