from convert.adapters.solidworks.Archive.Construction.Styles.MakeDetails import (
    MakeDetails,
)
from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitTable import (
    MakeUnitTable,
)
from convert.adapters.solidworks.Archive.Construction.Views.MakeStdViews import (
    MakeStdViews,
)
from convert.adapters.solidworks.Drawing.Construction.Model.DrawBuild import DrawBuild
from convert.adapters.solidworks.Drawing.Construction.Model.DrawRootRefs import (
    DrawRootRefs,
)


# shared style unit and view constructors must supply drawing dependencies directly from neutral presentation intent
def MakeDrawRefs(BuildValue: DrawBuild) -> DrawRootRefs:
    StyleValue = BuildValue.StyleValue
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
    return DrawRootRefs(
        DetailFields,
        MakeUnitTable(BuildValue.UnitValue),
        MakeStdViews(StyleValue.StandardValue),
    )
