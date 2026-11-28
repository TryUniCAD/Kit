from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.AnchorFields import (
    KAnchorFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.WidthDimLayouts import (
    KWidthDimLayouts,
    KWidthDimSchemas,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.PartRelationFields import (
    KPartRelationFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedLayouts import (
    KResolvedLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedSchemas import (
    KResolvedSchemas,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedVirtuals import (
    KResolvedVirtuals,
)

# the local part dimension owners admit the measured sketch graph in the configuration stream
KPartRelationRefClasses = (
    "ParallelPlaneDistanceDim_c",
    "moDisplayDistanceDim_c",
    "moFavoriteHandle_c",
    "moFeatureDimHandle_c",
    "moLengthParameter_c",
    "sgLineHandle",
    "sgPointHandle",
    "sgSketch",
)


# configuration precedence and map ownership must survive reuse of existing dimension serializers
def BindPartRelsMut(ContextValue: BodyContext) -> None:
    if ContextValue.VersionValue != 19000:
        raise BodyUnsupported("part equation archive requires SOLIDWORKS version 19000")
    ContextValue.LayoutsValue = {
        **KResolvedLayouts,
        **ContextValue.LayoutsValue,
        **KPartRelationFields,
        **KAnchorFields,
        **KWidthDimLayouts,
    }
    ContextValue.VirtualValue = {**KResolvedVirtuals, **ContextValue.VirtualValue}
    ContextValue.SchemasValue = {
        **ContextValue.SchemasValue,
        **{
            NameValue: KResolvedSchemas[NameValue]
            for NameValue in KPartRelationRefClasses
        },
        **KWidthDimSchemas,
        **{NameValue: (1,) for NameValue in KPartRelationFields},
    }
    ContextValue.FlagsValue.update(model_is_part=1, part_relations=1)
