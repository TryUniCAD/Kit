from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.BossIntent.Candidate.RunCandidate import RunCandidate
from tests.Research.Archives.BossIntent.Candidate.VerifyCandidate import VerifyCandidate


# the process report must describe the archive actually published by each isolated replay
def ReplayCandidate(
    RequestPath: FilePath,
    Digest: str,
    CandidatePath: FilePath,
    *,
    PreserveKeywordOrder: bool = False,
) -> bytes:
    Result = RunCandidate(
        RequestPath, Digest, CandidatePath, PreserveKeywordOrder=PreserveKeywordOrder
    )
    assert Result.returncode == 0, Result.stdout + Result.stderr
    _ = CandidatePath.with_suffix(".json").write_text(Result.stdout, encoding="utf-8")
    Report = CastValue(dict[str, object], ReadJson(Result.stdout))
    Output = CandidatePath.read_bytes()
    assert (
        VerifyCandidate(Report, Digest, RequestPath, Output)
        == HashBytes(Output).hexdigest()
    )
    return Output
