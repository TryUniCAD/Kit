from __future__ import annotations

SCHEMA = "kit.sw2026.drawing-cache-trial.v1"
CONTROL = "D00EmptySheet"
NATIVE_NAME = CONTROL + ".SLDDRW"
CASES = (
    ("Pristine", None),
    ("Repacked", None),
    ("OmitDisplayLists", "Contents/DisplayLists"),
    ("OmitViewBucketLists", "Contents/VBLists"),
    ("OmitDisplayStamp", "_DL_VERSION_19000/DLUpdateStamp"),
    ("OmitSheetPreviewNames", "SheetPreviews/SheetNames"),
)
TOOL_NAMES = ("DrawingCacheCases.py", "InspectDrawingCache.py", "AuthorDrawingSources.py", "AuthorCurves.py", "OracleIdentity.py", "Swapp.py")


def input_file(root, name):
    return root / "Inputs" / name / NATIVE_NAME
