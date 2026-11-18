from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.LocalCircle import (
    LocalCircle,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPublicPlanes import (
    CheckPublicPlanes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a pocket solid is reconstructed only when the public history exposes both complete typed profiles and their actual support
def CheckPublicPocket(
    ModelValue: NativeModel, Features: Mapping[int, ArchiveNode]
) -> tuple[LocalCircle, float]:
    Evidence = NativeRecord(ModelValue.TypedGraph.get("cut_body_dependency"))
    if (
        Evidence.get("binding") != "cold_all_bodies_intersection"
        or ModelValue.active_configuration_id != 0
        or len(ModelValue.configurations) != 1
        or ModelValue.equations
        or {Feature.object_id for Feature in ModelValue.features} != set(Features)
        or len(ModelValue.operations) != 2
        or len(ModelValue.sketches) != 2
    ):
        raise ValueError("cache free pocket lacks its full public feature inventory")
    Boss, Cut = ModelValue.operations
    Stock, Cavity = ModelValue.sketches
    if (
        Boss.object_id != Evidence.get("producer_feature_id")
        or Cut.object_id != Evidence.get("consumer_feature_id")
        or Boss.profile_id != Stock.object_id
        or Cut.profile_id != Cavity.object_id
        or Stock.TypedLines is None
        or Cavity.TypedCircle is None
        or Cut.length_mm is None
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
    CheckPublicPlanes(ModelValue, Features)
    return Cavity.TypedCircle, Cut.length_mm
