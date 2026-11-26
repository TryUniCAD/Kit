from hashlib import sha256 as HashBytes
from pathlib import Path as FilePath

from tests.Research.Archives.BossIntent.Candidate.BuildRequest import BuildRequest
from tests.Research.Archives.BossIntent.Candidate.CheckKeyOrder import (
    CheckKeyOrder,
)
from tests.Research.Archives.BossIntent.Candidate.ReplayCandidate import ReplayCandidate
from tests.Research.Archives.BossIntent.Candidate.RunCandidate import RunCandidate


# request custody must survive losing the original inputs before independent candidate generation
def CheckCandidate(TmpPath: FilePath) -> None:
    RequestPath = BuildRequest(TmpPath)
    Payload = RequestPath.read_bytes()
    Digest = HashBytes(Payload).hexdigest()
    for FileName in ("Source.json", "Logical.json"):
        (TmpPath / FileName).unlink()
    First, Second = (
        ReplayCandidate(RequestPath, Digest, TmpPath / f"Replay{Attempt}.SLDPRT")
        for Attempt in range(2)
    )
    assert First == Second
    CheckKeyOrder(RequestPath, Digest, Payload, First)
    Refused = RunCandidate(RequestPath, "0" * 64)
    assert Refused.returncode == 1
    assert (
        "P03 request does not match the separately retained SHA-256" in Refused.stderr
    )
    assert RequestPath.read_bytes() == Payload
    assert not (TmpPath / "Source.json").exists()
    assert not (TmpPath / "Logical.json").exists()
