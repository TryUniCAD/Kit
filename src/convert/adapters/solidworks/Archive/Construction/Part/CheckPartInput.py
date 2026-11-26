from ntpath import basename as BaseName, splitext as SplitExt
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from interchange.document.Models.DocumentModel import CadDocument


# modeled presentation and provenance must agree with the supported neutral graph before construction can consume any persistent identity
def CheckPartInput(
    DocumentValue: CadDocument, InputValue: PartBuildInput, PlanValue: BlindPlan
) -> None:
    if type(InputValue) is not PartBuildInput:
        raise TypeError(
            "complete blind part requires typed explicit construction settings"
        )
    if (
        InputValue.DocumentUnits.LengthUnit != DocumentValue.units
        or InputValue.StyleValue.StandardValue != 1
        or InputValue.DefinitionValue.DraftingStandard != "moISO_c"
    ):
        raise ValueError(
            "first complete blind part requires matching document units and effective iso standard one"
        )
    if (
        InputValue.SystemValue.OriginAxis != "z"
        or dict(InputValue.SystemValue.PlaneNames).get("z") != PlanValue.PlaneName
    ):
        raise ValueError(
            "part system support must match the actual neutral front plane"
        )
    if (
        InputValue.HeaderValue.CreatedAt != InputValue.SystemValue.CreatedAt
        or InputValue.HeaderValue.CreatedAt != InputValue.HistoryValue.CreatedAt
        or InputValue.HeaderValue.CommentText != InputValue.HistoryValue.CommentText
    ):
        raise ValueError("part provenance must agree across folders header and history")
    if InputValue.HistoryValue.LanguageId != InputValue.StyleValue.LanguageId:
        raise ValueError("part style and history language provenance differ")
    if (
        SplitExt(BaseName(InputValue.OutputValue.PathName))[0].casefold()
        != PlanValue.NameValue.casefold()
    ):
        raise ValueError("native self filename must match the actual modeled part name")
    if (
        type(CastValue(object, InputValue.DesignIntent)) is not bool
        or type(CastValue(object, InputValue.SelectedLeader)) is not int
        or not -(1 << 31) <= InputValue.SelectedLeader < (1 << 31)
    ):
        raise ValueError(
            "boss display requires explicit design intent and selected leader presentation"
        )
    if ReadStyleNum(InputValue.DensityValue, "part density") <= 0:
        raise ValueError("part density must be positive")
    _ = ReadStyleText(InputValue.HatchName, "part hatch name")
    _ = ReadStyleText(InputValue.ManagerName, "configuration manager name")
    _ = ReadStyleText(InputValue.DefinitionValue.JournalName, "journal name")
    NamesValue = tuple(
        NameValue
        for _, NameValue in InputValue.SystemValue.FolderValues
        + InputValue.SystemValue.PlaneNames
    ) + (
        InputValue.SystemValue.CabinetName,
        InputValue.SystemValue.OriginName,
        PlanValue.SketchName,
        PlanValue.FeatureName,
    )
    if len(set(NamesValue)) != len(NamesValue):
        raise ValueError("native part features require distinct authored names")
