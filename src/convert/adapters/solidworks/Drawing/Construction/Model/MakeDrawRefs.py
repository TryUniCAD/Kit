from convert.adapters.solidworks.Archive.Construction.Styles.Ansi.MakeAnsiDetails import (
    MakeAnsiDetails,
)
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
from convert.adapters.solidworks.Drawing.Construction.Model.MakeDrawViews import (
    MakeDrawViews,
)


# shared style unit and view constructors must supply drawing dependencies directly from neutral presentation intent
def MakeDrawRefs(
    BuildValue: DrawBuild, *, UseDrawingAnsi: bool = False
) -> DrawRootRefs:
    StyleValue = BuildValue.StyleValue
    if UseDrawingAnsi:
        return DrawRootRefs(
            MakeAnsiDetails(StyleValue),
            MakeUnitTable(BuildValue.UnitValue),
            MakeDrawViews(StyleValue.LanguageId),
        )
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
