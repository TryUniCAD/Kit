from math import isfinite

from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import PrincipalFrame
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeBoundRoot import (
    KLocalLinearResolution, KLocalSessionPrecision,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakePrismNodes import MakePrismNodes
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismCell import PrismCell, PrismRef
from convert.adapters.solidworks.Archive.Partition.LocalPrism.PrismRootKeys import KPrismBody
from SweepModel import require
from SweepSectionTransport import encode_section_nodes


def make_path_wire(radius):
    require(type(radius) in (int, float) and isfinite(radius) and 0.001 <= radius <= 0.15,
            "path radius exceeds the measured positive quarter-arc range")
    frame = PrincipalFrame("z")
    shell, region = PrismRef(13, "path-shell"), PrismRef(19, "path-region")
    edge, curve = PrismRef(16, "path-edge"), PrismRef(31, "path-circle")
    end, start = PrismRef(18, "path-end"), PrismRef(18, "path-start")
    end_pt, start_pt = PrismRef(29, "path-end-point"), PrismRef(29, "path-start-point")
    positive, negative = PrismRef(17, "path-positive-fin"), PrismRef(17, "path-negative-fin")
    cells = (
        PrismCell(KPrismBody, {
            "shell": shell, "region": region, "edge": 0, "vertex": end, "boundary_point": end_pt,
            "boundary_curve": curve, "boundary_surface": 0, "body_type": 2, "state": 1, "nom_geom_state": 1,
            "res_size": KLocalLinearResolution / KLocalSessionPrecision, "res_linear": KLocalLinearResolution,
        }),
        PrismCell(region, {"body": KPrismBody, "next": 0, "previous": 0, "shell": shell, "type": "V"}),
        PrismCell(shell, {"body": KPrismBody, "region": region, "face": 0, "front_face": 0, "edge": edge}),
        PrismCell(curve, {"owner": edge, "previous": 0, "next": 0, "sense": "+", "centre": (0.0, radius, 0.0),
                          "normal": frame.NormalValue, "x_axis": frame.AxisU, "radius": float(radius)}),
        PrismCell(end_pt, {"owner": end, "previous": 0, "next": start_pt, "pvec": (radius, radius, 0.0)}),
        PrismCell(start_pt, {"owner": start, "previous": end_pt, "next": 0, "pvec": frame.OriginValue}),
        PrismCell(end, {"halfedge": positive, "previous": 0, "next": start, "point": end_pt, "owner": KPrismBody}),
        PrismCell(start, {"halfedge": negative, "previous": end, "next": 0, "point": start_pt, "owner": KPrismBody}),
        PrismCell(edge, {"halfedge": positive, "previous": 0, "next": 0, "curve": curve, "owner": shell}),
        PrismCell(positive, {"loop": 0, "forward": 0, "backward": 0, "vertex": end, "other": negative,
                             "edge": edge, "next_at_vx": 0, "sense": "+"}),
        PrismCell(negative, {"loop": 0, "forward": 0, "backward": 0, "vertex": start, "other": positive,
                             "edge": edge, "next_at_vx": 0, "sense": "-"}),
    )
    return encode_section_nodes(MakePrismNodes(cells))
