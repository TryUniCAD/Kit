# Read the ordinary SOLIDWORKS imported base-body layout

The shared typed archive admits schema-one `moBaseBody_c` for the measured
SOLIDWORKS 2026 SP05.2 ordinary part context. It retains the source CString,
signed local-body selector, local storage CString and ordered segment-mesh
IDs. The parser and emitter refuse other storage branches.

The [layout record](../../../../re/solidworks/records/ImportedBaseBodyTypedLayout2026.md)
describes the native field ownership and replay command. Two independent
offline processes each reproduced all five linked streams in four
disclosed originals with the production tables and no runtime file reads.
The [receipt](../../../../re/solidworks/measurements/2026/ImportedBaseBodyTypedReplay01.json)
records the exact source hashes and refusal controls. Native imported-body
construction and public writer acceptance remain open.
