# Empty assembly Definition renderers have their own profile

## Expectation

An empty renderer wrapper uses the same leading word for ordinary parts and
assemblies.

## Actual behavior

Eight disclosed SOLIDWORKS 2026 assembly saves store the empty renderer
wrapper with leading word 1, second word 0 and an empty object list. The
measured ordinary part controls use leading word 6. Fresh constructors leave
the wrapper absent when no rendering content is authored.
[Measured assembly and part boundaries](../../../../../../re/solidworks/records/OrdinaryAssemblyDefinition2026.md)

## Workaround

Select the concrete document class from its Definition CLSID and check the
matching empty-wrapper profile. Preserve the typed wrapper fields on
readback. Keep renderer presence and object count separate.
