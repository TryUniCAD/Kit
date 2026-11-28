from dataclasses import replace as ReplaceValue

from convert.Commands.CheckRetained import CheckRetained
from convert.adapters.registry.NativeWrite import CheckNative
from convert.adapters.solidworks.Core.Preparation.Chamfers.MakeChmfSnap import (
    MakeChmfSnap,
)
from interchange import CadDocument
from interchange.Features.FeatureKinds import NativeFeature


# only a fully checked chamfer snapshot can defer the native row and retained bytes gates to json export
def CheckJsonNative(Document: CadDocument) -> CadDocument:
    Snapshot = MakeChmfSnap(Document)
    if Snapshot is None:
        CheckNative(Document)
        return Document
    CheckRetained(Snapshot)
    CheckNative(
        ReplaceValue(
            Snapshot,
            feature_timeline=tuple(
                Value
                for Value in Snapshot.feature_timeline
                if not isinstance(Value.definition, NativeFeature)
            ),
        )
    )
    return Snapshot
