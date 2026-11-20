from pathlib import Path as FilePath
import subprocess as ProcessLib
import sys as SystemLib

from tests.Convert.Formats.FusionHistoryTests import HistoryArchive
from tests.Convert.Runtime.IsolatedRuntime import KIsolatedRuntime
from tests.Convert.Runtime.RuntimeRules import KRootPath
from tests.Interchange.Fixtures.AssemblyFixture import BuildAssembly, BuildPiston


# isolated execution proves the built wheel cannot reach external runtime hooks
def RunIsolated(
    TmpPath: FilePath, InstallRoot: FilePath
) -> ProcessLib.CompletedProcess[str]:
    OutputFolder = TmpPath / "runtime"
    OutputFolder.mkdir()
    _ = (OutputFolder / "runtime-fusion.f3d").write_bytes(HistoryArchive())
    _ = (OutputFolder / "piston.json").write_text(
        BuildPiston().to_json(), encoding="utf-8"
    )
    _ = (OutputFolder / "assembly.json").write_text(
        BuildAssembly().to_json(), encoding="utf-8"
    )
    return ProcessLib.run(
        (
            SystemLib.executable,
            "-I",
            "-S",
            "-c",
            KIsolatedRuntime,
            str(InstallRoot),
            str(KRootPath),
            str(OutputFolder),
        ),
        cwd=TmpPath,
        check=False,
        capture_output=True,
        text=True,
    )
