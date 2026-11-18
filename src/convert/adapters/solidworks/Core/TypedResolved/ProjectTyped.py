from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Native import NativeModel, NativeSketch
from convert.adapters.solidworks.Core.TypedResolved.BindCircle import BindCircle
from convert.adapters.solidworks.Core.TypedResolved.BindExtrude import (
    BindDepth,
    BindExtrude,
)
from convert.adapters.solidworks.Core.TypedResolved.BindFeature import BindFeature
from convert.adapters.solidworks.Core.TypedResolved.Circles.BindLocalCirc import (
    BindLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutHistory import (
    ReadCutHistory,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.Lines.BindLineLoop import (
    BindLineLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ProjectTree import (
    ProjectTree,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReportTyped import ReportTyped


# the public model must consume complete typed facts atomically while preserving unrelated legacy behavior
def ProjectTyped(Model: NativeModel, LinkValue: NativeLink) -> NativeModel:
    NodesValue = IndexFeatures(LinkValue)
    Features = {
        Feature.object_id: (
            BindFeature(Feature, NodesValue[Feature.object_id], LinkValue)
            if Feature.object_id in NodesValue
            else Feature
        )
        for Feature in Model.features
    }
    OwnersValue = {
        NativeId: ReadExtrude(LinkValue, NodeValue, NodesValue)
        for NativeId, NodeValue in NodesValue.items()
        if NativeId in Features and NodeValue.ClassValue.NameValue == "moExtrusion_c"
    }
    SketchIds = {Sketch.object_id for Sketch in Model.sketches}
    OperationIds = {Operation.object_id for Operation in Model.operations}
    BodyEvidence = None
    CutProfileId = None
    if OwnersValue and len(Model.operations) != 1:
        CutValue, BodyEvidence = ReadCutHistory(
            Model, LinkValue, NodesValue, OwnersValue
        )
        OwnersValue[NativeNodeId(CutValue.NodeValue)] = CutValue
        CutProfileId = NativeNodeId(CutValue.ProfileValue)
    if any(
        NativeId not in OperationIds
        or NativeNodeId(OwnerValue.ProfileValue) not in SketchIds
        for NativeId, OwnerValue in OwnersValue.items()
    ):
        raise ValueError("typed blind owner lacks its public operation or sketch")
    Features.update(
        {
            NativeId: BindDepth(Features[NativeId], OwnerValue)
            for NativeId, OwnerValue in OwnersValue.items()
        }
    )
    Operations = tuple(
        ReplaceValue(
            (
                BindExtrude(Operation, OwnersValue[Operation.object_id])
                if Operation.object_id in OwnersValue
                else Operation
            ),
            name=Features[Operation.object_id].name,
        )
        for Operation in Model.operations
    )
    Circles: dict[int, NativeSketch] = {}
    Lines: dict[int, NativeSketch] = {}
    for Sketch in Model.sketches:
        NodeValue = NodesValue.get(Sketch.object_id)
        if NodeValue is None or NodeValue.ClassValue.NameValue != "moProfileFeature_c":
            continue
        LineValue = BindLineLoop(Sketch, NodeValue, LinkValue)
        if LineValue is not None:
            Lines[Sketch.object_id] = LineValue
            Features[Sketch.object_id] = ReplaceValue(
                Features[Sketch.object_id], dimensions=LineValue.dimensions
            )
            continue
        Circle = BindCircle(Sketch, NodeValue, LinkValue) or BindLocalCirc(
            Sketch, NodeValue, LinkValue, AllowFree=Sketch.object_id == CutProfileId
        )
        if Circle is not None:
            Circles[Sketch.object_id] = Circle
            Features[Sketch.object_id] = ReplaceValue(
                Features[Sketch.object_id], dimensions=Circle.dimensions
            )
    TreeValue = ProjectTree(Model, LinkValue, NodesValue, Features)
    return ReplaceValue(
        Model,
        features=TreeValue.FeaturesValue,
        operations=Operations,
        sketches=tuple(
            ReplaceValue(
                Lines.get(Sketch.object_id, Circles.get(Sketch.object_id, Sketch)),
                name=Features[Sketch.object_id].name,
            )
            for Sketch in Model.sketches
        ),
        planes=tuple(
            ReplaceValue(Plane, name=Features[Plane.object_id].name)
            for Plane in Model.planes
        ),
        TypedGraph={
            **ReportTyped(
                Model,
                LinkValue,
                NodesValue,
                OwnersValue,
                tuple(Key for Key, Value in Circles.items() if Value.dimensions),
                tuple(Lines),
                BodyEvidence,
                tuple(Key for Key, Value in Circles.items() if not Value.dimensions),
            ),
            "native_tree": TreeValue.EvidenceValue,
            **(
                {
                    "line_dimension_profiles": tuple(
                        SketchId
                        for SketchId, SketchValue in Lines.items()
                        if SketchValue.dimensions
                    )
                }
                if any(SketchValue.dimensions for SketchValue in Lines.values())
                else {}
            ),
        },
    )
