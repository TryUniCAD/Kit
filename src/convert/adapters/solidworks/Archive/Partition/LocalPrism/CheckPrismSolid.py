from itertools import chain as ChainValues

from interchange.brep.Topology.BrepModel import BrepModel
from interchange.brep.Validation.BrepValidate import GetBrepErrors
from interchange.geometry.Models.Transform import KTransformIdentity


# a bare local transmit owns only one portable solid with no carried native state
def CheckPrismSolid(ModelValue: BrepModel, *, AllowReverse: bool = False) -> None:
    if type(ModelValue) is not BrepModel or ModelValue.schema_version != "1.0":
        raise ValueError("local prism requires a typed neutral B-rep")
    if (
        any(
            len(Values) != 1
            for Values in (
                ModelValue.bodies,
                ModelValue.regions,
                ModelValue.shells,
                ModelValue.shell_uses,
            )
        )
        or ModelValue.wires
        or ModelValue.pcurves
    ):
        raise ValueError(
            "local prism requires one solid shell without wires or pcurves"
        )
    ErrorsValue = GetBrepErrors(ModelValue, frozenset())
    if ErrorsValue:
        raise ValueError("invalid local prism B-rep: " + "; ".join(ErrorsValue))
    BodyValue, RegionValue, ShellValue, UseValue = (
        ModelValue.bodies[0],
        ModelValue.regions[0],
        ModelValue.shells[0],
        ModelValue.shell_uses[0],
    )
    if (
        BodyValue.transform != KTransformIdentity
        or BodyValue.design_body_id
        or BodyValue.wire_ids
        or BodyValue.vertex_ids
        or BodyValue.region_ids != (RegionValue.id,)
        or RegionValue.shell_use_ids != (UseValue.id,)
        or UseValue.shell_id != ShellValue.id
        or UseValue.reversed
        or not RegionValue.solid
        or not ShellValue.closed
        or not AllowReverse
        and any(UseValue.reversed for UseValue in ModelValue.face_uses)
    ):
        raise ValueError("local prism requires an untransformed outward solid shell")
    CheckBareCells(ModelValue)


# geometry records with additional ownership cannot enter a bare local transmit
def CheckBareCells(ModelValue: BrepModel) -> None:
    if any(
        EntityValue.Attributes or EntityValue.Provenance is not None
        for EntityValue in ChainValues(
            ModelValue.curves,
            ModelValue.surfaces,
            ModelValue.vertices,
            ModelValue.edges,
            ModelValue.coedges,
            ModelValue.loops,
            ModelValue.faces,
            ModelValue.face_uses,
            ModelValue.shells,
            ModelValue.shell_uses,
            ModelValue.regions,
            ModelValue.bodies,
        )
    ):
        raise ValueError("local prism does not admit geometry attributes or provenance")
    if (
        any(VertexValue.tolerance for VertexValue in ModelValue.vertices)
        or any(
            EdgeValue.tolerance or EdgeValue.degenerate
            for EdgeValue in ModelValue.edges
        )
        or any(FaceValue.tolerance for FaceValue in ModelValue.faces)
    ):
        raise ValueError(
            "local prism does not admit local tolerances or degenerate edges"
        )
