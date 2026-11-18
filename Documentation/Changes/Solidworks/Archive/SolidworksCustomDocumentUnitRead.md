# Read custom mass units from SOLIDWORKS parts

The normal reader exposes the measured SOLIDWORKS 2026 custom unit choices
under `document.metadata["solidworks.typed_resolved_semantics"]["document_units"]`.
The mapping gives millimetres, degrees, grams or kilograms, cubic millimetres
and separate decimal counts for length, angle and mass. The read follows the
document's actual user unit table and requires its own nested density length
format. Presets and unqualified custom settings omit this optional report.

Seventeen separate processes verified strict path and byte reads of six
native-authored saves, eight generated or native-edited states and three
FreeCAD-derived parts. Six altered unit graphs omit the report while retaining
the same feature timeline and solid topology. [Read receipt](../../../../re/solidworks/measurements/2026/PublicDocumentUnitsRead01.json)
