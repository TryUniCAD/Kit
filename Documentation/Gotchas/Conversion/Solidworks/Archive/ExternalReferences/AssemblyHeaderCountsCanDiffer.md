# The two assembly headers can store different component counts

The empty native discovery file stores one in `Header2.fc4` and zero
in `Contents/Config-0-ModelHeader.fc4`. Both generated empty files
opened, rebuilt, saved and reopened with zero in both headers. The
populated discovery files instead store the same count in both headers.

Keep the fields tied to their owning header and context. The empty
observation does not prove a general rule to add one to either count.
See the [directory readback](../../../../../../re/solidworks/measurements/2026/AssemblyExternalDirectoryEA67.json)
and the [generated empty comparison](../../../../../../re/solidworks/measurements/2026/EmptyAssemblyNative01.json).
