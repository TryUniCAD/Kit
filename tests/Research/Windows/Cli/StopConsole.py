from subprocess import Popen, run as RunProcess


# a failed console witness must not leave its launcher or supervised descendants running
def StopConsole(ChildProcess: Popen[bytes] | Popen[str]) -> None:
    if ChildProcess.poll() is not None:
        return
    Stopped = RunProcess(
        ["taskkill.exe", "/PID", str(ChildProcess.pid), "/T", "/F"],
        capture_output=True, text=True, check=False, timeout=30,
    )
    if Stopped.returncode != 0 and ChildProcess.poll() is None:
        ChildProcess.kill()
        _ = ChildProcess.wait(timeout=10)
        raise RuntimeError(f"Owned console tree cleanup failed: {Stopped.stderr}")
    _ = ChildProcess.wait(timeout=10)
