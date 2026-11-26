from json import dumps as DumpJson
from os import environ as Environment
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# the snapshot research command must run in a fresh process with only the written request
def RunSnapBuild(Folder: FilePath, Title: str, Height: float) -> bytes:
    RootPath = FilePath(__file__).resolve().parents[5]
    Request = Folder / "Request.json"
    Target = Folder / "Cuboid.f3d"
    _ = Request.write_text(
        DumpJson(
            {
                "schema": 1,
                "title": Title,
                "dimensions_mm": {"width": 21.3, "depth": 33.2, "height": Height},
                "drivers": {
                    "width": "plateWidth",
                    "depth": "plateDepth",
                    "height": "padHeight",
                },
                "names": {"sketch": "Plate Profile", "extrude": "Pad", "body": "Plate"},
                "material": {
                    "label": "Plate Material",
                    "density_kg_m3": 1175,
                    "rgba": [0.25, 0.5, 0.75, 1],
                },
            }
        ),
        encoding="utf-8",
    )
    Driver = RootPath / "re/Fusion/GeneratedSnapshot/GenerateSnapshot.py"
    Result = RunProcess(
        [PythonExe, "-B", str(Driver), str(Request), str(Target)],
        env=dict(Environment, PYTHONPATH=str(RootPath / "src")),
        cwd=Folder,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr
    return Target.read_bytes()
