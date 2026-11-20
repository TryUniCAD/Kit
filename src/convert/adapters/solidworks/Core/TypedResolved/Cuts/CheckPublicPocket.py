from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel, NativeOperation
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicPlanes import (
    CheckPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.Features.FeatureExtrude import ExtrudeEnd


# a pocket solid is reconstructed only when the public history exposes both complete typed profiles and their actual support
def CheckPocket(
    ModelValue: NativeModel, Features: Mapping[int, ArchiveNode]
) -> tuple[LocalCircle, NativeOperation]:
    Evidence = NativeRecord(ModelValue.TypedGraph.get("cut_body_dependency"))
    if (
        Evidence.get("binding")
        not in ("cold_all_bodies_intersection", "cold_selected_stock_atom")
        or ModelValue.active_configuration_id != 0
        or len(ModelValue.configurations) != 1
        or ModelValue.equations
        or {Feature.object_id for Feature in ModelValue.features} != set(Features)
        or len(ModelValue.operations) != 2
        or len(ModelValue.sketches) != 2
    ):
        raise ValueError("cache free pocket lacks its full public feature inventory")
    BossOperation, CutOperation = ModelValue.operations
    Stock, Cavity = ModelValue.sketches
    if (
        BossOperation.object_id != Evidence.get("producer_feature_id")
        or CutOperation.object_id != Evidence.get("consumer_feature_id")
        or BossOperation.profile_id != Stock.object_id
        or CutOperation.profile_id != Cavity.object_id
        or Stock.TypedLines is None
        or Cavity.TypedCircle is None
        or (
            CutOperation.length_mm is None
            and CutOperation.extrusion_end != ExtrudeEnd.KThroughAll
        )
    ):
        raise ValueError(
            "cache free pocket lacks its actual public contour and depth owners"
        )
    for Sketch in (Stock, Cavity):
        Profile = RequireNative(Features[Sketch.object_id], "moProfileFeature_c")
        Reference = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
        if Sketch.support_plane_id != NativeRecord(
            Reference.FieldsValue.get("ff0")
        ).get("f00"):
            raise ValueError(
                "cache free pocket public support differs from its native datum"
            )
    CheckPlanes(ModelValue, Features)
    return Cavity.TypedCircle, CutOperation
