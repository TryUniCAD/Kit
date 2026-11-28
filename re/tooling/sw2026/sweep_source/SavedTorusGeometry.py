from math import atan2, cos, dist, hypot, isclose, pi, sin, ulp

from convert.Geometry.Parasolid import AnalyticGeom, DecodePartData, NativeId
from convert.Geometry.SweptTube.QuarterMetric import MeasureQuarter
from convert.adapters.solidworks.Container.Format import KPartitionStream
from convert.adapters.solidworks.Container.Parasolid import decode_brep_model
from convert.adapters.solidworks.Core.Partition.CircularPartition import ReadShellAtom
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwArc import CheckSwRules, ReadSwArc, SwArcPoints
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwDriver import ReadSwDriver
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwRow import ReadSwRow
from SavedTorusActive import demand

UNIT_TOL = 64 * ulp(1.0)


def dot(left, right):
    return sum(a * b for a, b in zip(left, right, strict=True))


def cross(left, right):
    x, y, z = left
    a, b, c = right
    return y * c - z * b, z * a - x * c, x * b - y * a


def add(left, right, factor=1.0):
    return tuple(a + factor * b for a, b in zip(left, right, strict=True))


def vector(value):
    return value.x, value.y, value.z


def aligned_sign(left, right):
    relation = dot(left, right)
    demand(abs(abs(relation) - 1.0) <= UNIT_TOL, "saved carrier directions are not parallel")
    return -1 if relation < 0 else 1


def rim_trim(torus, rim):
    cap, face, curve, edge, cap_fin, wall_fin = rim
    torus, cap, curve = (node.FieldsValue for node in (torus, cap, curve))
    demand(torus["sense"] == cap["sense"] == curve["sense"] == "+"
           and curve["radius"] == torus["minor_radius"], "unexpected saved carrier orientation or rim radius")
    major, minor = torus["major_radius"], torus["minor_radius"]
    length_tol = 64 * ulp(major)
    axial, radial_zero, center = torus["axis"], torus["x_axis"], torus["centre"]
    radial_quarter = cross(axial, radial_zero)
    cap_center = cap["pvec"]
    center_offset = add(cap_center, center, -1)
    u = atan2(dot(center_offset, radial_quarter), dot(center_offset, radial_zero))
    radial = add(scale(radial_zero, cos(u)), radial_quarter, sin(u))
    tangent = cross(axial, radial)
    outward = scale(cap["normal"], 1 if face.String("sense") == "+" else -1)
    outward_du_sign = aligned_sign(outward, tangent)
    demand(dist(add(center, radial, major), cap_center) <= length_tol
           and dist(cap_center, curve["centre"]) <= length_tol,
           "saved rim is not the complete circle at its torus meridian")
    meridian_sign = aligned_sign(curve["normal"], cross(radial, axial))
    cap_chart_sign = aligned_sign(curve["normal"], cap["normal"])
    cap_direction = cap_chart_sign * (1 if cap_fin.String("sense") == "+" else -1)
    wall_direction = meridian_sign * (1 if wall_fin.String("sense") == "+" else -1)
    demand(abs(dot(curve["x_axis"], tangent)) <= UNIT_TOL
           and cap_direction == (1 if face.String("sense") == "+" else -1)
           and wall_direction == outward_du_sign, "saved boundary orientation disagrees with face sense")
    v_start = atan2(dot(curve["x_axis"], axial), dot(curve["x_axis"], radial))
    for quarter in (0, 1, 2, 3):
        theta = quarter * pi / 2
        point_direction = add(scale(curve["x_axis"], cos(theta)), cross(curve["normal"], curve["x_axis"]), sin(theta))
        v = v_start + meridian_sign * theta
        meridian_direction = add(scale(radial, cos(v)), axial, sin(v))
        demand(dist(add(curve["centre"], point_direction, minor),
                    add(add(center, radial, major), meridian_direction, minor)) <= length_tol,
               "signed analytic rim parametrization differs from the actual circular carrier")
    return {"edge": edge.IndexValue, "curve": rim[2].IndexValue, "cap_face": face.IndexValue,
            "cap_fin": cap_fin.IndexValue, "side_fin": wall_fin.IndexValue, "u": u, "v_at_curve_zero": v_start,
            "curve_to_torus_v": meridian_sign, "wall_fin_dv": wall_direction,
            "cap_fin_dangle": cap_direction, "outward_dot_du_sign": outward_du_sign,
            "cap_center_m": cap_center, "outward": outward}


def scale(value, factor):
    return tuple(item * factor for item in value)


def result_geometry(archive, torus, rims, topology, drivers, native):
    packet, _ = DecodePartData(archive.require(KPartitionStream), KPartitionStream)
    legacy = decode_brep_model(packet.data)
    physical = ReadShellAtom(packet.data, legacy)
    demand(tuple(physical[key] for key in ("native_owner", "native_region", "native_shell"))
           == tuple(1 + topology[key] for key in ("body", "region", "shell"))
           and physical["body_atom_id"] == topology["atom"], "legacy and typed shell owners differ")
    fields = torus.FieldsValue
    name = NativeId("surface", torus.IndexValue + 1)
    analytic = AnalyticGeom(54, name, (*fields["centre"], *fields["axis"], fields["major_radius"],
                                      fields["minor_radius"], *fields["x_axis"]))
    (prior,) = (value for value in legacy.surfaces if value.id == name)
    demand(analytic is not None and (
        analytic.center, analytic.axis, analytic.reference_direction, analytic.major_radius, analytic.minor_radius
    ) == (prior.center, prior.axis, prior.reference_direction, prior.major_radius, prior.minor_radius),
        "shared analytic projection disagrees with the actual typed torus")
    major, minor = fields["major_radius"], fields["minor_radius"]
    demand((major, minor) == (drivers[1], drivers[0] / 2) and 0 < minor < major
           and fields["centre"] == (0.0, major, 0.0)
           and fields["axis"] == (0.0, 0.0, 1.0) and fields["x_axis"] == (1.0, 0.0, 0.0),
           "stored raw result parameters disagree with the live signed sweep")
    trims = sorted((rim_trim(torus, rim) for rim in rims), key=lambda row: row["u"])
    start, end = trims
    demand(abs(start["u"] + pi / 2) <= UNIT_TOL and abs(end["u"]) <= UNIT_TOL
           and (start["outward_dot_du_sign"], end["outward_dot_du_sign"]) == (-1, 1)
           and dist(start["cap_center_m"], (0.0, 0.0, 0.0)) <= 64 * ulp(major)
           and dist(end["cap_center_m"], (major, major, 0.0)) <= 64 * ulp(major),
           "oriented caps do not bound the actual quarter sweep")
    measures = measured_geometry(minor, major, topology["density"], native)
    return {"radii_m": (major, minor), "torus_center_m": fields["centre"],
            "torus_axis": fields["axis"], "torus_reference": fields["x_axis"],
            "signed_rims": trims, "measures": measures, "shared_geometry_matches": True}


def measured_geometry(minor, major, density, native):
    metric = MeasureQuarter(minor, major)
    expected = {"volume": metric.VolumeValue, "area": metric.AreaValue, "com": vector(metric.CenterValue),
                "mass": density * metric.VolumeValue}
    facts = native["mass"]
    for key in ("volume", "area", "mass"):
        demand(isclose(expected[key], facts[key], rel_tol=5e-7), f"native {key} differs from owned geometry")
    demand(all(isclose(a, b, rel_tol=5e-7, abs_tol=1e-16) for a, b in zip(expected["com"], facts["com"], strict=True)),
           "native centroid differs from the signed quarter geometry")
    demand(native["bodies"] == {"solid": 1, "sheet": 0}, "native topology has another body")
    cap, side = pi * minor**2, pi**2 * major * minor
    areas = (cap, cap, side)
    demand(all(row["producer"] == "OrdinarySweptBoss" and row["torus"] == (index == 2)
               and isclose(row["area_m2"], area, rel_tol=5e-7)
               for index, (row, area) in enumerate(zip(native["faces"], areas, strict=True))),
           "native cap or torus face differs from the physical result")
    return {"analytic": expected, "native": facts,
            "bounds_m": (vector(metric.BoundsValue.minimum), vector(metric.BoundsValue.maximum)),
            "native_face_areas_m2": [row["area_m2"] for row in native["faces"]]}


def saved_profiles(config, resolved, sweep, drivers):
    earlier = {NativeNodeId(node): node for node in resolved.RootsValue}
    section, path = ReadParents(sweep)
    observations = []
    for index, feature in enumerate((section, path)):
        is_section = index == 0
        support = feature.FieldsValue["pd_f78"].FieldsValue["ff0"]["f00"]
        frame = ReadPrismFrame(feature, config.RootValue, earlier, FrontOnly=False)
        demand(ReadNativeName(earlier[support]) == ("Right Plane" if is_section else "Front Plane")
               and vector(frame.origin) == (0.0, 0.0, 0.0)
               and vector(frame.z_axis) == ((1.0, 0.0, 0.0) if is_section else (0.0, 0.0, 1.0)),
               "saved sweep profile changed its signed support")
        sketch = feature.FieldsValue["pd_f80"]
        driver = ReadSwDriver(sketch, is_section)
        demand(driver.MetresValue == drivers[index], "saved sweep changed its driving parameter")
        if not is_section:
            ReadSwArc(sketch, driver.MetresValue, False)
            observations.append({"feature": NativeNodeId(feature), "dimension": driver.NativeId,
                                 "radius_m": driver.MetresValue, "axis": vector(frame.z_axis)})
            continue
        observations.append(section_seam(sketch, feature, frame, driver))
    return observations


def section_seam(sketch, feature, frame, driver):
    fields = sketch.FieldsValue
    arc = ReadSwRow(fields, "narcs", "arcs", "arc")
    rows = fields["points"]
    demand((arc["fd8"], arc["fdc_s"], arc["fc8_s"], arc["fcc_s"]) == (1, 0, 1, 1)
           and len(rows) == 2 and all(set(row["point"]["pos"]) == {"x", "y"} for row in rows)
           and not any(fields[name] for name in ("nlines", "nellipses", "nsplines")),
           "saved Section has an alternate arc or indexed incidence")
    center, seam = SwArcPoints(sketch)
    radius = driver.MetresValue / 2
    marks = [row["point"]["f0c"] for row in rows]
    demand((center.x, center.y) == (0.0, 0.0) and hypot(seam.x, seam.y) == radius
           and len(set(marks)) == 2 and min(marks) > 0, "saved seam is not on its actual fixed circle")
    CheckSwRules(sketch, True)
    world = add(add(vector(frame.origin), vector(frame.x_axis), seam.x), vector(frame.y_axis), seam.y)
    return {"feature": NativeNodeId(feature), "dimension": driver.NativeId, "diameter_m": driver.MetresValue,
            "axis": vector(frame.z_axis), "center_index": 0, "same_start_end_index": 1,
            "permanent_marks": marks, "seam_local_m": (seam.x, seam.y),
            "seam_model_m": world, "seam_angle_rad": atan2(seam.y, seam.x)}
