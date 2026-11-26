from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import (
    KConfigHdrClass,
)
from convert.adapters.solidworks.Archive.Construction.Model.GraphValue import (
    FieldInt,
    FieldText,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# lightweight entries derive the name and save state from the chosen configuration and part
def MakeMgrEntry(ConfigValue: ArchiveNode, OwnerValue: ArchiveNode) -> ArchiveNode:
    Values = ConfigValue.FieldsValue
    NameNode = ArchiveNode.RequireNode(Values["f18"])
    NameValue = FieldText(NameNode.FieldsValue, "f08")
    Description = ReadStyleText(Values["f1f8"], "configuration description")
    return ArchiveNode(
        KConfigHdrClass,
        {
            "f08": 1,
            "f10": NameValue,
            "f30": FieldInt(Values, "f08"),
            "f38": FieldInt(Values, "f860"),
            "f18": Description or NameValue,
            "f34": -1,
            "f40": int(
                FieldInt(Values, "f968") != 1 and bool(FieldInt(Values, "f0c") & 8)
            ),
            "f20": ReadStyleText(Values["f4a8"], "configuration comment"),
            "f28": ReadStyleText(Values["f498"], "configuration alternate name"),
            "f44": FieldInt(Values, "f4c4"),
            "f48": FieldInt(Values, "fbd0"),
            "f50": FieldInt(OwnerValue.FieldsValue, "f1300"),
            "f4c": 101,
        },
    )
