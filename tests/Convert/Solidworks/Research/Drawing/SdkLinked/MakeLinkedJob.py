from typing import cast as CastValue

from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingModelRef import DrawingModelRef
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from interchange.document.Models.Drawing.DrawingView import DrawingView
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.serialization.EncodeData import ToData
from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import (
    BlindCaseInput,
)
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import (
    MakePlainDoc,
)
from tests.Convert.Solidworks.Research.Drawing.Portable.MakePortableCase import (
    MakeBlankCase,
)
from tests.Convert.Solidworks.Research.Drawing.Portable.MakePortableJob import (
    MakePortableJob,
)


# fresh actual neutral documents must vary child geometry view families scale and placement without borrowing any saved model
def MakeLinkedJob(
    Label: str,
    WidthValue: float,
    HeightValue: float,
    DepthValue: float,
    Orientation: str,
    ScaleValue: float,
) -> dict[str, object]:
    BaseValue = MakePortableJob(MakeBlankCase(Label, 7, 5))
    OptionsValue = CastValue(dict[str, object], BaseValue["options"])
    CastValue(dict[str, object], OptionsValue["folder_names"])[
        "binder"
    ] = "Design Binder"
    ChildValue = BlindCaseInput(Label + "Child", False)
    ChildValue["document"] = ToData(
        MakePlainDoc(Label + "Child", WidthValue, HeightValue, DepthValue)
    )
    SettingsValue = CastValue(dict[str, object], ChildValue["settings"])
    OutputValue = CastValue(dict[str, object], SettingsValue["output"])
    Reference = DrawingModelRef(
        "neutral:child:" + Label, str(OutputValue["path_name"]), "solidworks.sldprt"
    )
    ViewValue = DrawingView(
        "neutral:view:" + Label,
        Label + " model view",
        Reference.EntityId,
        "modeled default",
        PlaneVector(0.1217, 0.0873),
        Orientation,
        (ScaleValue, 1.0),
    )
    SheetValue = DrawingSheet(
        "neutral:sheet:" + Label,
        Label + " paper",
        11 * 0.0254,
        8.5 * 0.0254,
        (7.0, 5.0),
        (ViewValue,),
    )
    return {
        "schema": "kit.sw2026.sdk-linked-drawing-process.v1",
        "drawing_document": CastValue(
            object,
            ToData(DrawingData(SheetValue.EntityId, (SheetValue,), (Reference,))),
        ),
        "native": {
            KeyValue: BaseValue[KeyValue]
            for KeyValue in ("options", "provenance", "ui", "output")
        },
        "part": ChildValue,
        "support_names": {
            "detail": Label + " view detail",
            "sheet_plane": Label + " paper plane",
            "sheet_profile": Label + " paper sketch",
            "model_plane": Label + " model plane",
            "model_profile": Label + " model sketch",
        },
    }
