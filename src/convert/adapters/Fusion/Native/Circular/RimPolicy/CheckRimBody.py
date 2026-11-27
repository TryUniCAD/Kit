from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from convert.adapters.Fusion.Native.Graph.GraphChecks import EmptyFields, RequireFields
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields
from convert.adapters.Fusion.Native.Graph.NativeGraph import NativeGraph


# an unchanged body identity must survive the modifying feature without accepting overridden physical properties
def CheckRimBody(Graph: NativeGraph, Context: RimContext) -> None:
    Extrusion = Context.Extrusion
    for Value in (Extrusion.Component, Extrusion.BodyNode):
        if any(
            Amount != -1
            for Amount in ObjectFields(Value.Fields["massProperties"]).values()
        ):
            raise ValueError("Native rim mass overrides are not qualified")
    EmptyFields(Extrusion.BodyNode, ("faceVisualMaterialByAttrTagID",))
    RequireFields(Extrusion.DcBody, {"isEliminated": False})
    if (
        Graph.Resolve(Extrusion.DcBody.Fields["rOwnFeature"]) != Extrusion.Extrude
        or Graph.Resolve(Extrusion.DcBody.Fields["rParent"]) != Extrusion.Fragment
    ):
        raise ValueError("Native rim body ownership differs from its extrusion")
    if (
        Extrusion.BodyNode.Fields["persistentId"] != Extrusion.DcBody.Fields["bodyUuid"]
        or Extrusion.BodyNode.Fields["persistentId"]
        != Graph.OneClass("BodyProgenitor").Fields["bodyUuid"]
    ):
        raise ValueError("Native rim body persistent identities disagree")
