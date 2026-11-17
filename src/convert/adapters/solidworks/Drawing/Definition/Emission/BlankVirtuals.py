from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedVirtuals import (
    KResolvedVirtuals,
)

# drawing feature inheritance must select actual lightweight resolved and xml serializer owners
KBlankVirtuals = MappingProxyType(
    {
        **KResolvedVirtuals,
        **{
            (ClassName, SlotValue): TargetValue
            for ClassName in (
                "moDrSheet",
                "moDetailFolder_c",
                "moBlockFolder_c",
                "moMarkupCommentFolder_c",
            )
            for SlotValue, TargetValue in (
                (1208, "moConcept_c.SerializeLWData"),
                (1216, "moConcept_c.SerializeResolvedData"),
                (1016, True),
                (1000, "moFeature_c.SerializeXmlData"),
            )
        },
    }
)
