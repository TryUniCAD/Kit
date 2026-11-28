import json as JsonLib
from os import environ as SystemEnv, pathsep as PathSeparator
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as KPythonPath
from typing import cast as CastValue

from convert import open_document as OpenDocument
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.Formats.Fusion.SegmentCodec.Features.Model.LocalRef import LocalRef
from interchange import CadDocument
from tests.Convert.Api.Fusion.SavedCuboid.ReadResave import (
    GetCatalog,
    ReadResave,
    ResavePath,
)


# a strict source projection must preserve the native observer order through persisted json
def TestResaveOrder() -> None:
    Payload = ReadResave()
    Model = ReadDocument(Payload)
    Table, Catalog, TableSlots = GetCatalog(Model)
    assert TableSlots == (1158, 1159, 1051, 1160, 1164, 1125, 1127)
    Subjects = Catalog.Frame.Subjects
    assert Subjects is not None
    assert tuple(Subject.Target for Subject in Subjects) == tuple(
        LocalRef(SlotIndex) for SlotIndex in (Table.ObjectId, *sorted(TableSlots))
    )
    assert all(Subject.ObserverIndex == 0 for Subject in Subjects)
    Document = OpenDocument(Payload, source_format="f3d", strict=True)
    assert not Document.diagnostics and not Document.brep_payloads
    assert Document.bodies[0].topology.volume == 11240.158203125
    Neutral = CadDocument.from_json(Document.to_json())
    assert Neutral == Document and Neutral.metadata["fusion.read_only"] is True
    Contract = CastValue(dict[str, object], Neutral.metadata["fusion.native_state"])
    assert Contract["version"] == 2
    assert DecodeState(Contract["model"]) == Model


# a fresh cli must independently emit the same complete document as strict sdk decoding
def TestResaveCli(TmpPath: FilePath) -> None:
    Repository = FilePath(__file__).resolve().parents[5]
    Source = ResavePath()
    Output = TmpPath / "Decoded.json"
    Result = RunProcess(
        (
            KPythonPath,
            "-B",
            "-m",
            "KitCli",
            "decode",
            str(Source),
            "--output",
            str(Output),
        ),
        cwd=TmpPath,
        env={
            **SystemEnv,
            "PYTHONPATH": PathSeparator.join(
                (str(Repository / "src"), str(Repository / "Cli"))
            ),
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    Record = JsonLib.loads(Output.read_bytes())
    assert Record["partial"] is False and Record["layer"] == "neutral"
    assert CadDocument.from_json(JsonLib.dumps(Record["document"])) == OpenDocument(
        Source, strict=True
    )
