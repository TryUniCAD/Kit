# SOLIDWORKS assembly header aliases

The version-19000 direct header writer accepts the mapped schema-one
assembly root. Both codecs use the configuration owner catalog.
The action allocates distinct external header objects in map order
and writes zero bytes. Only the top-level model owns this action.
[Direct header writer](../../../../../src/convert/adapters/solidworks/Archive/Bodies/Writing/WriteDirectMut.py)

Two disclosed assembly prefixes establish the physical slots.
Two independent authored cases reproduce the order through separate
writer and reader processes. Their computed archive frames have
38 and 40 bytes. Existing part section and ghost control bytes match.
[Action evidence](../../../../../re/solidworks/records/AssemblyDirectAction2026.md)

The change covers one shared archive action. Complete configuration,
mate, and native assembly output require their own verification.
[Adapter reference](../../../../Reference/Adapters/Solidworks.md)
