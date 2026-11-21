from dataclasses import replace as ReplaceValue

from convert.Geometry.Revolve.SweepModel import BuildSweepModel
from interchange.brep.Topology.BrepModel import BrepModel


# disjoint raised profiles share their lower rims with holes in the plate upper face
def JoinRaised(
    BodyId: str, PlateValue: BrepModel, RaisedValues: tuple[BrepModel, ...]
) -> BrepModel:
    TopValue = PlateValue.faces[1]
    RimsValue = tuple(ModelValue.loops[0] for ModelValue in RaisedValues)
    TopLoops = TopValue.loop_ids + tuple(LoopValue.id for LoopValue in RimsValue)
    TopFace = ReplaceValue(TopValue, loop_ids=TopLoops)
    ModelsValue = (PlateValue, *RaisedValues)
    return BuildSweepModel(
        BodyId,
        f"{BodyId}-raised",
        tuple(Curve for ModelValue in ModelsValue for Curve in ModelValue.curves),
        PlateValue.surfaces
        + tuple(
            Surface
            for ModelValue in RaisedValues
            for Surface in ModelValue.surfaces[1:]
        ),
        tuple(Vertex for ModelValue in ModelsValue for Vertex in ModelValue.vertices),
        tuple(
            EdgeValue for ModelValue in ModelsValue for EdgeValue in ModelValue.edges
        ),
        (PlateValue.faces[0], TopFace, *PlateValue.faces[2:])
        + tuple(
            FaceValue
            for ModelValue in RaisedValues
            for FaceValue in ModelValue.faces[1:]
        ),
        PlateValue.loops
        + tuple(ReplaceValue(LoopValue, outer=False) for LoopValue in RimsValue)
        + tuple(
            LoopValue
            for ModelValue in RaisedValues
            for LoopValue in ModelValue.loops[1:]
        ),
        tuple(Coedge for ModelValue in ModelsValue for Coedge in ModelValue.coedges),
    )
