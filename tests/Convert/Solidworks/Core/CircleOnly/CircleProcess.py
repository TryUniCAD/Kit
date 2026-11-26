# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as DumpRecord
from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook, argv as ArgValues

# guarded execution must identify source fixture roots without importing any research helper
KRepoRoot = FilePath(__file__).resolve().parents[5]


# a production read and neutral replay must never invoke an oracle or recover a research fixture
def BlockOracle(EventName: str, EventArgs: tuple[object, ...]) -> None:
    if EventName in {
        "subprocess.Popen",
        "os.system",
        "socket.connect",
        "socket.bind",
        "ctypes.dlopen",
    }:
        raise RuntimeError(f"forbidden production operation {EventName}")
    if EventName == "import" and str(EventArgs[0]).split(".")[0] in {
        "adsk",
        "FreeCAD",
        "Part",
        "win32com",
        "pythoncom",
    }:
        raise RuntimeError("forbidden CAD application import")
    if EventName != "open" or not isinstance(EventArgs[0], str):
        return
    Opened = FilePath(EventArgs[0]).resolve()
    try:
        Relative = Opened.relative_to(KRepoRoot)
    except ValueError:
        return
    if Relative.parts and Relative.parts[0] in {"re", "tests", "examples"}:
        raise RuntimeError("production execution attempted a research fixture read")


# separate processes prove that the serialized model no longer needs its original source path
def RunCircleProof() -> None:
    AddAuditHook(BlockOracle)
    from convert.api.ApiOpen import OpenDocument
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.serialization.JsonCodec import DumpJson, LoadJson

    if ArgValues[1] == "read":
        Document = OpenDocument(FilePath("Source.SLDPRT"), IncludeBrep=False, IncludeTess=False)
        _ = FilePath("Model.json").write_text(DumpJson(Document), encoding="utf-8")
    elif ArgValues[1] == "replay":
        Decoded = LoadJson(FilePath("Model.json").read_text(encoding="utf-8"))
        assert isinstance(Decoded, CadDocument)
        Document = Decoded
    else:
        raise ValueError("unknown circle proof operation")
    Document.assert_valid()
    (SketchValue,) = Document.sketches
    print(
        DumpRecord(
            {
                "bodies": len(Document.bodies),
                "entities": [str(Value.kind) for Value in SketchValue.entities],
                "constraints": [Value.kind for Value in SketchValue.constraints],
                "support": SketchValue.support_plane_id,
                "guarded": True,
            }
        )
    )


if __name__ == "__main__":
    RunCircleProof()
