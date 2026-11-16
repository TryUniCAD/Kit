# Feature-tree counts require matching traversal depth

## Expectation

Two native feature-tree snapshots can be compared directly to establish preserved names, node types and hierarchy.

## Actual behavior

The [end-condition held-out reference comparison](../../../../../re/solidworks/measurements/2026/EndHeldoutReference01.json) contains four native source trees with 25 recursively visited entries. Each has 19 top-level entries and six children: two annotation areas and four lights. The generated observer records only its top-level walk, with 20 entries. Subtracting 20 from 25 would therefore misidentify a count difference as five missing source features.

Filtering the source records by their explicit null parent establishes a real top-level difference: the generated tree includes one additional `NotesAreaFtrFolder`. The native design sketch and extrusion names/types agree, while declared authored system presentation names differ from native defaults. Both original observation arrays remain in the receipt; full hierarchy and presentation parity remain false.

## Workaround

Record node identity, name, type, parent and depth consistently in both observers. Compare equivalent traversal scopes before interpreting differences, and retain nested child observations before claiming a complete feature-tree round trip. A top-level-only result cannot establish that child features are missing or preserved. Healthy body/mass/dimension measurements remain a separate bounded result and do not substitute for tree parity.

The [prediction entry](../../../../Changes/Solidworks/Inspection/Extrusions/SolidworksEndConditionHeldoutPrediction.md) links the frozen writer, native measurements and remaining acceptance limits.
