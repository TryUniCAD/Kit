from ntpath import join as JoinPath

from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Core.Preparation.DefaultPartTree import DefaultPartTree
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.Preparation.SelectPartSelf import KNeutralRoot
from interchange.document.Models.DocumentModel import CadDocument


# part labels and native locator names must survive through the same authored feature graph
def ReadStockName(DocumentValue: CadDocument) -> str:
    if set(DocumentValue.metadata) != {"name"}:
        raise ValueError("two-stock preparation requires only the authored part name")
    NameValue = ReadStyleText(DocumentValue.metadata["name"], "two-stock part name")
    if not NameValue.strip() or any(Character in NameValue for Character in "/\\"):
        raise ValueError("two-stock document name must be one native basename")
    _ = RequirePartPath(JoinPath(KNeutralRoot, NameValue + ".SLDPRT"), 0)
    Defaults = DefaultPartTree("Front Plane", 0)
    Reserved = (
        *(Value for _, Value in Defaults.FolderValues),
        *(Value for AxisValue, Value in Defaults.PlaneNames if AxisValue == "y"),
        Defaults.CabinetName,
        Defaults.OriginName,
    )
    LabelsValue = tuple(
        ReadStyleText(LabelValue, "two-stock owner name")
        for LabelValue in (
            *(Value.name for Value in DocumentValue.support_planes),
            *(Value.name for Value in DocumentValue.sketches),
            *(Value.name for Value in DocumentValue.feature_timeline),
        )
    )
    AllLabels = (*Reserved, *LabelsValue)
    if any(not LabelValue.strip() for LabelValue in LabelsValue) or len(
        {LabelValue.casefold() for LabelValue in AllLabels}
    ) != len(AllLabels):
        raise ValueError("two-stock preparation requires distinct authored owner names")
    return NameValue
