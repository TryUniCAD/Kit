from pathlib import Path as FilePath
from sys import executable as PythonExe, platform as HostPlatform

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.RunQueueHost import RunQueueHost
from tests.Research.Windows.Records.CheckQueueReply import CheckQueueReply


# a witnessed native sharing conflict must preserve queue response binding and its original deadline
@TestMark.skipif(HostPlatform != "win32", reason="Windows file publication boundary")
@TestMark.parametrize("ReleaseHandle", (True, False))
def CheckQueueShare(TmpPath: FilePath, ReleaseHandle: bool) -> None:
    Harness = DispatchHost(TmpPath)
    Harness.Command = [
        PythonExe,
        str(
            FilePath(__file__).resolve().parents[4]
            / "re/automation/ApplicationWorkers/BusyQueueFixture.py"
        ),
    ]
    with RunQueueHost(Harness) as HostIdentity:
        Client = Harness.StartClient(Seconds=20 if ReleaseHandle else 5)
        try:
            _ = Harness.WaitFile("busy-ready")
            _ = Harness.WaitFile("busy-observed")
            assert Client.poll() is None
            if ReleaseHandle:
                (Harness.Endpoint / "release-busy").touch()
            Output, ErrorText = Client.communicate(timeout=25)
            assert Client.returncode == 0, Output + ErrorText
            CheckQueueReply(Output, HostIdentity, ReleaseHandle)
            assert (Harness.Endpoint / "fence.json").exists()
        finally:
            (Harness.Endpoint / "release-busy").touch()
            if Client.poll() is None:
                Client.kill()
                _ = Client.communicate(timeout=15)
