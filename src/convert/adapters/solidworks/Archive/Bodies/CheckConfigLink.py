from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# final cyclic ownership must be verified after all containing occurrence fields are assigned
def CheckConfigLink(ContextValue: BodyContext) -> None:
    for NodeValue in ContextValue.PendingNodes:
        Reference = ArchiveNode.RequireNode(NodeValue.FieldsValue["f50"])
        if Reference.FieldsValue.get(
            "f4f8"
        ) is not NodeValue or NodeValue.FieldsValue.get(
            "f44"
        ) != Reference.FieldsValue.get(
            "f08"
        ):
            raise BodyUnsupported(
                "configuration external feature has an inconsistent occurrence backlink or identifier"
            )
