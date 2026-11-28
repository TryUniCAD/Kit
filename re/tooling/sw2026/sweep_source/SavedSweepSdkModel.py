from dataclasses import replace
from math import isclose

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import ReadActiveNodes
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KGhostPartition, KPartitionStream
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwGraph import ReadSwGraph
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwPart import ReadSwPart
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwFrames import ReadSwFrames
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwResult import ReadSwResult
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwRims import ReadSwRims
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwShell import ReadSwShell
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwTrim import ReadSwTrim
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.SweepFeature import SweepFeature
from interchange.geometry.Models.GeometryCurves import ArcGeometry, CircleGeometry
from AuditSavedSweepMain import demand
from SavedSweepSdkTrims import check_trims


def compare_model(direct, same, design_only, job):
    demand(all(replace(value, source=direct.source) == direct for value in same),
           "strict adapter and registry differ for the selected physical lane")
    demand(replace(design_only, source=direct.source, brep=direct.brep, capabilities=direct.capabilities) == direct
           and design_only.brep is None, "design-only saved sweep changed its history or kept geometry")
    section, path = direct.sketches
    diameter, radius, density = direct.parameters
    feature, = direct.feature_timeline
    body, = direct.bodies
    actual = (diameter.value.value, radius.value.value, density.value.value)
    expected = (*(v * 1000.0 for v in job["drivers_m"]), job["prior"]["topology"]["density"])
    native_dimensions = tuple(str(value["dimension"]) for value in job["prior"]["saved_sketches"])
    demand(actual == expected and (diameter.name, radius.name) == ("D1", "D1")
           and (diameter.provenance.native_id, radius.provenance.native_id) == native_dimensions
           and (diameter.owner_id, radius.owner_id, density.owner_id) == (section.id, path.id, body.id)
           and section.parameter_ids == (diameter.id,) and path.parameter_ids == (radius.id,),
           "typed saved D1 or density did not retain the real owner and current value")
    demand(feature.kind is FeatureKind.KSweep and feature.operation is BooleanOp.KCreate
           and feature.sketch_id == section.id and type(feature.definition) is SweepFeature
           and feature.definition.PathSketchId == path.id and body.final_feature_id == feature.id
           and body.name == feature.name == "OrdinarySweptBoss"
           and body.attributes["native_atom_id"] == str(job["prior"]["topology"]["atom"]),
           "saved history lacks the actual sweep and body ownership")
    demand(tuple(plane.name for plane in direct.support_planes) == ("Front Plane", "Top Plane", "Right Plane")
           and len(direct.configurations) == 1 and direct.configurations[0].active
           and direct.configurations[0].name == "Default"
           and direct.configurations[0].attributes["native_configuration_id"] == 0
           and direct.metadata["solidworks.part_text_properties"]["status"] == "complete",
           "saved datum or configuration ownership was lost")
    sketches = check_sketches(section, path, job)
    topology = check_body(direct, body, job)
    rims = check_trims(direct.brep, job["prior"]["geometry"], body.id)
    return {"typed_result_atom": body.attributes["native_atom_id"], "native_body_name": body.name,
            "independent_drivers_mm": actual[:2], "density_kg_m3": actual[2], "sketches": sketches,
            "current_geometry": topology, "oriented_rims": rims,
            "matched_direct_registry_explicit_default_and_design_only": True}


def check_sketches(section, path, job):
    from math import cos, hypot, isclose, sin

    native, _ = job["prior"]["saved_sketches"]
    section_entity, = section.entities
    path_entity, = path.entities
    seam = section_entity.attributes["periodic_seam"]
    demand(type(section_entity.geometry) is CircleGeometry and type(path_entity.geometry) is ArcGeometry
           and tuple(seam["saved_point_mm"]) == tuple(value * 1000.0 for value in native["seam_local_m"])
           and (seam["center_index"], seam["start_end_index"], tuple(seam["point_marks"]))
           == (native["center_index"], native["same_start_end_index"], tuple(native["permanent_marks"]))
           and seam["diameter_parameter_id"] == section.constraints[1].parameter_id
           and isclose(seam["angle_rad"], native["seam_angle_rad"], abs_tol=1e-15)
           and tuple(item.kind for item in section.constraints) == ("fixed", "diameter")
           and tuple(item.kind for item in path.constraints) == ("fixed", "vertical", "horizontal", "radius"),
           "portable section seam or Standard sketch relations differ from the observed source")
    edited_radius = section_entity.geometry.Radius * 2.0
    angle = seam["angle_rad"]
    derived = (edited_radius * cos(angle), edited_radius * sin(angle))
    demand(isclose(hypot(*derived), edited_radius) and derived != tuple(seam["saved_point_mm"]),
           "portable seam does not follow an edited circle radius")
    return {"periodic_seam_mm": tuple(seam["saved_point_mm"]), "point_marks": tuple(seam["point_marks"]),
            "local_seam_angle_rad": angle, "center_index": seam["center_index"],
            "start_end_index": seam["start_end_index"]}


def check_body(document, body, job):
    summary = body.topology
    native = job["native_measurement"]["mass"]
    actual = (summary.solid_count, summary.shell_count, summary.face_count, summary.edge_count, summary.vertex_count)
    demand(actual == (1, 1, 3, 2, 0) and summary.valid and not document.brep_payloads,
           "portable result does not distinguish physical topology from periodic seam anchors")
    volume, area, mass = summary.volume * 1e-9, summary.surface_area * 1e-6, body.attributes["mass_kg"]
    center = tuple(value * 0.001 for value in body.attributes["center_of_mass_mm"])
    demand(all(isclose(value, native[name], rel_tol=5e-7) for name, value in (("volume", volume), ("area", area), ("mass", mass)))
           and all(isclose(value, wanted, rel_tol=5e-7, abs_tol=1e-16) for value, wanted in zip(center, native["com"], strict=True)),
           "actual portable result metrics disagree with the independently recorded native save")
    return {"native_counts": actual, "volume_m3": volume, "area_m2": area, "mass_kg": mass, "center_m": center}


def reject(action, message):
    try:
        action()
    except ValueError as error:
        demand(message in str(error), str(error))
    else:
        raise ValueError("strict saved sweep accepted an unrelated owner")


def swap_stream(archive, foreign, name):
    return replace(archive, records=tuple(replace(row, data=foreign.require(name)) if row.name == name else row
                                          for row in archive.records))


def manager_stamp(raw):
    graph = ReadSwGraph(SldprtArchive.from_bytes(raw), Saved=True)
    fields = graph.FeatureValue.FieldsValue
    manager, = graph.LinkValue.ManagerValue.RootValue.FieldsValue["f5b8"]
    demand((fields["f2a4"] & 0xFFFFFFFF, fields["f2a0"] & 0xFFFFFFFF) == (manager["b"], manager["c"]),
           "typed feature and manager did not retain the same bit pattern")
    return {"feature_f2a4": fields["f2a4"], "feature_f2a0": fields["f2a0"], "manager": manager}


def negative_contrasts(raw, foreign_raw, slot, role):
    archive, foreign = SldprtArchive.from_bytes(raw), SldprtArchive.from_bytes(foreign_raw)
    for name in (KPartitionStream, KGhostPartition):
        swapped = swap_stream(archive, foreign, name)
        for include in (True, False):
            reject(lambda: ReadSwPart(swapped, raw, "<disclosed>", ReadOptions(include_brep=include)),
                   "unsupported SOLIDWORKS saved sweep result partition")
    if (slot, role) == (1, "original"):
        graph = ReadSwGraph(archive, Saved=True)
        active, _ = ReadSwFrames(archive)
        nodes = ReadActiveNodes(active)
        body, faces = ReadSwShell(nodes)
        torus, first, second = ReadSwRims(nodes, body, faces)
        wrong = replace(first, CircleValue=replace(first.CircleValue, FieldsValue=dict(first.CircleValue.FieldsValue)
                                                   | {"normal": second.CircleValue.FieldsValue["normal"]}))
        reject(lambda: ReadSwTrim(torus, wrong), "foreign cap chart")
        field = graph.DensityValue
        altered = replace(graph, DensityValue=replace(field, FieldsValue=dict(field.FieldsValue) | {"f58": field.FieldsValue["f58"] + 1}))
        reject(lambda: ReadSwResult(archive, altered), "physical density owner")
        return ["foreign_saved_partition", "foreign_saved_ghost", "foreign_trim_frame", "foreign_density"]
    return ["foreign_saved_partition", "foreign_saved_ghost"]
