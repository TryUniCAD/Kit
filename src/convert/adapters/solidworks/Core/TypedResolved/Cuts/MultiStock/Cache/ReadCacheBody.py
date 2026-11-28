from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import (
    ReadBodyAttrs,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import (
    ReadBodyScalar,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadKernelName import (
    ReadKernelName,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cache.StockCacheBody import (
    StockCacheBody,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName


# transient kernel tags alone can identify the retired input as well as the surviving cut
def ReadCacheBody(
    NodesValue: Mapping[int, XmtNode],
    KernelValue: XmtNode,
    Owners: Mapping[int, tuple[ArchiveNode, ArchiveNode]],
) -> StockCacheBody:
    Fields = KernelValue.FieldsValue
    if (
        Fields.get("state") != 1
        or Fields.get("body_type") != 1
        or any(Fields.get(NameValue) != 0 for NameValue in ("ref_instance", "child", "key"))
    ):
        raise ValueError("saved stock cache has alternate kernel body state")
    Attributes = ReadBodyAttrs(NodesValue, KernelValue)
    if not {"ATOM_ID_2001", "BODY_MATCH", "LAST_BODY_MODIFYING_FEATURE_ID", "SWIMPLICITBODYNAME_ID_U"}.issubset(Attributes):
        raise ValueError("saved stock cache lacks its actual body identity attributes")
    if any(
        Attributes[NameValue].Indexes("fields")[:1] != (0,)
        for NameValue in ("ATOM_ID_2001", "LAST_BODY_MODIFYING_FEATURE_ID")
    ):
        raise ValueError("saved stock cache has alternate tracking pointer lanes")
    AtomId = ReadBodyScalar(NodesValue, Attributes, "ATOM_ID_2001", 1)
    if AtomId not in Owners:
        raise ValueError("saved kernel body does not identify a surviving stock atom")
    AtomValue, ProducerValue = Owners[AtomId]
    TagValue = ReadBodyScalar(NodesValue, Attributes, "BODY_MATCH", 0)
    FeatureId = ReadBodyScalar(NodesValue, Attributes, "LAST_BODY_MODIFYING_FEATURE_ID", 1)
    AtomFields = AtomValue.FieldsValue
    if (
        TagValue <= 0
        or AtomFields.get("f180") != TagValue
        or AtomFields.get("f1b0") != TagValue
        or FeatureId != NativeNodeId(ProducerValue)
    ):
        raise ValueError("saved kernel body tag or producer differs from its surviving atom")
    NameValue, ExplicitName = ReadKernelName(NodesValue, Attributes)
    if (
        ExplicitName is not None
        or AtomFields.get("f18") is not None
        or AtomFields.get("f18c") != 1
        or NameValue != ReadNativeName(ProducerValue)
    ):
        raise ValueError("saved stock cache has alternate body name ownership")
    return StockCacheBody(AtomValue, ProducerValue, KernelValue, AtomId, NameValue)
