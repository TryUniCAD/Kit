from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.BossIntent.Candidate.RunRequest import RunRequest
from tests.Research.Archives.BossIntent.Candidate.VerifyRequest import VerifyRequest
from tests.Research.Archives.BossIntent.RunBossIntent import RunIntentStep


# the candidate request must originate from the real capture and logical preparation commands
def BuildRequest(TmpPath: FilePath) -> FilePath:
    SourcePath = TmpPath / "Source.json"
    LogicalPath = TmpPath / "Logical.json"
    for Arguments in (
        ("capture", "--output", str(SourcePath)),
        ("prepare", "--input", str(SourcePath), "--output", str(LogicalPath)),
    ):
        Result = RunIntentStep(TmpPath, *Arguments)
        assert Result.returncode == 0, Result.stdout + Result.stderr
    SourceBytes, LogicalBytes = SourcePath.read_bytes(), LogicalPath.read_bytes()
    Built = RunRequest(TmpPath)
    assert Built.returncode == 0, Built.stdout + Built.stderr
    RequestPath = TmpPath / "Request.json"
    Payload = RequestPath.read_bytes()
    Report = CastValue(dict[str, object], ReadJson(Built.stdout))
    assert Report["request_sha256"] == HashBytes(Payload).hexdigest()
    VerifyRequest(Payload, SourceBytes, LogicalBytes)
    Retry = RunRequest(TmpPath)
    assert Retry.returncode == 1 and "destination already exists" in Retry.stderr
    assert RequestPath.read_bytes() == Payload
    assert SourcePath.read_bytes() == SourceBytes
    assert LogicalPath.read_bytes() == LogicalBytes
    return RequestPath
