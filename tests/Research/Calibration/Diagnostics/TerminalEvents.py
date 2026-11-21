import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.Calibration.Diagnostics.TerminalEvent import TerminalEvent


# the final bounded output window preserves failure classifications from the supervisor
def TerminalEvents(TrialPath: FilePath) -> list[dict[str, object]]:
    try:
        LogPath = TrialPath / "stdout.log"
        with LogPath.open("rb") as Source:
            _ = Source.seek(max(0, LogPath.stat().st_size - 32768))
            Content = Source.read(32768)
    except OSError:
        return []
    Events: list[dict[str, object]] = []
    for LineBytes in Content.splitlines():
        try:
            Detail = TerminalEvent(JsonCodec.loads(LineBytes))
        except ValueError:
            continue
        if Detail is not None:
            Events.append(Detail)
    return Events[-8:]
