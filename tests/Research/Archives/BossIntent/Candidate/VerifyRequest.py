from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from typing import cast as CastValue

from interchange.document.Models.DocumentModel import CadDocument
from tests.Research.Archives.BossIntent.Candidate.VerifyCornerAliases import (
    VerifyCorners,
)
from tests.Research.Archives.BossIntent.Candidate.VerifyRuleGeometry import (
    VerifyRuleGeom,
)
from tests.Research.Archives.BossIntent.Candidate.VerifySavedRows import VerifySavedRows


# the durable request must retain exact source lineage while separately binding its generator view
def VerifyRequest(Payload: bytes, SourceBytes: bytes, LogicalBytes: bytes) -> None:
    Request = CastValue(dict[str, object], ReadJson(Payload))
    assert Request["source_json_sha256"] == HashBytes(SourceBytes).hexdigest()
    assert Request["logical_json_sha256"] == HashBytes(LogicalBytes).hexdigest()
    TargetJson = Request["target_document"]
    assert isinstance(TargetJson, str)
    assert Request["target_json_sha256"] == HashBytes(TargetJson.encode()).hexdigest()
    SourceProof = CastValue(dict[str, object], Request["source_evidence"])
    Source = CadDocument.from_json(SourceBytes.decode("utf-8"))
    Target = CadDocument.from_json(TargetJson)
    assert (
        SourceProof["source_sha256"]
        == Source.source.sha256
        == ("db1390476325f5817e6f80fb4067a3c6df5cc063315604c133ccbeaafdeac357")
    )
    (SketchValue,) = Source.sketches
    SavedRows = tuple(
        RuleValue
        for RuleValue in SketchValue.constraints
        if RuleValue.provenance is not None
    )
    VerifySavedRows(SavedRows, Request, SourceProof)
    VerifyRuleGeom(Source, Target, SavedRows)
    VerifyCorners(Source, Target, SourceProof)
    assert SourceProof["source_operation"] == "join"
    assert Request["target_operation"] == "create"
