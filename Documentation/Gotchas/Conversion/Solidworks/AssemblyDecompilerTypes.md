# Assembly decompiler parameter types can name another class

An inferred first-parameter type in a native decompile can appear to identify the serialized class. In the SOLIDWORKS 2026 assembly dump, `sldmodu.dll!0x4c221a20` is shown with a `moMateGroup_c *` parameter, even though the 2026 serializer map assigns it to `moConfiguration_c` and `moDeformConfiguration_c`.

Using the inferred type would conflate an assembly configuration's config-object list and mass-cache tail with the actual mate-group serializer at `0x4b669f90`. The two records have different inheritance and counted sequences. Their native vtables also matter: configuration slot `0x4c0` points to concept resolved data, unlike the empty part-configuration dispatch used elsewhere.

Identify ownership from the RTTI/vtable serializer map, verify the relevant virtual slots in the matching PE binary, then follow both read and write paths. Parameter annotations remain aids to reading the pseudocode, not independent class-ownership evidence. The [assembly grammar finding](../../../../re/solidworks/records/AssemblyArchive2026.md) binds the addresses to the exact 2026 module hashes and records the resulting layout.
