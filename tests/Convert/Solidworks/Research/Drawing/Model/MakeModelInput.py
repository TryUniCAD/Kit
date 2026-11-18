from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Drawing.Definition.MakeDefInput import (
    MakeDefInput,
)


# model construction must receive new folder names clocks and presentation intent independently of saved drawing graphs
def MakeModelInput(Label: str, Numerator: int, Denominator: int) -> dict[str, object]:
    Request = MakeDefInput(Label, Numerator, Denominator)
    Request["folder_names"] = {
        "annotations": Label + " annotations",
        "binder": Label + " documents",
        "comments": Label + " comments",
        "blocks": Label + " blocks",
        "ink_markups": Label + " ink",
        "review_markups": Label + " review",
    }
    Request["sheet_names"] = {
        "plane_name": Label + " datum",
        "profile_name": Label + " profile",
        "detail_name": Label + " details",
    }
    Provenance = CastValue(dict[str, object], Request["provenance"])
    Provenance.update(created_at=1794871231, modified_at=1794871272)
    OutputValue = CastValue(dict[str, object], Request["output"])
    OutputValue["saved_at"] = 1794871291
    return Request
