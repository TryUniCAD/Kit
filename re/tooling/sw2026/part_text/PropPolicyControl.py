from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Properties.MakePropContext import MakePropContext
from convert.adapters.solidworks.Archive.Properties.ReadPropManager import ReadPropRoot

CAUSE = "part property manager policy is outside the empty profile"


def encode(root):
    writer = BodyWriter(ArchiveMaps(1), MakePropContext(19000), WriteBodyMut)
    WriteNodeMut(writer, root)
    return bytes(writer.OutputValue)


def unknown_policy(data):
    root = ReadPropRoot(data, 19000)
    if root.FieldsValue["f08"] != 1 or encode(root) != data:
        raise ValueError("the policy control requires its exact typed original manager")
    root.FieldsValue["f08"] = 2
    changed = encode(root)
    decoded = ReadPropRoot(changed, 19000)
    if decoded.FieldsValue["f08"] != 2:
        raise ValueError("the unsupported manager policy did not reach the physical owner")
    decoded.FieldsValue["f08"] = 1
    if encode(decoded) != data:
        raise ValueError("the policy control changed unrelated manager state")
    return changed
