from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.Definition.MakeDefInput import (
    MakeDefInput,
)


# independent names and clocks must reach newly allocated supports rather than retained sheet fields
def MakeCtorInput(Label: str, Numerator: int, Denominator: int) -> dict[str, object]:
    Request = MakeDefInput(Label, Numerator, Denominator)
    Request["sheet_names"] = {
        "plane_name": Label + " datum",
        "profile_name": Label + " profile",
        "detail_name": Label + " annotations",
    }
    Provenance = CastValue(dict[str, object], Request["provenance"])
    Provenance.update(created_at=1794794441, modified_at=1794794461)
    OutputValue = CastValue(dict[str, object], Request["output"])
    OutputValue["saved_at"] = 1794794470
    return Request
