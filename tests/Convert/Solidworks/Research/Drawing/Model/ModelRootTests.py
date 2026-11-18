from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.Model.AssertModel import AssertModel
from tests.Convert.Solidworks.Research.Drawing.Model.MakeModelInput import (
    MakeModelInput,
)
from tests.Convert.Solidworks.Research.Drawing.Model.RunModelCase import RunModelCase


# distinct neutral settings must generate complete blank model ownership with exact independent bytes in fresh workers
def TestModelRoots() -> None:
    HashesValue: set[object] = set()
    for Label, Numerator, Denominator in (
        ("ModelAlpha", 9, 14),
        ("ModelBeta", 11, 3),
        ("ModelGamma", 21, 5),
        ("ModelDelta", 8, 23),
    ):
        Request = MakeModelInput(Label, Numerator, Denominator)
        Presentation = CastValue(dict[str, object], Request["presentation"])
        if Label == "ModelBeta":
            CastValue(dict[str, object], Request["sheet"])["custom_property_view"] = (
                "independent model Ω " + "p" * 360
            )
            CastValue(dict[str, object], Request["provenance"]).update(
                created_at=1794871004, modified_at=1794871209
            )
        if Label == "ModelGamma":
            CastValue(dict[str, object], Request["sheet"])["length_unit"] = "in"
            CastValue(dict[str, object], Presentation["units"]).update(
                length_unit="in", unit_system="ips", decimal_places=3
            )
            Presentation["auto_dim_text_link"] = False
        if Label == "ModelDelta":
            CastValue(dict[str, object], Presentation["definition"])[
                "drafting_standard"
            ] = "moISO_c"
            CastValue(dict[str, object], Presentation["styles"])[
                "font_name"
            ] = "Liberation Sans"
        JobValue: dict[str, object] = {
            "schema": "kit.sw2026.sdk-drawing-model-process.v1",
            "request": Request,
        }
        Result = RunModelCase(JobValue)
        assert Result == RunModelCase(JobValue)
        AssertModel(Result, 131)
        HashesValue.add(Result["artifact_sha256"])
    assert len(HashesValue) == 4
