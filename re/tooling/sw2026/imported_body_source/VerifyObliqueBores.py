from argparse import ArgumentParser
from dataclasses import replace
from fractions import Fraction
from json import dumps, loads
from math import dist, fsum, inf, nextafter, pi, sqrt, tau
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import sys
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(path) for path in (
    ROOT / "src", ROOT, HERE.parent, HERE.parent.parent, HERE.parent.parent / "serial",
)]

import VerifyLocalBores as principal
from VerifyLocalBores import (
    BareLabels, EncodeLocalBody, MakeAnnularBody, MakeBareImport, ReadLocalCyl, ReadLocalNodes,
    SldprtArchive, SpaceVector, actual_cap, cylinder, document, fingerprint, guard, ordered_payloads,
    read_owners, recipe, refuse, rejected, ring_owners, subtract_straight_bore, support_caps,
)
from convert.Geometry.Revolve.SweepVector import CrossVector
from convert.adapters.solidworks.Container.Format import KLocalBodyStream
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface

MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
PRINCIPAL_SHA = "cc1c3a00165aa07e97fce3ee0da00152252ef7e3bc2a2771e05fa925fa59db73"
SIMPLE_NATIVE_SHA = "7d18092bcf71dc7a10ef179eb9016c0eb56486ea495b4569eaddbb7e8008588c"
AXIAL_ERROR = "does not join its two exact cap stations"
AUTHORED = {
    "ObliqueTwin": (93.75, (2, -1, 2), (1, 0, -1), 15.625, (31.25, -46.875, 15.625),
                    (((15.625, -78.125, 15.625), 11.71875), ((62.5, -46.875, -15.625), 7.8125)),
                    ((2, 0, 1), (1, 2, 0))),
    "ObliqueTriple": (109.375, (-1, -4, 8), (4, -1, 0), 7.8125, (-93.75, 7.8125, 62.5),
                      (((-62.5, 0., 62.5), 9.765625), ((-93.75, 39.0625, 78.125), 13.671875),
                       ((-156.25, 7.8125, 54.6875), 9.765625)),
                      ((3, 1, 0, 2), (0, 2, 1, 3))),
}


def pinned_receipt(name, digest):
    data = (MEASUREMENTS / name).read_bytes()
    assert fingerprint(data)["sha256"] == digest
    return data, loads(data)


def observe():
    previous, evidence = pinned_receipt("PerforatedLocalImport01.json", PRINCIPAL_SHA)
    geography = loads(dumps(principal.observe()))
    assert geography == evidence["native-observation"]
    simple, qualification = pinned_receipt("SdkPublicPeriodicNative01.json", SIMPLE_NATIVE_SHA)
    assert qualification["passed"] and qualification["controls_healthy"]
    assert qualification["oracle_version"] == geography["native_build_of_controls"] == "34.5.2.0604"
    source_axis = qualification["authored_boundary_si"]["axis"]
    assert sum(abs(value) > 0. for value in source_axis) > 1
    return {"native_build": qualification["oracle_version"], "disclosed_ingredients": fingerprint(previous),
            "disclosed_census": geography["census"], "measured_single_oblique_cylinder": fingerprint(simple),
            "single_cylinder_axis": source_axis, "all_current_generated_cases_native_qualified": False}


def add(first, second):
    return tuple(a + b for a, b in zip(first, second, strict=True))


def directions(authored):
    _, raw, ref, step, origin, bores, orders = authored
    axis_length = sqrt(sum(value**2 for value in raw))
    ref_length = sqrt(sum(value**2 for value in ref))
    axis = tuple(value / axis_length for value in raw)
    radial = tuple(value / ref_length for value in ref)
    shift = tuple(value * step for value in raw)
    assert tuple(value * (axis_length * step) for value in axis) == shift
    return axis_length * step, origin, axis, radial, bores, orders, shift


def construct(name, authored):
    radius = authored[0]
    height, origin, axis, radial, bores, orders, _ = directions(authored)
    normal, reference = SpaceVector(*axis), SpaceVector(*radial)
    stock = cylinder(name + "-stock", radius, height, SpaceVector(*origin), normal, reference)
    for index, (centre, inside) in enumerate(bores):
        hole = cylinder(f"{name}-bore-{index}", inside, height, SpaceVector(*centre), normal, reference)
        stock = subtract_straight_bore(stock, hole)
    by_face = {face.id: tuple(face.loop_ids[index] for index in order)
               for face, order in zip(support_caps(stock), orders, strict=True)}
    return replace(stock, faces=tuple(replace(row, loop_ids=by_face[row.id])
                                      if row.id in by_face else row for row in stock.faces))


def verify_geometry(shape, settings):
    radius, height, origin, axis, radial, bores, orders, shift = settings
    shaft = ((origin, radius), *bores)
    actual = tuple(actual_cap(shape, face) for face in support_caps(shape))
    moments = []
    sections = []
    world_centre = []
    for cap, order, translation in zip(actual, orders, ((0., 0., 0.), shift), strict=True):
        targets = [(add(shaft[index][0], translation), shaft[index][1]) for index in order]
        principal.close(tuple((centre, value) for centre, value, _ in cap), tuple(targets))
        assert tuple(outer for _, _, outer in cap) == tuple(index == 0 for index in order)
        weights = tuple((1 if outside else -1) * value**2 for _, value, outside in cap)
        section = fsum(weights)
        sections.append(section)
        moments.append(tuple(fsum(weight * row[0][index] for weight, row in zip(weights, cap, strict=True)) / section
                             for index in range(3)))
        world_centre.append(next(point for point, _, outside in cap if outside))
    walls = tuple(value for value in shape.surfaces if isinstance(value, CylinderSurface))
    stock = max(walls, key=lambda value: value.radius)
    signed_axis = principal.xyz(stock.axis)
    actual_height = dist(*world_centre)
    actual_volume = pi * sections[0] * actual_height
    actual_area = pi * fsum(sections) + tau * actual_height * fsum(value.radius for value in walls)
    actual_centroid = tuple((low + high) / 2 for low, high in zip(*moments, strict=True))
    section = radius**2 - fsum(value**2 for _, value in bores)
    desired_centroid = tuple(
        origin[index] + shift[index]/2
        - fsum((point[index] - origin[index]) * value**2 for point, value in bores) / section
        for index in range(3)
    )
    principal.close((actual_height, actual_volume, actual_area, actual_centroid, signed_axis), (
        height, pi * section * height, 2 * pi * (section + height * fsum(value for _, value in shaft)),
        desired_centroid, axis,
    ))
    bounds = tuple(tuple(get(a, b) + sign * stock.radius * sqrt(1 - signed_axis[index]**2)
                         for index, (a, b) in enumerate(zip(*world_centre, strict=True)))
                   for sign, get in ((-1, min), (1, max)))
    across = principal.xyz(CrossVector(SpaceVector(*axis), SpaceVector(*radial)))
    expected_bounds = tuple(
        tuple(get(a, b) + sign * radius * sqrt(radial[index]**2 + across[index]**2)
              for index, (a, b) in enumerate(zip(origin, add(origin, shift), strict=True)))
        for sign, get in ((-1, min), (1, max))
    )
    principal.close(bounds, expected_bounds)
    return {"cap_rims": actual, "axis": signed_axis, "height_mm": actual_height, "area_mm2": actual_area,
            "volume_mm3": actual_volume, "centroid_mm": actual_centroid, "bounds_mm": bounds}


def typed_refusals(nodes, offsets, group):
    bore_wall = next(node for node in nodes.values() if node.KindValue == 51 and node.FieldsValue["radius"] < 0.02)
    bore_rim = next(node for node in nodes.values() if node.KindValue == 31 and
                    node.FieldsValue["radius"] == bore_wall.FieldsValue["radius"])
    fin = next(node for node in nodes.values() if node.KindValue == 17)
    failures = {
        "adjacent_wire_coordinate": (bore_rim, "centre", AXIAL_ERROR),
        "adjacent_wire_axis_component": (bore_wall, "axis", "axes must follow both cap stations"),
        "physical_vertex_on_periodic_fin": (fin, "vertex", "bare ownership or identities"),
    }
    result = {}
    for role, (node, key, message) in failures.items():
        if key == "vertex":
            value = 1
        else:
            coordinate, *tail = node.FieldsValue[key]
            value = (nextafter(coordinate, inf), *tail)
        changed = replace(node, FieldsValue=dict(node.FieldsValue) | {key: value})
        contrast = nodes | {node.IndexValue: changed}
        result[role] = {
            "typed_read": rejected(lambda: ReadLocalCyl(contrast, offsets), message),
            "typed_write": rejected(lambda: EncodeLocalBody(group, tuple(contrast.values())), message),
        }
    return result


def run_case(name, authored):
    shape = construct(name, authored)
    assert not shape.validate()
    requested = document(shape)
    settings = (authored[0], *directions(authored))
    labels = BareLabels(name, "Default", "Imported oblique bores")
    locator = PureWindowsPath(r"C:\KitObliqueBores\Candidates") / (name + ".SLDPRT")
    options = recipe(labels, locator, 1790000000)
    candidate = MakeBareImport(requested, options, labels)
    repeat = MakeBareImport(document(construct(name, authored)), options, labels)
    assert repeat.BytesValue == candidate.BytesValue and repeat.StreamsValue == candidate.StreamsValue
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    assert archive.streams == candidate.StreamsValue and len(archive.streams) == 12
    _, local, group, mark = ordered_payloads(candidate.BytesValue, archive)
    nodes, offsets = ReadLocalNodes(local, AllowPeriodic=True)
    assert tuple(nodes.values()) == MakeAnnularBody(shape)
    assert EncodeLocalBody(group, tuple(nodes.values())) == archive.require(KLocalBodyStream)
    walls = len(authored[5]) + 1
    assert len(nodes) == 14 * walls + 9
    owners = read_owners(archive, group, mark)
    inputs, reader = principal.read_modes(candidate.BytesValue, settings, owners, measure=verify_geometry)
    for route in ("registry", "writer", "adapter"):
        for value in (requested, *inputs):
            refuse(route, value, {})
    return {"candidate": fingerprint(candidate.BytesValue), "local": fingerprint(local), "cells": len(nodes),
            "locator": str(locator), "epoch": 1790000000, "neutral_specification": authored,
            "stream_map": {key: fingerprint(value) for key, value in archive.streams.items()},
            "archive_ownership": owners, "local_ownership": ring_owners(nodes, walls),
            "source_geometry": verify_geometry(shape, settings), "sdk_readback": reader,
            "typed_refusals": typed_refusals(nodes, offsets, group), "public_write_refusals": 9}


def plane_residual(point, origin, axis, divisor):
    return sum(Fraction(v) * (Fraction(p / divisor) - Fraction(q / divisor))
               for p, q, v in zip(point, origin, axis, strict=True))


def neutral_refusals():
    radius, raw, frame, step, origin, bores, orders = AUTHORED["ObliqueTwin"]
    axis = directions(AUTHORED["ObliqueTwin"])[2]
    near, size = bores[0]
    epsilon = 2.0**-43
    shifted = add(near, (epsilon, 2*epsilon, 0.))
    shift = directions(AUTHORED["ObliqueTwin"])[-1]
    neutral_residual = plane_residual(shifted, origin, axis, 1.)
    encoded_residual = plane_residual(shifted, origin, axis, 1000.)
    assert not plane_residual(add(shifted, shift), add(origin, shift), axis, 1.)
    assert tuple(Fraction(a) - Fraction(b) for a, b in zip(add(shifted, shift), shifted, strict=True)) == shift
    assert not neutral_residual and encoded_residual
    tangent = ((origin, 11.71875), (add(origin, (15.625, 15.625, -7.8125)), 11.71875))
    assert dist(tangent[0][0], tangent[1][0]) == tangent[0][1] + tangent[1][1]
    overlap = ((origin, 11.71875), (add(origin, (7.8125, 7.8125, -3.90625)), 11.71875))
    assert dist(overlap[0][0], overlap[1][0]) < overlap[0][1] + overlap[1][1]
    off_plane = ((add(near, (0., 0., 0.125)), size), bores[1])
    contrasts = {
        "exact_neutral_but_not_after_metre_encoding": (((shifted, size), bores[1]), AXIAL_ERROR),
        "outside_cap_plane": (off_plane, AXIAL_ERROR),
        "tangent": (tangent, "openings overlap or touch"),
        "overlap": (overlap, "openings overlap or touch"),
    }
    results = {
        role: rejected(lambda: MakeAnnularBody(construct(role, (radius, raw, frame, step, origin, rings, orders))), message)
        for role, (rings, message) in contrasts.items()
    }
    exterior = ((add(origin, (31.25, 31.25, -15.625)), 15.625), bores[0])
    assert dist(exterior[0][0], origin) + exterior[0][1] == 62.5
    results["tangent_to_exterior"] = rejected(
        lambda: MakeAnnularBody(construct("Exterior", (62.5, raw, frame, step, origin, exterior, orders))),
        "does not clear the exterior wall",
    )
    solid = construct("InvalidSeam", AUTHORED["ObliqueTwin"])
    first, *others = solid.vertices
    wrong = replace(first, point=SpaceVector(*add(principal.xyz(first.point), (0.125, 0., 0.))))
    results["noncanonical_neutral_seam"] = rejected(
        lambda: MakeAnnularBody(replace(solid, vertices=(wrong, *others))), "seam is noncanonical"
    )
    return {"failures": results, "encoded_cap_residual": str(encoded_residual), "neutral_cap_residual": str(neutral_residual)}


def generate():
    with guard() as calls:
        cases = {name: run_case(name, authored) for name, authored in AUTHORED.items()}
        refusals = neutral_refusals()
    return {"cases": cases, "neutral_refusals": refusals, "runtime_data_reads": len(calls)}


def baseline():
    previous, evidence = pinned_receipt("PerforatedLocalImport01.json", PRINCIPAL_SHA)
    was = evidence["model-generate"]
    assert was["refusals"]["oblique"] == "local offset bores require one signed principal axis"
    was["refusals"]["oblique"] = "local circular bore does not join its two exact cap stations"
    assert loads(dumps(principal.generate())) == was
    older = principal.baseline()
    return {"previous_receipt": fingerprint(previous), "signed_perforated_cases": 2,
            "older_cases": sum(older[key] for key in ("exact_annular_cases", "exact_blind_cases",
                                                      "exact_rectangle_concave_and_cylinder_cases", "through_cases_from_prior_chain")),
            "stream_hashes": 24 + older["exact_logical_stream_hashes"],
            "runtime_data_reads": 0, "changed_diagnostic": was["refusals"]["oblique"]}


def main():
    methods = {"disclosed": observe, "generate": generate, "baseline": baseline}
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("all", *methods))
    args = parser.parse_args()
    result = methods[args.mode]() if args.mode != "all" else {
        mode: loads(check_output((sys.executable, "-I", "-B", str(HERE), mode), timeout=60))
        for mode in methods
    } | {
        "schema": "kit.sw2026.oblique-local-bores.v1",
        "runtime": sys.version.split()[0], "compressor": ZLIB_RUNTIME_VERSION,
        "tool": fingerprint(HERE.read_bytes()), "native_processes_started": 0, "new_heldout_cases": 0,
        "new_exact_native_admission": False,
    }
    print(dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
