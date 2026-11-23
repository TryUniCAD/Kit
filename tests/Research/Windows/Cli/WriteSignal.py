from json import dumps as DumpJson
from pathlib import Path as FilePath
from time import monotonic as ReadClock


# cancellation timing must distinguish forwarded shutdown from the independent maximum runtime fallback
def WriteSignal(RecordPath: FilePath, SignalName: str) -> None:
    _ = RecordPath.with_name("Interrupted").write_text(
        DumpJson({"signal": SignalName, "at": ReadClock()}), encoding="utf-8"
    )
