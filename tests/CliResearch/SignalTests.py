from pathlib import Path as FilePath
from signal import SIGINT, SIGTERM
from subprocess import PIPE as KPipe, Popen as StartProcess
from sys import executable as KPythonPath, platform as KPlatform
from time import sleep as WaitSeconds

from pytest import mark as TestMark


# direct launcher signals must reach the selected sdk process without losing cleanup or exit status
@TestMark.skipif(KPlatform == "win32", reason="POSIX research signal propagation")
@TestMark.parametrize(
    "SignalNumber,HandleSignal,ExpectedCode",
    ((SIGTERM, True, 37), (SIGINT, True, 37), (SIGTERM, False, -SIGTERM)),
)
def CheckSignal(
    SignalNumber: int, HandleSignal: bool, ExpectedCode: int, TmpPath: FilePath
) -> None:
    RootPath = TmpPath / "Checkout"
    (RootPath / ".git").mkdir(parents=True)
    SdkPath = RootPath / "src/convert"
    SdkPath.mkdir(parents=True)
    _ = (SdkPath / "__init__.py").write_text(
        "\n# the child must identify its own selected checkout sdk\n"
        'KIdentity = "selected research sdk"\n'
    )
    ToolPath = RootPath / "re/automation/Controller.py"
    ToolPath.parent.mkdir(parents=True)
    _ = ToolPath.write_text(
        """from pathlib import Path
from signal import SIGINT, SIGTERM, signal
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from convert import KIdentity

# interrupted research must finish cleanup before the launcher reports completion
def Finish(Number, Frame):
    Path(sys.argv[2]).write_text("cleaned")
    raise SystemExit(37)
if sys.argv[3] == "handled":
    signal(SIGINT, Finish)
    signal(SIGTERM, Finish)
Path(sys.argv[1]).write_text(KIdentity)
while True:
    time.sleep(0.01)
""",
        encoding="utf-8",
    )
    ReadyPath = TmpPath / "Ready"
    DonePath = TmpPath / "Done"
    with StartProcess(
        (
            KPythonPath,
            "-I",
            "-m",
            "KitCli",
            "research",
            "--root",
            str(RootPath),
            "controller",
            str(ReadyPath),
            str(DonePath),
            "handled" if HandleSignal else "default",
        ),
        cwd=TmpPath,
        stdout=KPipe,
        stderr=KPipe,
        text=True,
    ) as Launcher:
        try:
            for _ in range(3000):
                if ReadyPath.exists() or Launcher.poll() is not None:
                    break
                WaitSeconds(0.01)
            assert ReadyPath.read_text() == "selected research sdk"
            Launcher.send_signal(SignalNumber)
            _, ErrorText = Launcher.communicate(timeout=60)
            assert Launcher.returncode == ExpectedCode, ErrorText
            assert DonePath.exists() is HandleSignal
            if HandleSignal:
                assert DonePath.read_text() == "cleaned"
        finally:
            if Launcher.poll() is None:
                Launcher.terminate()
            _ = Launcher.wait(timeout=30)
