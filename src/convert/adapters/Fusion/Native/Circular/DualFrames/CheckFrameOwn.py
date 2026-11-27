from convert.adapters.Fusion.Native.Graph.ExtrudeContext import ExtrudeContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import (
    EmptyFields,
    RequireFields,
    ResolveField,
)
from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    ObjectFields,
    TextValue,
)
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode


# saved frame definitions require live reciprocal owners and the selected component scope
def CheckFrameOwn(
    Graph: NativeGraph,
    Context: ExtrudeContext,
    Matrix: NativeNode,
    Reference: NativeNode,
) -> None:
    RequireFields(
        Matrix,
        {
            "refType": 2,
            "isZFlip": False,
            "isInferredXAxis": False,
            "isInferredZAxis": False,
            "rOrigin": None,
            "rXAxis": None,
            "rZAxis": None,
            "extraOffset": None,
            "globalReorientParam": None,
            "globalReorientParam1": None,
            "globalParamU": None,
            "globalParamV": None,
            "oldRotation": 0.0,
        },
    )
    EmptyFields(Matrix, ("rEdgeReferences", "rPlaneReferences", "values"))
    for Owner in (Matrix, Reference):
        RequireFields(
            Owner, {"isActive": True, "isEdited": False, "isEliminated": False}
        )
        Update = ResolveField(Graph, Owner, "rDynamicUpdateData", "DynamicUpdateData")
        RequireFields(Update, {"isBodyOK": True, "isPredecessorOK": True})
        if (
            Graph.Resolve(Owner.Fields["rParentFeature"]) != Context.SketchFeature
            or Graph.Resolve(Update.Fields["rOwnerNode"]) != Owner
        ):
            raise ValueError(
                "Native dual frame definition has another feature or update owner"
            )
    Scope = ObjectFields(Reference.Fields["rScope"])
    if (
        Scope["scopeIdType"] != 2
        or Scope["segmentId"] != 0
        or Scope["scopeEntityIdentifier"]
        != TextValue(Context.Component.Fields["persistentId"])
    ):
        raise ValueError(
            "Native dual frame reference scope belongs to another component"
        )
    Instance = Graph.OneClass("ComponentInstance")
    if (
        Graph.Resolve(Instance.Fields["rTargetComponent"]) != Context.Component
        or Instance.Fields["rParent"] is not None
    ):
        raise ValueError("Native dual frame requires the owned root instance")
    CheckIdentity(Instance.Fields["transform"])
    CheckIdentity(Context.Sketch.Fields["occurrenceTransform"])
    if "initialTransform" in Instance.Fields:
        CheckIdentity(Instance.Fields["initialTransform"])
