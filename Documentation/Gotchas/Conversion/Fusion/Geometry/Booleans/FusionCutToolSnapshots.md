# Fusion cut tool snapshots

A saved BRep snapshot in a modifying history need not be the final result body. The bounded two extrusion corner cut captures contain six cache bodies: a solid tool, a sketch sheet and a profile region for each extrusion. The final eight face cut result is in the journal state. Treating one six face cached stock as the final body loses the modifying feature.

Decode the journal states identified by the actual feature startModelHS and endModelHS. Validate cached solids independently against their own authored profiles and distances. Validate sheet roles separately. Sketch sheet coedges may have Partner equal to -1 even though their polygon boundary closes. This is an open sheet edge, not a permitted missing mate in a solid. Keep solid ownership and mate checks enabled.

Feature allocation can reserve two IDs while live faces use only the first active operation. Validate reciprocal allocation and the recipe or physical labels rather than assuming every allocation appears on final geometry.

[The corpus and recorded joins](../../../../../../re/Fusion/Reconstruction/BoundaryCuts/Findings.md) provide original, held out, opposite corner and pocket observations. This knowledge does not establish native writer or conversion acceptance.
