from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import (
    ReadBodyScalar,
)


# matching kernel and archive identifiers must come from their separate typed ownership domains
def CheckBodyTags(
    AtomValue: ArchiveNode,
    FeatureId: int,
    NodesValue: Mapping[int, XmtNode],
    Attributes: Mapping[str, XmtNode],
) -> None:
    Expected = {
        "f140": ReadBodyScalar(NodesValue, Attributes, "ATOM_ID_2001", 1),
        "f180": ReadBodyScalar(NodesValue, Attributes, "BODY_MATCH", 0),
        "f1b0": ReadBodyScalar(NodesValue, Attributes, "BODY_MATCH", 0),
        "f12c": FeatureId,
        "f130": FeatureId,
    }
    if (
        ReadBodyScalar(NodesValue, Attributes, "LAST_BODY_MODIFYING_FEATURE_ID", 1)
        != FeatureId
        or any(
            type(AtomValue.FieldsValue.get(NameValue)) is not int
            or AtomValue.FieldsValue[NameValue] != ValueData
            for NameValue, ValueData in Expected.items()
        )
        or Expected["f140"] <= 0
        or Expected["f180"] <= 0
    ):
        raise ValueError("native body atom and feature identity domains disagree")
