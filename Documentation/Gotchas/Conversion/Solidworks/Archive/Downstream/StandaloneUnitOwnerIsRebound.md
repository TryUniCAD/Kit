# Standalone downstream unit owners are rebound on load

The runtime local self component has an actual model handle. Serializing that pointer as `moComponent_c.owner` appears natural but selects the wrong standalone graph.

In the exact 2026 ordinary standalone store path, the UI archive helper initializes filed-owner `+0x30` null. The selected component base writes a raw null object tag; the unit then writes `u8(0)`. The modern loader supplies the actual model through a different core helper and rebinds both component ownership and the runtime model handle. The helper lookup registry is separate from the CArchive object map.

Use the explicit standalone wire context and retain actual model ownership out of band. Preserve other condition, external-component and historical branches. Do not insert a whole model into this independent stream or infer a model map index from a runtime pointer.

The [source record](../../../../../../re/solidworks/records/DownstreamLocalOwnerContext2026.md) and [verification receipt](../../../../../../re/solidworks/measurements/2026/DownstreamLocalOwnerSource01.json) pin this rule. They do not establish native acceptance of a new downstream cache.
