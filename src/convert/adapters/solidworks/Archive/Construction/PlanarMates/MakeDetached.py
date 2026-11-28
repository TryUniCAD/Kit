from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.EndpointData import (
    EndpointData,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeAbsPlane import (
    MakeAbsPlane,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateContext import (
    MateContext,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.SignedStamp import (
    SignedStamp,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.WrapperFields import (
    WrapperFields,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# detached fallback wrappers own a separate anonymous plane and parent component instead of reusing the resolved selection
def MakeDetached(Endpoint: EndpointData, Context: MateContext) -> ArchiveNode:
    Plane = MakeAbsPlane(
        Context.AssemblyValue, Endpoint.FrameValue, Context.TargetValue
    )
    Component = RequireNode(
        Context.AssemblyValue.FieldsValue.get("f990"), "moUnitComponent_c"
    )
    ReferenceFields = CompRefFields(Component)
    ReferenceFields.update(
        {
            "ff0": {"f00": -1, "f08": 2592000},
            "ff8": Plane,
            "f100": 0,
            "f9c": Endpoint.DatumId,
        }
    )
    Reference = ArchiveNode(RuntimeClass("moCompRefPlane_c", 1), ReferenceFields)
    Fields = WrapperFields(Reference)
    Fields.update(
        {
            "fd0": dict(
                zip(("x", "y", "z"), Endpoint.FrameValue.OriginValue, strict=True)
            ),
            "fe8": dict(
                zip(("x", "y", "z"), Endpoint.FrameValue.NormalValue, strict=True)
            ),
            "f100": IdentityXform(),
            "f08": SignedStamp(FieldInt(Context.HeaderValue.FieldsValue, "f40")),
            "f0c": FieldInt(Context.ConfigValue.FieldsValue, "f08"),
            "f68": 1,
            "f188": dict.fromkeys(("x", "y", "z"), 0.0),
        }
    )
    Fields.update(dict.fromkeys(("fb0", "fb8", "fc0", "fc8"), 0.0))
    return ArchiveNode(RuntimeClass("moPlaneRef_w", 1), Fields)
