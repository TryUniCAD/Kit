# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.features.FeatureStep import FeatureStep
from interchange.records.RecordParameter import Parameter
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane


# document lookup methods preserve convenient access without owning collection storage
class DocumentLookup:
    locals()["__slots__"] = ()

    # parameter lookup remains discoverable without coupling storage to callers
    def GetParameter(SelfValue, EntityId: str) -> Parameter:
        from interchange.document.behavior.DocumentLookup import GetParameter

        return GetParameter(SelfValue, EntityId)

    # sketch lookup remains discoverable without coupling storage to callers
    def GetSketch(SelfValue, EntityId: str) -> Sketch:
        from interchange.document.behavior.DocumentLookup import GetSketch

        return GetSketch(SelfValue, EntityId)

    # feature lookup remains discoverable without coupling timeline storage to callers
    def GetFeature(SelfValue, EntityId: str) -> FeatureStep:
        from interchange.document.behavior.DocumentLookup import GetFeature

        return GetFeature(SelfValue, EntityId)

    # plane lookup remains discoverable without coupling support storage to callers
    def GetPlane(SelfValue, EntityId: str) -> SupportPlane:
        from interchange.document.behavior.DocumentLookup import GetPlane

        return GetPlane(SelfValue, EntityId)
