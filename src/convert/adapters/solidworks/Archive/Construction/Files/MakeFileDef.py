from ntpath import basename as BaseName, splitext as SplitExt
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Container.Format import (
    KAsmSuffix,
    KPartSuffix,
)


# native shared file identity derives handle text and kind from the modeled document while retaining explicit creation provenance
def MakeFileDef(
    InputValue: SelfFileInput, NameValue: str, KindValue: int, CreatedAt: int
) -> dict[str, object]:
    Extension = {2: KPartSuffix, 3: KAsmSuffix, 4: ".slddrw"}.get(KindValue)
    if (
        Extension is None
        or SplitExt(BaseName(InputValue.PathName))[1].casefold() != Extension
    ):
        raise ValueError(
            "native self path extension differs from its actual model kind"
        )
    _ = ReadStyleText(NameValue, "native model name")
    if not NameValue or type(CreatedAt) is not int or not 0 <= CreatedAt <= 0xFFFFFFFF:
        raise ValueError(
            "native file identity requires an actual model name and unsigned creation time"
        )
    return {
        "h18": ArchiveNode(
            RuntimeClass("moCStringHandle_c", 1),
            {"value": CStringValue(InputValue.PathName, True)},
        ),
        "h10": ArchiveNode(
            RuntimeClass("moCStringHandle_c", 1),
            {"value": CStringValue(NameValue, True)},
        ),
        "f20": KindValue,
        "f08": 0,
        "f28": CreatedAt,
        "f38": CStringValue("", True),
        "f40": CStringValue("", True),
        "f50": CStringValue("", True),
        "f35": 0,
    }
