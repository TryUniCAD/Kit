from hashlib import sha256 as CalcSha
from json import dumps as DumpJson

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.Chamfers.ChmfSnapTrust import (
    KChmfSourceBundles,
)


# an attachment free snapshot needs an independently authenticated original source identity
def CheckChmfSha(SourceSha: str | None, Candidate: PartCandidate) -> None:
    if SourceSha == CalcSha(Candidate.BytesValue).hexdigest():
        return
    Witness = KChmfSourceBundles.get(SourceSha or "")
    Digests = {
        NameValue: CalcSha(DataValue).hexdigest()
        for NameValue, DataValue in Candidate.StreamsValue.items()
    }
    Bundle = DumpJson(Digests, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if Witness != CalcSha(Bundle).hexdigest():
        raise ValueError(
            "cold chamfer JSON readback differs from its regenerated part source identity"
        )
