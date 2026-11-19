from collections.abc import Mapping
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicPlanes import (
    CheckPublicPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# reconstructed circle solids require the public history to retain every feature and the same typed circle boss and support owners
def CheckCircPublic(
    ModelValue: NativeModel,
    Features: Mapping[int, ArchiveNode],
    OwnerValue: ExtrudeOwner,
    CircleValue: LocalCircle,
) -> None:
    if (
        ModelValue.TypedGraph.get("status") != "supplemented"
        or len(ModelValue.features) != len(Features)
        or {Feature.object_id for Feature in ModelValue.features} != set(Features)
    ):
        raise ValueError(
            "cache free circle lacks complete typed public feature ownership"
        )
    if len(ModelValue.operations) != 1 or len(ModelValue.sketches) != 1:
        raise ValueError("cache free circle lacks its one public boss and sketch")
    Operation = ModelValue.operations[0]
    SketchValue = ModelValue.sketches[0]
    if (
        Operation.kind != "join"
        or Operation.object_id != NativeNodeId(OwnerValue.NodeValue)
        or Operation.profile_id != NativeNodeId(OwnerValue.ProfileValue)
        or SketchValue.object_id != NativeNodeId(OwnerValue.ProfileValue)
        or SketchValue.TypedCircle != CircleValue
    ):
        raise ValueError(
            "cache free circle public geometry differs from its actual owners"
        )
    Reference = RequireNative(
        OwnerValue.ProfileValue.FieldsValue.get("pd_f78"), "moCompRefPlane_c"
    )
    if (
        SketchValue.support_plane_id
        != NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
        or Operation.direction_code != int(OwnerValue.IsReversed)
        or Operation.extrusion_end != OwnerValue.ModeValue
    ):
        raise ValueError("cache free circle public support or direction differs")
    CheckPublicPlanes(ModelValue, Features)
