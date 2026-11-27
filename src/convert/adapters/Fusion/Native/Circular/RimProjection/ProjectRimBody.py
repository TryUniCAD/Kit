from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Circular.RimFillet.CheckRimMass import CheckRimMass
from convert.adapters.Fusion.Native.Graph.GraphValues import TextValue
from convert.Geometry.Fillet.Circular.BuildRimFillet import BuildRimFillet
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.FeatureBody import DesignBody
from interchange.Records.RecordTopology import TopologyCounts


# the final body must be generated from the selected profile and bound fillet radius
def ProjectRimBody(
    Context: RimContext, Radius: float, Height: float, Fillet: float, MaterialId: str
) -> tuple[BrepModel, DesignBody]:
    Geometry, Volume, AreaValue, Center, Bounds = BuildRimFillet(
        Context.Extrusion.BodyNode.Identity, Radius, Height, Fillet
    )
    CheckRimMass(Context, Radius, Height, Fillet)
    Counts = TopologyCounts(
        1,
        len(Geometry.shells),
        len(Geometry.faces),
        len(Geometry.edges),
        len(Geometry.vertices),
        Volume,
        AreaValue,
        Bounds,
        True,
    )
    return Geometry, DesignBody(
        Context.Extrusion.BodyNode.Identity,
        TextValue(Context.Extrusion.BodyNode.Fields["userName"]),
        Context.Feature.Identity,
        Counts,
        MaterialId,
        attributes={
            "creation_index": Context.Extrusion.BodyNode.Fields["creationIndex"],
            "analytic_centroid_mm": (Center.x, Center.y, Center.z),
        },
    )
