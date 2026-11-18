from functools import partial
from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUsage import BodyUsage
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigLayouts import (
    KConfigLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigSchemas import (
    KConfigSchemas,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConfigVirtuals import (
    KConfigVirtuals,
)
from convert.adapters.solidworks.Archive.Bodies.ReadBodyMut import ReadBodyMut
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Reading.BinaryReader import BinaryReader
from convert.adapters.solidworks.Archive.Reading.GraphReader import GraphReader
from convert.adapters.solidworks.Archive.Reading.ReadGraphNode import ReadNodeMut
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


def context(version):
    if type(version) is not int or version != 19000:
        raise ValueError(
            "ANSI construction requires the ordinary version-19000 body profile"
        )
    return BodyContext(
        version, KConfigLayouts, KConfigVirtuals, KConfigSchemas, BodyUsage()
    )


def encode(root, version=19000):
    writer = BodyWriter(ArchiveMaps(1), context(version), WriteBodyMut)
    WriteNodeMut(writer, root)
    if writer.ContextValue.UsageValue.MissingNames:
        raise ValueError("style emission used an unsupported class")
    return bytes(writer.OutputValue), writer


def decode(data, version=19000):
    scope = context(version)
    reader = GraphReader(
        BinaryReader(data), ArchiveMaps(1), partial(ReadBodyMut, scope)
    )
    root = ReadNodeMut(reader)
    if not isinstance(root, ArchiveNode) or root.ClassValue != RuntimeClass(
        "moDetailDefs_c", 1
    ):
        raise ValueError("style record has another actual root")
    if reader.Cursor.GetRemaining() or scope.UsageValue.MissingNames:
        raise ValueError("style record did not finish its typed grammar")
    return root, reader, scope


def plain(value, seen=()):
    if isinstance(value, CStringValue):
        return value.TextValue
    if isinstance(value, ArchiveNode):
        if id(value) in seen:
            raise ValueError(
                "style comparison requires explicit handling of a cyclic node"
            )
        return {
            "$class": value.ClassValue.NameValue,
            "$fields": plain(value.FieldsValue, seen + (id(value),)),
        }
    if isinstance(value, Mapping):
        return {key: plain(item, seen) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item, seen) for item in value]
    if value is None or type(value) in (str, int, float, bool):
        return value
    raise TypeError("unrepresented typed style field " + type(value).__name__)


def field_diff(left, right, path=""):
    if isinstance(left, dict) and isinstance(right, dict):
        return [
            row
            for key in sorted(set(left) | set(right))
            for row in field_diff(
                left.get(key, {"$missing": True}),
                right.get(key, {"$missing": True}),
                path + "/" + key,
            )
        ]
    if isinstance(left, list) and isinstance(right, list):
        return [
            row
            for index in range(max(len(left), len(right)))
            for row in field_diff(
                left[index] if index < len(left) else {"$missing": True},
                right[index] if index < len(right) else {"$missing": True},
                path + "/" + str(index),
            )
        ]
    return [] if left == right else [{"path": path, "left": left, "right": right}]
