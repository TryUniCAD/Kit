from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import (
    MakeRootLog,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import (
    FeatureTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# every completed native mate must advance the actual configuration allocation and append one real creation log in both independently rooted headers
def RecordMateMut(
    StateValue: AssemblyState,
    InputValue: AssemblyInput,
    NodeValue: ArchiveNode,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    *,
    CreatedAt: int | None = None,
) -> None:
    if CreatedAt is not None and any(
        NodeValue.FieldsValue.get(FieldName) != FieldValue
        for FieldName, FieldValue in FeatureTime(CreatedAt).items()
    ):
        raise ValueError(
            "mate revision event differs from its actual feature creation time"
        )
    StateValue.CurrentConfig.FieldsValue["f85c"] = StateValue.Allocator.NextValue - 1
    for HeaderValue in HeadersValue:
        LogsValue = ArchiveNode.RequireNode(HeaderValue.FieldsValue["f20"])
        ItemsValue = LogsValue.FieldsValue["items"]
        if not isinstance(ItemsValue, tuple):
            raise ValueError(
                "assembly header lost its actual ordered revision log collection"
            )
        LogsValue.FieldsValue["items"] = (
            *ItemsValue,
            MakeRootLog(NodeValue, InputValue.HeaderValue, CreatedAt=CreatedAt),
        )
        HeaderValue.FieldsValue["f08"] = StateValue.Allocator.NextValue
