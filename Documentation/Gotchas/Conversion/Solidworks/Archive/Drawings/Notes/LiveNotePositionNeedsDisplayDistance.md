# Live note position needs the display distance

The generic text record retains an explicit point. An ordinary plain note uses its display anchor, direction, distance and frame to return the live position through the annotation and note APIs. A generated note can preserve the text record and load without warnings while the live position remains at the anchor.

Use the actual display attachment location and compute the direction and distance from the authored point in the active frame. Four disclosed original and edited sheet notes reproduce their intended points from these owners. The independent generated name experiment confirmed that publishing the name and display identity still left the missing distance visible as a zero live point. [Field measurements](../../../../../../../re/solidworks/measurements/2026/FreshPlainDrawingNotePositionFields01.json) · [Native identity result](../../../../../../../re/solidworks/measurements/2026/FreshPlainDrawingNoteIdentityNative01.json)
