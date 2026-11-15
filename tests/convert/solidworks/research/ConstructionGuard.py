from __future__ import annotations

from pathlib import Path as FilePath
from inspect import currentframe as ReadFrame


class BuildAudit:
    def __init__(self, SchemaDir: FilePath) -> None:
        super().__init__()
        self.SchemaDir = str(SchemaDir)
        self.Importing = True
        self.ModuleReads: list[str] = []
        self.DeniedReads: list[str] = []

    def BeginBuild(self) -> None:
        self.Importing = False

    def InspectEvent(self, EventName: str, ArgsValue: tuple[object, ...]) -> None:
        if EventName not in (
            "open",
            "os.listdir",
            "os.scandir",
            "subprocess.Popen",
            "os.system",
            "os.exec",
            "os.posix_spawn",
            "os.fork",
            "os.forkpty",
        ):
            return
        CurrentFrame = ReadFrame()
        if CurrentFrame is None or CurrentFrame.f_back is None:
            raise PermissionError("construction audit caller is unavailable")
        CallerFrame = CurrentFrame.f_back
        SourceName = CallerFrame.f_code.co_filename
        ImportLoader = SourceName == "<frozen importlib._bootstrap_external>"
        PathValue = str(ArgsValue[0])
        if self.Importing and EventName == "open" and ImportLoader:
            if CallerFrame.f_code.co_name == "get_data" and PathValue.endswith(
                (".py", ".pyc")
            ):
                self.ModuleReads.append(PathValue)
                return
        if self.Importing and EventName in ("os.listdir", "os.scandir"):
            if ImportLoader or PathValue in (
                self.SchemaDir,
                self.SchemaDir + "/__pycache__",
            ):
                self.ModuleReads.append(PathValue)
                return
        self.DeniedReads.append(PathValue)
        raise PermissionError("construction attempted runtime access: " + PathValue)
