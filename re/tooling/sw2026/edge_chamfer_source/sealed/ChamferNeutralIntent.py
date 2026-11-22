from pathlib import PureWindowsPath

from ChamferModel import values_si
from FilletModel import AXES, edge_role, require, stock


def neutral_intent(case, orientation, locator, epoch):
    require(type(orientation) is list and len(orientation) == 2 and type(orientation[0]) is int
            and orientation[0] in (0, 1) and orientation[1] == "tan",
            "independent side must match the proved ordinary tangent branch")
    destination = PureWindowsPath(locator)
    require(destination.is_absolute() and destination.drive.casefold() == "c:"
            and ".." not in destination.parts and destination.name == case["name"] + ".SLDPRT",
            "neutral candidate requires its exact local output locator")
    sizes, bounds = stock(case)
    _, axis, transverse, _, _ = edge_role(case)
    first = transverse[orientation[0]]
    second = transverse[1 - orientation[0]]
    corner = {str(AXES.index(key)): int(value == "max") for key, value in case["corner"].items()}
    u, v = (tuple(float(2 * corner[str(side)] - 1) if index == side else 0.0 for index in range(3))
            for side in (first, second))
    normal = tuple(u[(i + 1) % 3] * v[(i + 2) % 3] - u[(i + 2) % 3] * v[(i + 1) % 3]
                   for i in range(3))
    distance, angle = values_si(case, False)
    view = "Chamfer Driver View"
    return {"origin_mm": list(case["center_mm"]),
            "request": {"case": case["name"], "size_mm": case["size_mm"],
                        "feature": "DistanceAngleEdgeChamfer", "epoch": epoch, "locator": str(destination),
                        "shape": {"body_id": "body/boss", "stock_bounds_m": [list(pair) for pair in bounds],
                                  "edge_axis": axis, "corner": corner, "distance_axis": first,
                                  "distance_m": distance, "angle_rad": angle},
                        "catalog": [{"name": view, "basis": [u, v, normal]}],
                        "presentation": {"view": view, "distance_text": [1.375, min(sizes) / 5],
                                         "angle_text_xy_m": [0.0, -min(sizes) / 3],
                                         "witness_length_m": min(sizes) / 4, "design_intent": False,
                                         "selected_leaders": [-2, -3]}}}
