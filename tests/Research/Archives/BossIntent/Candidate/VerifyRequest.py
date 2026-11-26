from hashlib import sha256 as HashBytes
from json import loads as ReadJson
from typing import cast as CastValue


# the durable request must retain exact source lineage while separately binding its generator view
def VerifyRequest(Payload: bytes, SourceBytes: bytes, LogicalBytes: bytes) -> None:
    Request = CastValue(dict[str, object], ReadJson(Payload))
    assert Request["source_json_sha256"] == HashBytes(SourceBytes).hexdigest()
    assert Request["logical_json_sha256"] == HashBytes(LogicalBytes).hexdigest()
    TargetJson = Request["target_document"]
    assert isinstance(TargetJson, str)
    assert Request["target_json_sha256"] == HashBytes(TargetJson.encode()).hexdigest()
    SourceProof = CastValue(dict[str, object], Request["source_evidence"])
    Relations = CastValue(
        list[dict[str, object]], Request["source_relation_provenance"]
    )
    assert len(Relations) == 7
    assert [Relation["id"] for Relation in Relations] == SourceProof["saved_relations"]
    assert all(Relation["adapter"] == "solidworks.sldprt" for Relation in Relations)
    assert all(Relation["native_id"] for Relation in Relations)
    FirstSpans = CastValue(list[list[object]], Relations[0]["spans"])
    LastSpans = CastValue(list[list[object]], Relations[-1]["spans"])
    assert FirstSpans[0][:3] == ["Contents/Config-0-ResolvedFeatures", 7828, 55]
    assert LastSpans[0][:3] == ["Contents/Config-0-ResolvedFeatures", 7993, 73]
    assert SourceProof["source_operation"] == "join"
    assert Request["target_operation"] == "create"
