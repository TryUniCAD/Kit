from json import loads as DecodeJson
from pathlib import Path as FilePath
from sys import executable as PythonExe, platform as HostPlatform

from pytest import mark as TestMark

from tests.Research.Applications.DispatchHost import DispatchHost
from tests.Research.Applications.RunQueueHost import RunQueueHost


# a witnessed native sharing conflict must preserve queue response binding and its original deadline
@TestMark.skipif(HostPlatform != "win32", reason="Windows file publication boundary")
@TestMark.parametrize("ReleaseHandle", (True, False))
def CheckRecordPublication(TmpPath: FilePath, ReleaseHandle: bool) -> None:
    Harness = DispatchHost(TmpPath)
    Harness.Command = [
        PythonExe,
        str(
            FilePath(__file__).resolve().parents[3]
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
            Response = DecodeJson(Output)
            if ReleaseHandle:
                assert Response["status"] == "completed"
                assert Response["host"] == HostIdentity
                assert Response["provider"] == "fixture.transport"
                assert Response["proof"]["native_qualified"] is False
            else:
                assert Response["outcome"] == "waiting_application"
                assert "bounded deadline" in Response["reason"]
                assert Response["native_qualified"] is False
            assert (Harness.Endpoint / "fence.json").exists()
        finally:
            (Harness.Endpoint / "release-busy").touch()
            if Client.poll() is None:
                Client.kill()
                _ = Client.communicate(timeout=15)
