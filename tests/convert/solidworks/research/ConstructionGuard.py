from __future__ import annotations

from pathlib import Path as FilePath
from sys import _getframe as GetFrame


class BuildAudit:
    def __init__(SelfValue, SchemaDir: FilePath) -> None:
        SelfValue.SchemaDir = str(SchemaDir)
        SelfValue.Importing = True
        SelfValue.ModuleReads: list[str] = []
        SelfValue.DeniedReads: list[str] = []

    def BeginBuild(SelfValue) -> None:
        SelfValue.Importing = False

    def InspectEvent(
        SelfValue, EventName: str, ArgsValue: tuple[object, ...]
    ) -> None:
        if EventName not in ("open", "os.listdir", "os.scandir", "subprocess.Popen"):
            return
        CallerFrame = GetFrame(1)
        SourceName = CallerFrame.f_code.co_filename
        ImportLoader = SourceName == "<frozen importlib._bootstrap_external>"
        PathValue = str(ArgsValue[0])
        if SelfValue.Importing and EventName == "open" and ImportLoader:
            if CallerFrame.f_code.co_name == "get_data" and PathValue.endswith(
                (".py", ".pyc")
            ):
                SelfValue.ModuleReads.append(PathValue)
                return
        if SelfValue.Importing and EventName in ("os.listdir", "os.scandir"):
            if ImportLoader or PathValue == SelfValue.SchemaDir:
                SelfValue.ModuleReads.append(PathValue)
                return
        SelfValue.DeniedReads.append(PathValue)
        raise PermissionError("construction attempted runtime access: " + PathValue)
