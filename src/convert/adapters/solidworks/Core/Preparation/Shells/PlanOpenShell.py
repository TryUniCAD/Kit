from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import (
    ProjectBlind,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectSketch import (
    ReadRectSketch,
)
from convert.adapters.solidworks.Archive.Construction.Shells.OpenShellPlan import (
    OpenShellPlan,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from convert.adapters.solidworks.Core.Preparation.Shells.ReadShellStep import (
    ReadShellStep,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.geometry.Models.Selection import SelectPathElem


# scope validates the selected stock cap and both original drivers before projecting the stock
def PlanOpenShell(DocumentValue: CadDocument) -> OpenShellPlan:
    CheckPlainScope(DocumentValue)
    DocumentValue.assert_valid()
    if (
        DocumentValue.units != "mm"
        or not DocumentValue.capabilities <= KPartWriteCaps | {Capability.KSelections}
        or len(DocumentValue.feature_timeline) != 2
        or len(DocumentValue.parameters) != 2
        or len(DocumentValue.bodies) != 1
        or len(DocumentValue.selections) != 1
    ):
        raise ValueError("open shell needs one independent rectangular stock and cap")
    StockValue, ShellValue = DocumentValue.feature_timeline
    (BodyValue,) = DocumentValue.bodies
    (SelectionValue,) = DocumentValue.selections
    Drivers = {Value.id: Value for Value in DocumentValue.parameters}
    OwnerIds = (*StockValue.parameter_ids, *ShellValue.parameter_ids)
    if (
        len(StockValue.parameter_ids) != 1
        or len(ShellValue.parameter_ids) != 1
        or set(OwnerIds) != set(Drivers)
        or len(set(OwnerIds)) != len(OwnerIds)
        or BodyValue.final_feature_id != ShellValue.id
        or BodyValue.name != ShellValue.name
        or ShellValue.selection_ids != (SelectionValue.id,)
        or SelectionValue.path != (SelectPathElem("feature", StockValue.id, "face:1"),)
        or SelectionValue.point is not None
        or SelectionValue.query
        or SelectionValue.attributes
        or SelectionValue.provenance is not None
    ):
        raise ValueError("open shell needs the actual upper stock cap and result body")
    StockDriver, ShellDriver = (Drivers[Value] for Value in OwnerIds)
    StockDoc = ReplaceValue(
        DocumentValue,
        parameters=(StockDriver,),
        selections=(),
        feature_timeline=(StockValue,),
        bodies=(
            ReplaceValue(
                BodyValue, name=StockValue.name, final_feature_id=StockValue.id
            ),
        ),
    )
    Stock = ProjectBlind(StockDoc, ReadRectSketch)
    if Stock.PlaneName != "Front Plane" or Stock.ConfigName != "Default":
        raise ValueError("open shell stock requires Front Plane and Default")
    FeatureName, ThicknessM = ReadShellStep(ShellValue, StockValue, ShellDriver)
    if (
        not FeatureName
        or not IsFinite(Stock.WidthValue * Stock.HeightValue * Stock.DepthValue)
        or not 2 * ThicknessM < min(Stock.WidthValue, Stock.HeightValue)
        or not ThicknessM < Stock.DepthValue
    ):
        raise ValueError("open shell wall would remove its rectangular cavity")
    return OpenShellPlan(Stock, FeatureName, ThicknessM)
