from hashlib import sha256 as HashBytes
from json import dumps as WriteJson, loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.BossIntent.Candidate.RunCandidate import RunCandidate
from tests.Research.Archives.BossIntent.Candidate.VerifyCandidate import VerifyCandidate


# a rehashed contradiction must fail even when request custody is valid
def CheckKeyOrder(RequestPath: FilePath, Digest: str, Payload: bytes) -> None:
    CandidatePath = RequestPath.with_name("SourceOrder.SLDPRT")
    Generated = RunCandidate(
        RequestPath, Digest, CandidatePath, PreserveKeywordOrder=True
    )
    assert Generated.returncode == 0, Generated.stdout + Generated.stderr
    Report = CastValue(dict[str, object], ReadJson(Generated.stdout))
    assert (
        VerifyCandidate(Report, Digest, RequestPath)
        == HashBytes(CandidatePath.read_bytes()).hexdigest()
        == "29b581feaf693b2a5e38e2f8bac70d2f3ab2b7f3f4f56be104e64701e0c0a62a"
    )
    Request = CastValue(dict[str, object], ReadJson(Payload))
    SavedRows = CastValue(list[list[object]], Request["source_ordered_relations"])
    First, Second = (
        Index for Index, SavedRow in enumerate(SavedRows) if SavedRow[1] == "distance"
    )
    SavedRows[First], SavedRows[Second] = SavedRows[Second], SavedRows[First]
    Contradictory = (
        WriteJson(Request, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    ).encode()
    ContradictoryPath = RequestPath.with_name("Contradictory.json")
    _ = ContradictoryPath.write_bytes(Contradictory)
    RejectedPath = RequestPath.with_name("Contradictory.SLDPRT")
    Refused = RunCandidate(
        ContradictoryPath,
        HashBytes(Contradictory).hexdigest(),
        RejectedPath,
        PreserveKeywordOrder=True,
    )
    assert Refused.returncode == 1
    assert (
        "P03 keyword order differs from the two ordered source driving dimensions"
        in Refused.stderr
    )
    assert not RejectedPath.exists()
    assert ContradictoryPath.read_bytes() == Contradictory
