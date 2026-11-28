# Record the ordinary assembly tree and its serialized owners

The [native discovery tree receipt](../../../../../re/solidworks/measurements/2026/AssemblySyncTreeTopology03.json)
records 15 stable snapshots across the empty, single and repeated assemblies.
The empty case has 22 nodes, including the live-section folder and an empty
mate group. The component reference nodes enter immediately before the mate
group. The ordinary part's separate solid-body, surface-body and material
folders are absent from these assembly trees.

The [fixture manifest](../../../../../re/solidworks/v2026/corpus/assembly-synchronized/Manifest.json)
shows 41 common parent streams with two additional tessellation streams in
the populated cases. These native parents have no configuration Partition
stream. This is an observed inventory and does not identify every required
container stream or authorize omitting a stream in generated output.

The remote reader now reports the active configuration owner and options,
the ordered resolved roots and the relevant live-section and mate-group
fields so the logical graph can be compared separately from its visible
tree. The [remote projection](../../../../../re/solidworks/measurements/2026/AssemblyArchiveLayoutProcesses458.json)
finds the same 16 serialized roots in all three files, including the mate
group. The configured object list grows from one through three as ordinary
references are added, with unchanged active option values. No held-out
payload or private held-out observation was used.
