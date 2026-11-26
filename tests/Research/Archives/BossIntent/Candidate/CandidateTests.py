from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.BossIntent.Candidate.BuildRequest import BuildRequest
from tests.Research.Archives.BossIntent.Candidate.CheckKeyOrder import (
    CheckKeyOrder,
)
from tests.Research.Archives.BossIntent.Candidate.RunCandidate import RunCandidate
from tests.Research.Archives.BossIntent.Candidate.VerifyCandidate import VerifyCandidate


# request custody must survive losing the original inputs before independent candidate generation
def CheckCandidate(TmpPath: FilePath) -> None:
    RequestPath = BuildRequest(TmpPath)
    Payload = RequestPath.read_bytes()
    Digest = HashBytes(Payload).hexdigest()
    for FileName in ("Source.json", "Logical.json"):
        (TmpPath / FileName).unlink()
    Reports: list[str] = []
    for Attempt in range(2):
        Result = RunCandidate(RequestPath, Digest)
        assert Result.returncode == 0, Result.stdout + Result.stderr
        _ = (TmpPath / f"Replay{Attempt}.json").write_text(
            Result.stdout, encoding="utf-8"
        )
        Report = CastValue(dict[str, object], ReadJson(Result.stdout))
        Reports.append(VerifyCandidate(Report, Digest, RequestPath))
    assert (
        Reports[0]
        == Reports[1]
        == "a0e524cc73b844042c7da6bf86b3a12120fb4f73aaf34de7f0d6cc481ebda15f"
    )
    CheckKeyOrder(RequestPath, Digest, Payload)
    Refused = RunCandidate(RequestPath, "0" * 64)
    assert Refused.returncode == 1
    assert (
        "P03 request does not match the separately retained SHA-256" in Refused.stderr
    )
    assert RequestPath.read_bytes() == Payload
    assert not (TmpPath / "Source.json").exists()
    assert not (TmpPath / "Logical.json").exists()
