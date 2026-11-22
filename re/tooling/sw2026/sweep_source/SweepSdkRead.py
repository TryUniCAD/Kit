from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from math import isclose, pi

from convert import open_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Container.Format import KGhostPartition
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import BuildSweepPart
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwState import ReadSwState
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface, TorusSurface
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.SweepFeature import SweepFeature
from interchange.geometry.Models.VectorSpace import SpaceVector


def topology_view(document, job):
    body, = document.bodies
    summary = body.topology
    radius, path = job["section"], job["path"]
    bounds = summary.bounding_box
    expected = job["measurement"]["receipt"]["cases"][job["slot"]]["states"][0]
    values = (summary.volume * 1e-9, summary.surface_area * 1e-6, body.attributes["mass_kg"],
              *(value * 0.001 for value in body.attributes["center_of_mass_mm"]))
    actual = (expected["volume_m3"], expected["area_m2"], expected["mass_kg"], *expected["com_m"])
    if (summary.solid_count, summary.face_count, summary.edge_count, summary.vertex_count) != (1, 3, 2, 0):
        raise ValueError("projected topology lost native counts")
    if not all(isclose(value, target, rel_tol=5e-7, abs_tol=1e-11 if index == 5 else 0.0)
               for index, (value, target) in enumerate(zip(values, actual, strict=True))):
        raise ValueError("sweep readback measures disagree with exact native phase")
    if bounds.minimum != SpaceVector(0.0, -radius * 1000.0, -radius * 1000.0) or bounds.maximum != SpaceVector(
        path * 1000.0 + radius * 1000.0, path * 1000.0, radius * 1000.0
    ):
        raise ValueError("invalid signed quarter bounds")
    native = job.get("native_topology")
    if native is not None:
        face_rows = native["face_rows"]
        areas = (pi * radius**2, pi * radius**2, pi**2 * radius * path)
        if (native["faces"], native["edges"], native["vertices"]) != (3, 2, 0) or not all(
            item["torus"] == (index == 2)
            and item["producer"] == body.name
            and isclose(item["area_m2"], area, rel_tol=5e-7)
            for index, (item, area) in enumerate(zip(face_rows, areas, strict=True))
        ):
            raise ValueError("sweep reconstructed carriers disagree with native face identities")
    return {"native_face_edge_vertex_counts": [3, 2, 0], "solid_count": 1, "analytic_native_matches": 6,
            "native_face_rows_checked": native is not None}


def check_boundary(document, job):
    brep = document.brep
    body, = document.bodies
    if (brep is None or brep.validate(frozenset({body.id}))
            or len(brep.bodies) != 1 or brep.bodies[0].design_body_id != body.id
            or len(brep.faces) != 3 or len(brep.edges) != 2 or len(brep.pcurves) != 4):
        raise ValueError("sweep readback lacks its valid owner bound trimmed solid")
    caps = tuple(surface for surface in brep.surfaces if isinstance(surface, PlaneSurface))
    torus, = (surface for surface in brep.surfaces if isinstance(surface, TorusSurface))
    if (tuple(plane.normal for plane in caps) != (SpaceVector(-1.0, 0.0, 0.0), SpaceVector(0.0, 1.0, 0.0))
            or (torus.major_radius, torus.minor_radius) != (job["path"] * 1000.0, job["section"] * 1000.0)
            or len(brep.vertices) != 2 or any(not vertex.attributes.get("periodic_seam") for vertex in brep.vertices)
            or any(edge.start_vertex_id != edge.end_vertex_id for edge in brep.edges)):
        raise ValueError("sweep carrier signs or canonical periodic boundaries differ")
    trim_uses = tuple(coedge for coedge in brep.coedges if coedge.reversed)
    trims = tuple(next(curve for curve in brep.pcurves if curve.id == use.pcurve_id) for use in trim_uses)
    if tuple((uv.origin.XCoord, uv.direction.YCoord) for uv in trims) != ((0.0, 1.0), (pi / 2.0, -1.0)):
        raise ValueError("sweep reconstructed the wrong angular sector")


def reject_source(raw, expected_error):
    for include_brep in (True, False):
        for read in (lambda: open_document(raw, include_brep=include_brep),
                     lambda: SldprtAdapter().read(raw, ReadOptions(include_brep=include_brep))):
            try:
                read()
            except ValueError as error:
                if expected_error not in str(error):
                    raise
            else:
                raise ValueError("strict sweep read accepted unqualified source bytes")


def prove_sw_archives(payload, candidate, job):
    archive = SldprtArchive.from_bytes(payload)
    state = ReadSwState(archive)
    config, resolved = state.LinkValue.ConfigValue, state.LinkValue.ResolvedValue
    config_bytes, cfg_replay = WriteConfigMut(config.RootValue, 19000, config.HeaderValue, SweepGhosts=True)
    resolved_bytes, res_replay = WriteResolMut(
        resolved.RootsValue, resolved.ExtraFields, 19000, cfg_replay.MapValue,
        resolved.ContextValue, WriteSweeps=True,
    )
    if (config_bytes != archive.require(state.LinkValue.ConfigName) or cfg_replay.MapValue != config.MapValue
            or resolved_bytes != archive.require(state.LinkValue.StreamName) or res_replay.MapValue != resolved.MapValue):
        raise ValueError("sweep typed archive replay changed a measured wire owner")
    moved = replace(state.IntentValue, PathValue=replace(state.IntentValue.PathValue,
                    center=replace(state.IntentValue.PathValue.Center, y=job["path"] + 0.001),
                    radius=job["path"] + 0.001))
    foreign = BuildSweepPart(moved)
    if foreign.StreamsValue[KGhostPartition] == archive.require(KGhostPartition):
        raise ValueError("the authored path contrast did not change its actual ghost wire")
    reject_source(build_sldprt(dict(archive.streams) | {KGhostPartition: foreign.StreamsValue[KGhostPartition]}, FormatVersion=4),
                  "canonical sweep reconstruction differs")
    missing = {name: value for name, value in archive.streams.items() if name != KGhostPartition}
    reject_source(build_sldprt(missing, FormatVersion=4), "GhostPartition")
    extra = dict(archive.streams) | {"Contents/UnmodeledSweepState": b"unowned"}
    reject_source(build_sldprt(extra, FormatVersion=4), "canonical sweep reconstruction differs")
    if len(archive.records) != len(candidate.StreamsValue):
        raise ValueError("sweep source and re-emitted stream cardinalities differ")
    return {"config_map": config.MapValue.CounterValue, "resolved_map": resolved.MapValue.CounterValue,
            "typed_stream_replays": 2, "rejected_sources": ["foreign_ghost_shape", "missing_ghost", "unmodeled_stream"]}


def prove_sw_read(payload, candidate, job, transfer, options, reject):
    result = prove_sw_archives(payload, candidate, job)
    checks = []
    for include_brep in (True, False):
        document = open_document(payload, include_brep=include_brep)
        direct_doc = SldprtAdapter().read(BytesIO(payload), ReadOptions(include_brep=include_brep))
        same_label = replace(direct_doc, source=replace(direct_doc.source, path=document.source.path))
        portable = document.to_json(indent=None)
        if document != same_label or CadDocument.from_json(portable).to_json(indent=None) != portable:
            raise ValueError("registry direct reader and neutral JSON projections disagree")
        section, path = document.sketches
        step, = document.feature_timeline
        drivers = document.parameters[:2]
        if (type(step.definition) is not SweepFeature or step.sketch_id != section.id or step.definition.PathSketchId != path.id
                or tuple(driver.owner_id for driver in drivers) != (section.id, path.id)
                or tuple(driver.value.value / 1000.0 for driver in drivers) != (2 * job["section"], job["path"])
                or tuple(driver.attributes["typed_archive_owner"]["object_index"] for driver in drivers) != (174, 196)
                or tuple(driver.attributes["typed_archive_owner"]["dimension_index"] for driver in drivers) != (172, 195)
                or document.parameters[2].owner_id != document.bodies[0].id
                or document.source.sha256 != sha256(payload).hexdigest()):
            raise ValueError("sweep projection lost the actual typed sketch, feature, body or D1 links")
        shape = topology_view(document, job)
        if include_brep:
            check_boundary(document, job)
        elif document.brep is not None:
            raise ValueError("design-only sweep read retained a B-rep")
        for direct in (False, True):
            sink = BytesIO()
            outcome = transfer(direct_doc if direct else CadDocument.from_json(portable), sink, options, direct)
            if sink.getvalue() != payload or outcome.native_capabilities != document.capabilities:
                raise ValueError("canonical strict sweep readback did not republish exact measured bytes")
            broken = replace(document, source=replace(document.source, sha256="0" * 64))
            sink = BytesIO(b"unchanged")
            reject(lambda: transfer(broken, sink, options, direct), sink, "differs from its regenerated part")
            body, = document.bodies
            wrong_body = replace(body, topology=replace(body.topology, edge_count=3))
            wrong_geometry = replace(document, bodies=(wrong_body,))
            sink = BytesIO(b"unchanged")
            reject(lambda: transfer(wrong_geometry, sink, options, direct), sink, "differs from its regenerated part")
        checks.append({"include_brep": include_brep, "strict_reader_routes": 2, "exact_republication_routes": 2,
                       "native_transfers": len(document.capabilities), "driver_slots": [174, 196], **shape})
    return result | {"strict_readback": checks}


def check_permissive(payload):
    permissive = open_document(payload, strict=False)
    inventory = [len(permissive.feature_timeline), len(permissive.sketches), int(permissive.brep is not None)]
    if inventory != [20, 2, 0]:
        raise ValueError("legacy source inspection behavior changed")
    return inventory
