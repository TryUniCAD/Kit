# Construct the SOLIDWORKS 2026 assembly definition

The assembly research builder generates the document definition with the
assembly CLSID, shared presentation settings and fresh assembly settings.
The caller supplies the ten save-as-part preference values as explicit
inputs. The builder applies the recovered clamp and writes the settings
record without an archive object tag.

The [record map](../../../../../re/solidworks/records/AssemblyDefinition2026.md)
links the field order and effective values to the pinned 2026 constructors
and serializer. The process gate builds six streams in memory, reads back
the assembly class and authored journal, checks exact re-emission and
exercises values beyond both ends of the native clamp. The
[remote format job](https://github.com/TryUniCAD/Kit/actions/runs/44007621061/job/133786654820)
passed on `1325790cf`. This check does not establish native application
acceptance or enable output in the public adapter.
