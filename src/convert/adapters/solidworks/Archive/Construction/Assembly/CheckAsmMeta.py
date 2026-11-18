from ntpath import basename as BaseName, splitext as SplitExt
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)


# flat and recursive assembly construction need identical supported release style file identity and explicit provenance admission
def CheckAsmMeta(InputValue: AssemblyInput) -> None:
    if type(InputValue) is not AssemblyInput:
        raise TypeError("assembly publication requires typed construction inputs")
    StemValue, Extension = SplitExt(BaseName(InputValue.OutputValue.PathName))
    if (
        StemValue.casefold() != InputValue.NameValue.casefold()
        or Extension.casefold() != ".sldasm"
    ):
        raise ValueError(
            "assembly self filename must match its actual authored name and assembly kind"
        )
    if (
        InputValue.StyleValue.StandardValue != 1
        or InputValue.DefinitionValue.DraftingStandard != "moISO_c"
        or InputValue.TargetValue.FileVersion != 19000
    ):
        raise ValueError(
            "first complete assembly requires effective iso standard one and archive version 19000"
        )
    if (
        InputValue.HeaderValue.CreatedAt != InputValue.SystemValue.CreatedAt
        or InputValue.HeaderValue.CreatedAt != InputValue.HistoryValue.CreatedAt
        or InputValue.HeaderValue.CommentText != InputValue.HistoryValue.CommentText
        or InputValue.StyleValue.LanguageId != InputValue.HistoryValue.LanguageId
    ):
        raise ValueError(
            "assembly provenance differs across system header history or presentation owners"
        )
    for NameValue in (
        InputValue.NameValue,
        InputValue.ConfigName,
        InputValue.ManagerName,
    ):
        if not ReadStyleText(NameValue, "assembly document identity"):
            raise ValueError("assembly document identity names must not be empty")
