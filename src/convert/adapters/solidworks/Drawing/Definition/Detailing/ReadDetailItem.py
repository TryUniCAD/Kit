from convert.adapters.solidworks.Drawing.Definition.Detailing.DetailEntry import (
    DetailEntry,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailMap import (
    NeedDetailMap,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailNode import (
    NeedDetailNode,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.NeedDetailText import (
    NeedDetailText,
)
from convert.adapters.solidworks.Drawing.Definition.Detailing.ReadDownstream import (
    ReadDownstream,
)


# detailing rows must keep concrete edge references and their separate native lookup identities
def ReadDetailItem(Value: object) -> DetailEntry:
    FieldsValue = NeedDetailMap(Value)
    return DetailEntry(
        NeedDetailText(FieldsValue.get("name")),
        ReadDownstream(FieldsValue.get("key")),
        NeedDetailNode(FieldsValue.get("ref"), "moEdgeRef_c"),
    )
