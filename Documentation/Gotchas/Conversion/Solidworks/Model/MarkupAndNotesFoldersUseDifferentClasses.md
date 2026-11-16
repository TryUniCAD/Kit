# Markup and notes folders use different classes

## Expectation

Giving a `moNotesAreaFtrFolder_c` node the label `authored markups` supplies the
ordinary top-level markup folder in a new part.

## Actual behavior

The controlled 2026 recursive-tree measurements show a distinct
`InkMarkupFolder` node for `Markups`. Notes-area nodes are `NotesAreaFtrFolder`
children of `Annotations`. The generated part has those native children plus
the independently emitted extra top-level notes-area node. The native application
also creates the missing markup folder, at a different position in the tree.

The [recursive-tree receipt](../../../../../re/solidworks/measurements/2026/TreeNamesInspection01.json)
retains the generated observations. The already-unsealed independent camera
source API observations corroborate the native class/parent distinction. This
does not depend on inspecting an original held-out native CAD payload.

## Workaround

Model the markup folder and notes areas as separate native classes. Derive their
positions and ownership from the document graph. Changing a caption cannot change
a node's runtime class. Preserve the old experiment and obtain new independent
source inputs before qualifying the corrected topology.

The [new source protocol](../../../../Changes/Solidworks/Inspection/Cohorts/SolidworksTreePresentationSourceLock.md)
prepares those inputs. No correction or tree-parity acceptance is claimed yet.
