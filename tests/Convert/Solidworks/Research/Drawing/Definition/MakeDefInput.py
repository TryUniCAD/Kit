from hashlib import sha256 as DigestValue
from typing import cast as CastValue
from uuid import UUID as UuidValue

from tests.Convert.Solidworks.Research.Drawing.MakeSheetInput import MakeSheetInput


# fresh neutral metadata and identities must challenge complete stream emission beyond one saved design
def MakeDefInput(Label: str, Numerator: int, Denominator: int) -> dict[str, object]:
    Request = MakeSheetInput(Label, Numerator, Denominator)
    Provenance = CastValue(dict[str, object], Request["provenance"])
    SeedValue = int.from_bytes(DigestValue(Label.encode()).digest()[:16], "big")
    Provenance["block_identity"] = str(UuidValue(int=SeedValue, version=4))
    Provenance["author"] = "independent author " + Label
    Provenance["company"] = "independent whole definition"
    Provenance["comment"] = "authored definition " + Label
    return Request
