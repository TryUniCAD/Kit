# Child directory times come from two different archive objects

The normal external-reference walk updates the directory's modification
timestamp from the child's own `moExtObject_c.f60` through its model
header. If the self object is missing, the getter samples the current
Unix time.

The directory's last-save timestamp comes from the child's runtime
configuration manager. SOLIDWORKS 2026 loads that value from the
`dmConfigMgrHeader_c.f60` record in `Contents/CMgrHdr2`. The occurrence
update timestamp still comes from the child's model header `f48`.

Use the generated self record and the generated configuration-manager
header as separate owners of the two directory fields. The
[native traces](../../../../../../re/solidworks/records/AssemblyConstruction2026.md#child-directory-timestamp-sources)
give the loader calls and the missing-self fallback.
