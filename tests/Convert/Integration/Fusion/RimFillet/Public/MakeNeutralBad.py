from hashlib import sha256 as HashData

from convert.api.ApiOpen import OpenDocument
from interchange.document.Models.DocumentModel import CadDocument
from tests.Convert.Integration.Fusion.RimFillet.Policy.RimPolicyCase import (
    RimPolicyCase,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.ChangeRimPick import (
    ChangeRimPick,
)
from tests.Convert.Integration.Fusion.RimFillet.Public.ChangeRimShape import (
    ChangeRimShape,
)


# malformed neutral inputs must originate from a valid public archive read and complete json restoration
def MakeNeutralBad(Sample: RimPolicyCase, ModeName: str) -> str:
    assert HashData(Sample.Source.read_bytes()).hexdigest() == Sample.Digest
    Document = OpenDocument(Sample.Source)
    Document.AssertValid()
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored == Document
    Changed = (
        ChangeRimPick(Restored, ModeName)
        if ModeName
        in (
            "vertex_query",
            "wrong_curve",
            "lower_query",
            "missing_body",
            "foreign_body",
            "self_source",
            "missing_source",
            "missing_dependency",
            "extra_dependency",
        )
        else ChangeRimShape(Restored, ModeName)
    )
    return Changed.to_json()
