# Comparing embedded and saved extrusion depths

After the public FreeCAD reader refuses an inconsistent inline edit, the research CLI compares the embedded model's emitted depth fields with the actual saved extrusion. It matches typed extrusion objects by unique Kit identity and checks each changed depth against its live parameter owner, expression and spreadsheet target. Input-native-edits.json retains original and current distances in millimetres, the expression and the cell in its authored unit. A refusal or missing dependency leaves the evidence incomplete.

Local native inspection recovered both forward edits from 11 to 14 mm, both rear edits from 5 to 8 mm and the symmetric total thickness from 16 to 20 mm. Each saved expression resolved to one spreadsheet cell. This evidence identifies edited inputs; cached solids, downstream geometry and complete graph reconciliation still require independent verification.
