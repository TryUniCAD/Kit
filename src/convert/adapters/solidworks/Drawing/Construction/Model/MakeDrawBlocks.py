from uuid import UUID as UuidValue

from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.System.ClearSystemMut import (
    ClearSystemMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# empty block managers need their own fresh identity and actual map backlink rather than a shared template identifier
def MakeDrawBlocks(
    OwnerValue: ArchiveNode,
    TargetValue: FeatureTarget,
    BlockValue: UuidValue,
    CreatedAt: int,
    NameValue: str,
) -> ArchiveNode:
    RequireRootNode(OwnerValue, "moDrawing_c")
    if type(BlockValue) is not UuidValue or BlockValue.version != 4:
        raise ValueError("drawing root block identity requires uuid4")
    NodeValue = ArchiveNode(RuntimeClass("moSketchBlockMgr_c", 1), {})
    InitFeatureMut(NodeValue, NameValue, OwnerValue, TargetValue)
    NodeValue.FieldsValue.update(
        {
            "f18": None,
            "f380": BlockValue.bytes_le,
            **FeatureTime(CreatedAt),
            "blocks": {
                "f18": 0,
                "f30": NodeValue,
                "n70": 0,
                "f68": (),
                "n98": 0,
                "f90": (),
            },
        }
    )
    ClearSystemMut(NodeValue)
    return NodeValue
