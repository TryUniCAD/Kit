# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe


# independent processes expose archive imports and serialization across the actual command boundary
def RunVisualCase(Program: str, Payload: object) -> CompletedProcess[str]:
    RootPath = FilePath(__file__).resolve().parents[4]
    return RunProcess(
        [PythonExe, "-B", "-c", Program],
        cwd=RootPath,
        input=EncodeJson(Payload),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )


# the codec must construct arbitrary authored ownership without consulting historical native input
KCodecModel = r"""
import json
import sys
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "re/solidworks/WriterResearch"))
from CmgrVisualPrefix import CmgrVisualFields, RequireVisualFields
from VisualState.VisualStateArchive import EncodeVisualState
from VisualState.VisualStateModel import CanonicalState, VisualDisplay, VisualOwner, VisualState
from VisualState.VisualStateReadback import DecodeVisualState
from convert.adapters.solidworks.Container.Archive import ArchiveError

case = json.load(sys.stdin)
material = CmgrVisualFields(0x325476, 0x102030, 0xABCDEF, "Steel", case["appearance"],
    0xA0B0C0, r"<SystemTexture>\graphics\materials\color.p2m", 3, 0.001, 0.001, True, True)
display = VisualDisplay(case["visible"], 6, 1, 0)
owners = [VisualOwner(None, None, material, display)]
owners.extend(VisualOwner(index + 61, 1800000000 + index, None,
    replace(display, Visible=(index % 2 == 0) if case["mixed"] else case["visible"]))
    for index in range(case["features"]))
state = VisualState(7, case["representation"], case["name"], tuple(owners))
"""


# malformed owners and unsupported fields exercise the encoder refusal contract from a separate process
KCodecRefusals = r"""
action = case.get("invalid")
if action == "duplicate": state = replace(state, Owners=state.Owners + (state.Owners[1],))
if action == "holder": state = replace(state, Owners=state.Owners + (state.Owners[0],))
if action == "visibility": state = replace(state, Owners=(replace(state.Owners[0], Display=replace(display, Visible=1)), *state.Owners[1:]))
if action == "display": state = replace(state, Owners=(replace(state.Owners[0], Display=replace(display, DisplayMode=2)), *state.Owners[1:]))
if action == "locator": state = replace(state, Owners=(replace(state.Owners[0], Material=replace(material, NativeAssetPath=r"<SystemTexture>\..\materials\color.p2m")), *state.Owners[1:]))
if action == "clock": state = replace(state, Owners=(state.Owners[0], replace(state.Owners[1], Created=1 << 32), *state.Owners[2:]))
if action == "zero": state = replace(state, RepresentationId=0)
"""


# full readback must verify the primitive appearance and ordinary caller compatibility as well as pointers
KCodecReadback = r"""
try:
    payload = EncodeVisualState(19000, state)
    if action == "truncated": payload = payload[:-1]
    if action == "trailing": payload += b"x"
    decoded = DecodeVisualState(payload, 19000)
    assert decoded == CanonicalState(state)
    assert EncodeVisualState(19000, decoded) == payload
    assert decoded.Owners[0].Material.SurfaceColor == 0x325476
    assert decoded.Owners[0].Material.MaterialColor == 0xA0B0C0
except ArchiveError as error:
    assert action is not None, str(error)
    print(json.dumps({"rejected": action}))
else:
    assert action is None, f"accepted invalid case {action}"
    try:
        RequireVisualFields(19000, material)
    except ArchiveError:
        pass
    else:
        raise AssertionError("ordinary cmgr must refuse the system token without context")
    print(json.dumps({"bytes": len(payload), "sha256": sha256(payload).hexdigest(),
        "appearance": decoded.Owners[0].Material.AppearanceId, "name": decoded.Name,
        "representation": decoded.RepresentationId, "owners": len(decoded.Owners)}))
"""


# semantic process stages keep independently authored inputs separate from refusal injection and readback proof
KCodecProgram = KCodecModel + KCodecRefusals + KCodecReadback


# source access and native automation must remain impossible during independent candidate generation
KSourceFreeProgram = r"""
import json
import runpy
import sys
from pathlib import Path
context, settings, candidate = json.load(sys.stdin)
def deny_source(event, args):
    if event == "subprocess.Popen":
        raise RuntimeError("native or source subprocess access is forbidden")
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = str(args[0]).lower()
        if path.endswith((".sldprt", ".prtdot", ".sldasm", ".slddrw")) and not args[2] & 0x41:
            raise RuntimeError("native input access is forbidden")
sys.addaudithook(deny_source)
import io
sys.stdin = io.StringIO(json.dumps(context))
sys.argv = ["VerifyVisualState.py", "--fixture-context", "-", "--visual-state", json.dumps(settings)]
if candidate is not None:
    sys.argv.extend(["--candidate", candidate])
runpy.run_path(str(Path.cwd() / "re/solidworks/WriterResearch/VisualState/VerifyVisualState.py"), run_name="__main__")
"""
