# Internal SOLIDWORKS nested bundle publication

The internal `WriteNestedAsm` path uses the Kit registry transaction to
publish one requested assembly and all owned sibling part and assembly
definitions. The caller supplies the logical Windows assembly destination
on other hosts. The writer validates the complete sibling set and active
configuration before generating bytes.

The staged host checks reproduced all seven files across two disclosed
hierarchies and verified rollback on both a denied publish and a concurrently
created last companion. Usability and loadability remain unmeasured on this
route. Default writer selection and existing flat profiles retain their
current behavior.
[Usage](../../../../Reference/Adapters/SolidworksAssemblyCompiler.md) ·
[Process evidence](../../../../../re/solidworks/records/SdkNestedAssemblyPublication2026.md)
