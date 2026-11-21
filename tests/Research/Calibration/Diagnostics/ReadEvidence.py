import json as JsonCodec
from pathlib import Path as FilePath

from tests.Research.Calibration.Diagnostics.CalJsonTypes import IsJsonRecord


# diagnostic reads must stay within calibration metadata bounds even after a partial write
def ReadEvidence(RecordPath: FilePath) -> dict[str, object]:
    try:
        with RecordPath.open("rb") as Source:
            Content = Source.read(1048577)
        if len(Content) > 1048576:
            return {}
        Record: object = JsonCodec.loads(Content)
    except (OSError, ValueError):
        return {}
    return Record if IsJsonRecord(Record) else {}
