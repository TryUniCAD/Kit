# Verifying the saved geometry of edited extrusion depths

When native FreeCAD extrusion depths differ from an embedded polygonal profile, the inference run checks the feature's saved shape member. It builds two prism predictions from the same profile, frame, direction and reversal flags, varying only the two depth fields. The existing prism reader checks placed vertices, topology, faces and edge geometry against each prediction. The report confirms the edit only when the saved depths match and the embedded depths fail.

The single-input CLI records both pairs of signed end positions, both comparison results and the shape member hash in Input-native-edits.json. Forward, reversed and symmetric saves support this comparison. The report makes no claim about unrelated features, dependencies or subsequent editing in FreeCAD.

Five local single-input runs confirmed the saved prism and rejected the stale depth prediction. Signed end positions in millimetres were −5 and 14 for the forward front edit, −8 and 11 for the forward rear edit, −14 and 5 for the reversed front edit, −11 and 8 for the reversed rear edit, and −10 and 10 for the symmetric edit. All five still reported incomplete whole-file coverage.
