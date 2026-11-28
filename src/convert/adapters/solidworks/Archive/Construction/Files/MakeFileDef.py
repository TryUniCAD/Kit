from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# the native self record derives handle text and model kind from the validated locator
def MakeFileDef(
    InputValue: SelfFileInput, NameValue: str, CreatedAt: int
) -> dict[str, object]:
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
        "f20": 3 if InputValue.IsAssembly else 2,
        "f08": 0,
        "f28": CreatedAt,
        "f38": CStringValue("", True),
        "f40": CStringValue("", True),
        "f50": CStringValue("", True),
        "f35": 0,
    }
