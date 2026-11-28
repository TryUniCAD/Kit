from convert.adapters.solidworks.Archive.Construction.Model.PartRootRefs import (
    PartRootRefs,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.MakeModelVisual import (
    MakeModelVisual,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.MakeDetails import (
    MakeDetails,
)
from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitTable import (
    MakeUnitTable,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Construction.Views.MakeStdViews import (
    MakeStdViews,
)


# neutral presentation inputs must generate independently owned document dependencies before the actual model root receives their references
def MakePartRefs(
    StyleValue: StyleInput,
    DocumentValue: UnitInput,
    AnalysisValue: UnitInput,
    *,
    PlatformViewMath: bool = False,
) -> PartRootRefs:
    if type(StyleValue) is not StyleInput:
        raise TypeError("model presentation requires explicit typed style inputs")
    DetailFields = MakeDetails(
        StandardValue=StyleValue.StandardValue,
        FontName=StyleValue.FontName,
        LineStyleName=StyleValue.LineStyleName,
        LanguageId=StyleValue.LanguageId,
        PrintWidths=StyleValue.PrintWidths,
        ExclusionNames=StyleValue.ExclusionNames,
        TaskLabels=StyleValue.TaskLabels,
        CutlistExpressions=StyleValue.CutlistExpressions,
    )
    return PartRootRefs(
        DetailFields,
        MakeUnitTable(DocumentValue),
        MakeUnitTable(AnalysisValue),
        MakeModelVisual(),
        MakeStdViews(StyleValue.StandardValue, PlatformMath=PlatformViewMath),
    )
