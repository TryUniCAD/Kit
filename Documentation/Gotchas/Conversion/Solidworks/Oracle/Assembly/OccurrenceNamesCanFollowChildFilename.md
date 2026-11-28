# Occurrence display names can follow the child file

The neutral assembly explicitly named its two instances Cylinder-1 and Cylinder-2. The generated file carried the distinct occurrences and both resolved to the intended generated child. SOLIDWORKS exposed their names as NeutralCylinderAlphaDerived-1 and NeutralCylinderAlphaDerived-2, using the child file's basename. This happened both before and after a successful explicit rebuild.

Compare the authored names with the actual Component2.Name2 values before checking mate endpoints. The two new names identify resolved occurrences, but a valid path or matching transform does not establish source name preservation. Keep the source name check active while identifying the persisted override. [Controlled diagnostic](../../../../../../re/solidworks/records/ConcentricOpenDiagnostic2026.md)
