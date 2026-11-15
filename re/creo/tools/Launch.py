"""Research probe: launch a part in Creo and report one of the three outcomes.

Every Creo check in this project ends the same way — launch the part, read the newest `trail.txt.*` and the parse
trace in `std.out`, then classify. Doing that by hand invites the two mistakes that have already cost time here:
a mistyped Windows path (the launch silently does nothing) and reading `dbg_err_crash` as a refusal when the part
still loaded.

So this prints one line per run:

    clean          Start, End, MT Part Solid, no dbg_err_crash, no "cannot be retrieved"
    load-with-error the previous line plus dbg_err_crash
    refused        no End line, or "cannot be retrieved"
    not-launched   no trail was written at all
    unavailable    prlctl cannot open a session (the guest is not signed in)

    PYTHONPATH=src python3 re/creo/tools/Launch.py ~/Documents/creo-authored/hybrid949.prt

The VM name can be overridden with `--vm`, and `--keep-trail` skips clearing the previous logs.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

KRemote = "\\\\Mac\\Home\\Documents\\creo-authored"
KBinary = "C:\\Program Files\\PTC\\Creo 2027.2.0.0\\Parametric\\bin"
KTrailPattern = "trail.txt.*"


def Run(Command: str) -> tuple[int, str]:
    Process = subprocess.run(
        Command, shell=True, capture_output=True, text=True, timeout=180
    )
    return (Process.returncode, Process.stdout + Process.stderr)


def Execute(VmName: str, RemotePath: str) -> bool:
    Command = (
        f'prlctl exec "{VmName}" cmd /c "cd /d \\"{KBinary}\\" && '
        f'start /b parametric.exe -g:no_graphics \\"{RemotePath}\\""'
    )
    ReturnCode, _Output = Run(Command)
    return ReturnCode == 0


def ClearLogs(VmName: str) -> None:
    Run(
        f'prlctl exec "{VmName}" powershell -NoProfile -Command '
        f'"Get-Process parametric -ErrorAction SilentlyContinue | Stop-Process -Force; '
        f"Remove-Item '{KBinary}\\{KTrailPattern}' -Force -ErrorAction SilentlyContinue; "
        f"Remove-Item '{KBinary}\\std.out' -Force -ErrorAction SilentlyContinue\""
    )


def ReadLogs(VmName: str) -> str:
    Command = (
        f'prlctl exec "{VmName}" powershell -NoProfile -Command '
        f'"$t=(Get-ChildItem \'{KBinary}\' -Filter \'{KTrailPattern}\' | '
        f"Sort-Object LastWriteTime | Select-Object -Last 1); "
        f'if($t){{Get-Content $t.FullName}}; '
        f"if(Test-Path '{KBinary}\\std.out'){{Get-Content '{KBinary}\\std.out'}}\""
    )
    _ReturnCode, Output = Run(Command)
    return Output


def Classify(Log: str) -> str:
    if "Unable to open new session" in Log:
        return "unavailable"
    if "Start " not in Log and "Inputname" not in Log:
        return "not-launched"
    if "cannot be retrieved" in Log:
        return "refused"
    if "dbg_err_crash" in Log:
        return "load-with-error"
    if "End   C:" in Log and "MT Part Solid" in Log:
        return "clean"
    return "refused"


def main() -> int:
    Arguments = [Value for Value in sys.argv[1:] if not Value.startswith("--")]
    if not Arguments:
        print("usage: Launch.py <part> [--vm NAME] [--keep-trail]")
        return 2
    VmName = "Windows 11"
    for IndexValue, Value in enumerate(sys.argv):
        if Value == "--vm" and IndexValue + 1 < len(sys.argv):
            VmName = sys.argv[IndexValue + 1]
    Source = Path(Arguments[0]).expanduser().resolve()
    if not Source.exists():
        print(f"missing part: {Source}")
        return 2
    if "--keep-trail" not in sys.argv:
        ClearLogs(VmName)
    RemotePath = KRemote + "\\" + Source.name
    Launched = Execute(VmName, RemotePath)
    if not Launched:
        Log = ReadLogs(VmName)
        Verdict = Classify(Log) if Log else "unavailable"
        Reason = "no prlctl session" if Verdict == "unavailable" else "prlctl exec failed"
        print(f"{Source.name}: {Reason}")
        return 1
    import time

    time.sleep(38)
    Log = ReadLogs(VmName)
    Verdict = Classify(Log)
    print(f"{Source.name}: {Verdict}")
    return 0 if Verdict == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
