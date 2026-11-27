# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import sys
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from pathlib import Path


def CheckReadback(request):
    source = Path(request["source"]).resolve(strict=True)
    before = source.read_bytes()
    digest = sha256(before).hexdigest()
    assert digest == request["sha256"], "native fixture hash changed"
    forbidden = []

    def guard(event, arguments):
        blocked = event.startswith("socket.") or event in {
            "subprocess.Popen",
            "os.system",
            "os.posix_spawn",
            "os.exec",
        }
        if event == "import" and arguments:
            module = str(arguments[0]).split(".")[0].casefold()
            blocked = blocked or module in {
                "freecad",
                "freecadgui",
                "part",
                "sketcher",
                "win32com",
                "pythoncom",
            }
        if blocked:
            forbidden.append(event)
            raise RuntimeError(
                "offline native readback attempted a forbidden operation"
            )

    sys.addaudithook(guard)
    from convert.adapters.freecad.Adapter import FreeCadAdapterA
    from convert.adapters.freecad.Archive import ExtractManifest
    from convert.api.ApiOpen import OpenDocument
    from convert.api.ApiWrite import WriteDocument

    inline = request["mode"] in {"inline", "refused"}
    try:
        manifest = ExtractManifest(before)
    except ValueError as problem:
        assert not inline
        assert str(problem) == "FCStd archive has no embedded Kit interchange document"
    else:
        assert inline and manifest
    observations = []
    for strict in (True, False):
        try:
            document = OpenDocument(
                source, SourceFormat="freecad.fcstd", StrictMode=strict
            )
        except FreeCadAdapterA as problem:
            assert request["mode"] == "refused", str(problem)
            assert (
                "inline native controls require unsupported edit reconciliation"
                in str(problem)
            )
            observations.append({"strict": strict, "status": "refused"})
            continue
        assert (
            request["mode"] != "refused"
        ), "saved edit returned a stale inline snapshot"
        parameters = {parameter.id: parameter for parameter in document.parameters}
        for expected in request["parameters"]:
            parameter = parameters[expected["id"]]
            assert parameter.value.value == expected["value"]
            assert parameter.value.unit == expected["unit"]
            assert parameter.owner_id == expected["owner"]
            if "expression" in expected:
                assert parameter.expression is not None
                assert parameter.expression.source == expected["expression"]
                assert parameter.expression.parameter_ids == tuple(expected["targets"])
        result = {"strict": strict, "status": "read", "parameters": len(parameters)}
        if not inline:
            output = BytesIO()
            written = WriteDocument(
                document, output, DestFormat="freecad.fcstd", AllowCarrier=True
            )
            assert written.metadata["mode"] == "exact_native_roundtrip"
            assert output.getvalue() == before
            result["replay_identical"] = True
        observations.append(result)
    assert source.read_bytes() == before, "public readback changed source evidence"
    assert not forbidden
    return {
        "sha256": digest,
        "source_unchanged": True,
        "forbidden_attempts": forbidden,
        "observations": observations,
        "native_qualification": "not_established",
    }


if __name__ == "__main__":
    print(dumps(CheckReadback(loads(sys.argv[1])), sort_keys=True))
