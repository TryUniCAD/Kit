# Directory timestamps differ from the occurrence update time

An ordinary assembly occurrence stores the target model-header update
timestamp in `f3e8`. In both populated native discovery files, the
header's external file directory stores a different time in `f60` and
`f70`. Copying the occurrence time into the directory would have
produced different values in both files.

Derive each timestamp from its own lifecycle. The
[reopen trace](../../../../../../re/solidworks/records/AssemblyConstruction2026.md#directory-timestamps-and-occurrence-update-stamps)
shows the last-save refresh from the target configuration manager. It
does not close the complete initial-save rule.
