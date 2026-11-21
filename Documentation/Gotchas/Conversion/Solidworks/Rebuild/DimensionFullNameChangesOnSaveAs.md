# Dimension full names change on Save As

SOLIDWORKS exposes an editable part driver as `D1@FeatureName@DocumentName.Part`. A Save As changes the document segment on the next open even if the same feature still owns the driver and its value and parents are unchanged.

Check the complete name against the expected document name for each phase. Compare the driver, feature, value and parent links across phases after checking that document segment. Comparing the first and last full name directly flagged both passed cases in the controlled 2026 revolve selection run. [Raw outcome](../../../../../re/solidworks/measurements/2026/SelectedRevolveCutSelectorNative01.json) · [Phase-bound audit](../../../../../re/solidworks/measurements/2026/SelectedRevolveCutSelectorSavedOwner01.json)
