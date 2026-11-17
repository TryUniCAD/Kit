# SOLIDWORKS rectangular Parasolid partition research

The 2026 research tools now walk the active Parasolid graph and rollback
history of an ordinary rectangular boss. Run `para.CompareRectangle`
with the independent prism bounds and the disclosed source files to
check topology, attribute ownership, model atom and partition-mark
attachment, rollback references and full stream identity. The research
tracking helpers accept body and face
tags, an update counter and an explicit time to construct the related
model-owned attributes.

An offline comparison reproduced both payloads and the complete
compressed bytes for E0, L1, C1a, C1b, P0 and the A13/A14 children.
The emitter opened zero files during those comparisons. All six
populated native wire graphs matched the independent dimensions, area,
volume and centre. This result covers the disclosed rectangular graph
and linear rollback shape. Fresh populated cache construction and native
load qualification remain open.
[Wire records, source hashes and command](../../../../../re/solidworks/records/PopulatedPrismPartition2026.md)
