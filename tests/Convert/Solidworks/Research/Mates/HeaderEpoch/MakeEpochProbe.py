from tests.Convert.Solidworks.Research.Mates.Distance.MakeDistInput import MakeDistInput
from tests.Convert.Solidworks.Research.Mates.Construction.MateDesigns import KDatumNames
from typing import cast as CastValue


# header epoch cases must start from authored model geometry and declare their view rather than taking native fixture values
def MakeEpochProbe(
    AxisValue: str,
    CaseValue: str,
    ViewValue: str,
    ModeValue: str = "sdk",
    FaultValue: str | None = None,
) -> dict[str, object]:
    BundleValue = MakeDistInput(AxisValue)
    ChildValue = CastValue(dict[str, object], BundleValue["child"])
    Presentation = CastValue(dict[str, object], ChildValue["presentation"])
    FolderNames = CastValue(dict[str, object], Presentation["folder_names"])
    Presentation["folder_order"] = list(FolderNames)
    return {
        "mode": ModeValue,
        "bundle": BundleValue,
        "header_probe": {
            "case": CaseValue,
            "view": ViewValue,
            "datum": KDatumNames[AxisValue],
            "fault": FaultValue,
        },
    }
