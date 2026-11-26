from hashlib import sha256 as HashBytes
from json import dumps as WriteJson, loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Research.Archives.BossIntent.Candidate.CheckKeyStreams import CheckKeyStreams
from tests.Research.Archives.BossIntent.Candidate.ReplayCandidate import ReplayCandidate
from tests.Research.Archives.BossIntent.Candidate.RunCandidate import RunCandidate


# a rehashed contradiction must fail even when request custody is valid
def CheckKeyOrder(
    RequestPath: FilePath, Digest: str, Payload: bytes, DefaultArchive: bytes
) -> None:
    First, Second = (
        ReplayCandidate(
            RequestPath,
            Digest,
            RequestPath.with_name(f"SourceOrder{Attempt}.SLDPRT"),
            PreserveKeywordOrder=True,
        )
        for Attempt in range(2)
    )
    assert First == Second
    CheckKeyStreams(DefaultArchive, First)
    Request = CastValue(dict[str, object], ReadJson(Payload))
    SavedRows = CastValue(list[list[object]], Request["source_ordered_relations"])
    FirstIndex, SecondIndex = (
        Index for Index, SavedRow in enumerate(SavedRows) if SavedRow[1] == "distance"
    )
    SavedRows[FirstIndex], SavedRows[SecondIndex] = (
        SavedRows[SecondIndex],
        SavedRows[FirstIndex],
    )
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
