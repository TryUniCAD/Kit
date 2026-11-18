from collections.abc import MutableMapping
from typing import cast as CastValue
from xml.etree.ElementTree import fromstring as ParseXml, tostring as EncodeXml

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.AlterDimOwner import (
    AlterDimOwner,
)
from tests.Convert.Solidworks.Research.Resolved.LineDimensions.ExtendDimsMut import (
    ExtendDimsMut,
)


# generated archive variants isolate actual owner failures from stale searchable keyword values and conditional handle encodings
def ApplyRectMut(
    SketchValue: ArchiveNode,
    OtherSketch: ArchiveNode,
    StreamsValue: dict[str, bytes],
    ModeValue: str,
) -> None:
    if ModeValue == "reference-count":
        PointValue = CastValue(
            MutableMapping[str, object],
            NativeRows(SketchValue.FieldsValue["points"])[0]["point"],
        )
        PointValue["f20"] = CastValue(int, PointValue["f20"]) + 1
    elif ModeValue == "stale-keywords":
        DataValue = StreamsValue["swXmlContents/KeyWords"]
        RootValue = ParseXml(DataValue[1:])
        for IndexValue, Element in enumerate(RootValue.iter("Dimension")):
            setattr(Element, "text", str(999.0 + IndexValue))
        StreamsValue["swXmlContents/KeyWords"] = (
            b"\x86" + EncodeXml(RootValue, encoding="utf-8") + b"\r\n"
        )
    elif ModeValue == "extended-handles":
        ExtendDimsMut(SketchValue)
    else:
        AlterDimOwner(SketchValue, OtherSketch, ModeValue)
