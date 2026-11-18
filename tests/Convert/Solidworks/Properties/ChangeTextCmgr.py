from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrRows import ReadCmgrRows
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# native binary cache values may lag live xml while stale configuration owner names must remain detectable
def ChangeTextCmgr(BufferValue: bytes, IsStaleOwner: bool) -> bytes:
    GraphValue = ReadCmgrMut(BufferValue, 19000)
    (ConfigValue,) = ReadCmgrRows(GraphValue.RootValue)
    if IsStaleOwner:
        NameValue = ArchiveNode.RequireNode(ConfigValue.FieldsValue["f18"])
        NameValue.FieldsValue["f08"] = "different manager configuration"
    else:
        ConfigValue.FieldsValue["fb68"] = {
            "n": 1,
            "items": [
                {
                    "p": {
                        "f08": "SharedName",
                        "f10": "Text",
                        "f18": "Earlier cached text",
                        "f2c": 1,
                        "f28": 0,
                        "f20": "",
                        "f34": 0,
                        "f38": 1,
                        "f3c": 0,
                    }
                }
            ],
        }
    OutputValue = WriteCmgrMut(GraphValue.RootValue, 19000)
    DecodedValue = ReadCmgrMut(OutputValue, 19000)
    assert WriteCmgrMut(DecodedValue.RootValue, 19000) == OutputValue
    return OutputValue
