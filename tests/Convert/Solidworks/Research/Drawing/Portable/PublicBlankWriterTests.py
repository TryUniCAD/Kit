import json
from hashlib import sha256 as HashBytes
from math import isclose as IsClose, ulp as FloatStep
from os import environ as SystemEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExec

from convert import open_document as OpenDoc
from convert.adapters.solidworks.Container.Container import SldprtArchive


# each guarded write uses an ordinary public call in a new interpreter and verifies actual committed bytes
def TestBlankWriter(TmpPath: FilePath) -> None:
    RootPath = FilePath(__file__).resolve().parents[6]
    Runner = RootPath / "re/tooling/sw2026/blank_eval/BuildPublicBlankDrawing.py"
    OptionsPath = TmpPath / "Options.json"
    _ = OptionsPath.write_text(
        json.dumps(
            {
                "schema": "kit.sw2026.public-blank-options.v1",
                "allow_carrier": False,
                "overwrite": False,
                "validate": True,
                "values": {
                    "require_native_transfers": True,
                    "require_self_contained": True,
                },
            }
        ),
        encoding="utf-8",
    )
    DefinitionSizes: set[int] = set()
    for Index, (Route, SheetName, Height, Ratio) in enumerate(
        (
            ("extension", "Shop sheet", 8.5 * 0.0254, (13, 7)),
            ("solidworks.slddrw", "Shop sheet for the second edition", 0.2159, (4, 9)),
        )
    ):
        SourcePath = TmpPath / f"Intent{Index}.json"
        TargetPath = (TmpPath / f"Blank{Index}.SLDDRW").resolve()
        ReportPath = TmpPath / f"Run{Index}.json"
        _ = SourcePath.write_text(
            json.dumps(
                {
                    "schema": "kit.sw2026.public-blank-neutral-intent.v1",
                    "sheet_id": "sheet-1",
                    "sheet_name": SheetName,
                    "width_m": 11 * 0.0254,
                    "height_m": Height,
                    "scale_ratio": Ratio,
                }
            ),
            encoding="utf-8",
        )
        Process = RunProcess(
            [
                PythonExec,
                "-B",
                str(Runner),
                "--intent",
                str(SourcePath),
                "--intent-sha256",
                HashBytes(SourcePath.read_bytes()).hexdigest(),
                "--options",
                str(OptionsPath),
                "--options-sha256",
                HashBytes(OptionsPath.read_bytes()).hexdigest(),
                "--target",
                str(TargetPath),
                "--report",
                str(ReportPath),
                "--route",
                Route,
                "--epoch",
                "1795090000",
                "--block-id",
                "0608cda7-6c94-490c-9caa-ad3fcaebfb8d",
                "--writer-manifest-sha256",
                HashBytes(Runner.read_bytes()).hexdigest(),
            ],
            cwd=RootPath,
            env={**SystemEnv, "PYTHONPATH": str(RootPath / "src")},
            timeout=45,
            capture_output=True,
            text=True,
        )
        assert Process.returncode == 0, Process.stderr
        Report = json.loads(ReportPath.read_bytes())
        Payload = TargetPath.read_bytes()
        assert Report["output"]["sha256"] == HashBytes(Payload).hexdigest()
        assert Report["atomic_write_verified"] and Report["no_overwrite_verified"]
        assert Report["data_file_reads"] == Report["cad_runtime_calls"] == 0
        assert Report["dropped"] == []
        Archive = SldprtArchive.from_bytes(Payload)
        assert len(Archive.streams) == 7
        DefinitionSizes.add(len(Archive.require("Contents/Definition")))
        Drawing = OpenDoc(TargetPath, strict=False).DrawingValue
        assert Drawing is not None and not Drawing.ModelRefs
        (Sheet,) = Drawing.Sheets
        assert Drawing.ActiveSheetId == Sheet.EntityId and not Sheet.Views
        assert (Sheet.EntityName, Sheet.SheetWidth, Sheet.ScaleRatio) == (
            SheetName,
            11 * 0.0254,
            Ratio,
        )
        assert IsClose(Sheet.SheetHeight, Height, rel_tol=0, abs_tol=FloatStep(Height))
    assert len(DefinitionSizes) == 2
