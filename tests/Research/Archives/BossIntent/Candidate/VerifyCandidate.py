from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import approx as Approx


# fresh generated readback must preserve geometry owners compatibility labels and honest qualification
def VerifyCandidate(
    Report: dict[str, object], Digest: str, RequestPath: FilePath
) -> str:
    Result = CastValue(dict[str, object], Report["result"])
    Candidate = CastValue(dict[str, object], Result["candidate"])
    Labels = CastValue(dict[str, object], Result["body_label_evidence"])
    assert Result["request_sha256"] == Digest
    assert (
        Result["source_operation"] == "join" and Result["target_operation"] == "create"
    )
    assert Result["vendor_loadable"] is False and Result["application_usable"] is False
    assert Labels["sdk_unbound_label"] == "Body 1"
    assert Labels["saved_compatibility_label"] == "BlindBoss"
    assert Labels["producer"] == "sldprt:feature:34"
    assert Candidate["stream_count"] == 32
    assert Candidate["dimensions_mm"] == [40.0, 20.0, 10.0]
    assert Candidate["centroid_metres"] == [0.02, 0.01, 0.005]
    assert Candidate["bounds_metres"] == [[0.0, 0.0, 0.0], [0.04, 0.02, 0.01]]
    assert Candidate["volume_m3"] == Approx(0.000008, rel=1e-12)
    assert Candidate["density_kg_m3"] == 1000.0
    assert Candidate["feature_ids"] == [57, 71]
    assert Candidate["dimension_ids"] == [91, 92, 93]
    assert Candidate["authored"] == Candidate["readback"]
    assert str(RequestPath.resolve()) in CastValue(list[str], Report["model_reads"])
    ArchiveHash = Candidate["archive_sha256"]
    assert isinstance(ArchiveHash, str) and len(ArchiveHash) == 64
    return ArchiveHash
