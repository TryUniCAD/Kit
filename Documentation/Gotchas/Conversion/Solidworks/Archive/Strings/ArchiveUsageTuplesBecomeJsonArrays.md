# Archive usage tuples become JSON arrays

The string-framing process check writes an archive usage report to JSON before it starts a fresh verifier. Shared SDK usage records expose tuple fields such as used schemas and native byte fields. The JSON reader restores these fields as arrays, so direct Python comparison rejected equivalent reports.

Compare canonical JSON for the complete baseline. This keeps all field values and collection order in the check. [String framing verification](../../../../../Changes/Solidworks/Model/SolidworksStringArchiveProcesses.md)
