from argparse import ArgumentParser
from math import isclose
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from CheckMeasuredCircleWriter import check_custody, demand, digest, MANIFEST, MANIFEST_SHA, NAME
from CheckScopedPlainWriter import reject


def vector(value):
    return [value.x, value.y, value.z]


def close(values, expected, detail):
    demand(all(isclose(left, right, rel_tol=5e-7, abs_tol=1e-10)
               for left, right in zip(values, expected, strict=True)), detail)


def linked_streams(archive, link):
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut

    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    config = link.ConfigValue
    resolved = link.ResolvedValue
    items = (
        ("Contents/CMgr", manager, WriteCmgrMut(manager.RootValue, 19000)),
        (link.ConfigName, config, WriteConfigMut(config.RootValue, 19000, config.HeaderValue)[0]),
        (link.StreamName, resolved, WriteResolMut(resolved.RootsValue, resolved.ExtraFields,
                                                  19000, config.MapValue, resolved.ContextValue)[0]),
    )
    rows = {}
    for stream, graph, generated in items:
        report = graph.ReportValue
        demand(report["completed"] and not report["missing_schemas"]
               and not report["provisional_schemas"] and generated == archive.require(stream),
               f"incomplete replay of {stream}")
        rows[stream] = {"bytes": len(generated), "sha256": digest(generated),
                        "next_counter": graph.MapValue.CounterValue}
    demand(manager.RootValue.FieldsValue["f658"] == 0, "manager context changed")
    return rows


def typed_semantics(document, lite, archive, link, observed):
    from convert.adapters.solidworks.Core.Adapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import ReadPrismParam
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude

    demand(not document.validate() and not lite.validate()
           and document.parameters == lite.parameters
           and document.sketches == lite.sketches
           and document.feature_timeline == lite.feature_timeline and lite.brep is None,
           "strict and semantic-only reads diverged in editable history")
    sketch, = document.sketches
    circle, = sketch.entities
    radial, fixed = sketch.constraints
    profile, boss = (row for row in document.feature_timeline if row.sketch_id == sketch.id)
    driver, depth = (document.parameter(entry.parameter_ids[0]) for entry in (profile, boss))
    demand(sketch.closed_profile_entity_ids == ((circle.id,),)
           and radial.kind == "diameter" and radial.driving and radial.parameter_id == driver.id
           and [(ref.entity_id, ref.point) for ref in radial.references] == [(circle.id, "")]
           and fixed.kind == "fixed"
           and [(ref.entity_id, ref.point) for ref in fixed.references] == [(circle.id, "center")]
           and circle.attributes["native_center_permanent_mark"] != circle.attributes["native_permanent_mark"]
           and (driver.owner_id, depth.owner_id) == (profile.id, boss.id)
           and (driver.name, depth.name) == ("D1", "D1")
           and boss.definition.length == depth.value and boss.definition.end_condition == "blind"
           and not boss.definition.reversed and boss.definition.second_length is None
           and boss.operation == "create", "strict read lost the native circle, owner, driver, or signed end")
    support = next(plane for plane in document.support_planes if plane.id == sketch.support_plane_id)
    demand(vector(support.transform.z_axis) == [0.0, 0.0, 1.0], "read changed actual support direction")
    close((circle.geometry.center.x, circle.geometry.center.y),
          (value * 1e3 for value in observed["center_m"]), "center moved from pinned native state")
    close((circle.geometry.radius, driver.value.value, depth.value.value),
          (observed["driving_radial_m"] * 500,
           observed["driving_radial_m"] * 1000, observed["driving_depth_m"] * 1000),
          "parsed live parameters differ from pinned native COM values")
    model = NativePartModel(archive, None)
    (operation,) = model.operations
    (native_sketch,) = model.sketches
    index = IndexFeatures(link)
    owner = ReadExtrude(link, index[operation.object_id], index)
    param = index[native_sketch.object_id].FieldsValue["pd_f80"].FieldsValue["dims"]
    radial_slot = param["val_g1"][0]["d"].FieldsValue["f28"]
    depth_word = owner.DepthValue.Parameter.FieldsValue["f58"]
    radial_word = radial_slot.FieldsValue["f58"]
    demand(driver.value.value == radial_word * 1000 and depth.value.value == depth_word / 0.001
           and driver.attributes["typed_archive_owner"]["object_index"] == radial_slot.IndexValue
           and depth.attributes["typed_archive_owner"]["object_index"] == owner.DepthValue.Parameter.IndexValue
           and model.SavedCircleAtom is not None, "public drivers are not their exact archived binary64 owners")
    inactive = ReadPrismParam(owner.EndValue.FieldsValue["f20"], False)[2]
    return owner, model.SavedCircleAtom, {"radial_mm": driver.value.value, "depth_mm": depth.value.value,
           "radial_m_hex": radial_word.hex(), "active_depth_m_hex": depth_word.hex(),
           "inactive_depth_m": inactive, "radius_mm": circle.geometry.radius,
           "driver_ids": [driver.id, depth.id], "feature_id": boss.id}


def physical(document, atom, semantic, observed):
    from convert.adapters.solidworks.Container.Parasolid import decode_brep_model
    from convert.adapters.solidworks.Core.Partition.CircularPartition import ReadShellAtom
    from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface

    body, = document.bodies
    (payload,) = (value for value in document.brep_payloads
                  if value.source_stream == "Contents/Config-0-Partition" and value.kind == "partition")
    brep = document.brep
    raw_model = decode_brep_model(payload.data)
    demand(brep is not None and raw_model is not None and len(brep.bodies) == 1
           and brep.bodies[0].design_body_id == body.id
           and (brep.surfaces, brep.curves, brep.faces, brep.edges) ==
               (raw_model.surfaces, raw_model.curves, raw_model.faces, raw_model.edges)
           and body.final_feature_id == semantic["feature_id"],
           "SDK replaced the actual native physical topology or owner")
    identity = ReadShellAtom(payload.data, brep)
    demand(identity["body_atom_id"] == atom, "physical and Config-0 atoms differ")
    cylinder, = (row for row in brep.surfaces if isinstance(row, CylinderSurface))
    planes = [row for row in brep.surfaces if isinstance(row, PlaneSurface)]
    signed_stations = sorted(plane.origin.z for plane in planes)
    close(signed_stations, (0.0, semantic["depth_mm"]), "cap planes have wrong signed stations")
    close((cylinder.radius,), (semantic["radius_mm"],), "physical side radius changed")
    demand(vector(cylinder.axis) == [0.0, 0.0, -1.0]
           and all(vector(plane.normal) == [0.0, 0.0, 1.0] for plane in planes)
           and (len(brep.faces), len(brep.edges), len(brep.vertices)) == (3, 2, 2),
           "native circle carrier or closed-edge topology changed")
    volume, area = body.topology.volume, body.topology.surface_area
    com = body.attributes["solidworks.body_centroid_mm"]
    mass = observed["mass_properties"]
    close((volume, area, *com),
          (mass["volume"] * 1e9, mass["area"] * 1e6, *(coordinate * 1000 for coordinate in mass["com"])),
          "physical volume, area or centroid disagrees with its pinned native observation")
    return {**identity, "partition_sha256": payload.sha256, "face_ids": [row.id for row in brep.faces],
            "cylinder_axis": vector(cylinder.axis), "signed_caps_mm": signed_stations, "volume_mm3": volume,
            "area_mm2": area, "centroid_mm": com}


def negative(archive, link, owner, initial):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive, SldprtFormatError

    payload = dict(archive.streams)
    partition = "Contents/Config-0-Partition"
    payload[partition] = SldprtArchive.from_bytes(initial).require(partition)
    contradictory = BuildSldprt(payload, FormatVersion=4)
    stale = reject(lambda: open_document(contradictory, source_format="solidworks.sldprt", strict=True),
                   SldprtFormatError, "active cylinder radius differs from the owned sketch")
    relaxed = open_document(contradictory, source_format="solidworks.sldprt", strict=False)
    demand(any(row.code == "sldprt.saved_circle_geometry_unresolved" for row in relaxed.diagnostics)
           and relaxed.bodies[0].topology.volume is None,
           "non-strict route attested contradictory body geometry")

    writer = link.ResolvedValue
    entry = owner.NodeValue.FieldsValue["f498"][0]
    original_id = entry["v"]
    try:
        entry["v"] += 1
        changed = WriteResolMut(writer.RootsValue, writer.ExtraFields, 19000,
                                link.ConfigValue.MapValue, writer.ContextValue)[0]
    finally:
        entry["v"] = original_id
    payload = {**archive.streams, link.StreamName: changed}
    fallback = open_document(BuildSldprt(payload, FormatVersion=4), source_format="solidworks.sldprt")
    message = next(row.message for row in fallback.diagnostics if "saved circle typed owners unavailable" in row.message)
    demand("saved circle atom does not link" in message
           and all("typed_archive_owner" not in p.attributes for p in fallback.parameters if p.name == "D1"),
           "a foreign body owner still received exact typed dimensions")
    return {"stale_partition": stale, "crossed_producing_atom": message}


def worker(request):
    sys.path.insert(0, str(ROOT / "src"))
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    path = Path(request["path"])
    raw = path.read_bytes()
    demand(digest(raw) == request["stage"]["saved_sha256"], "saved oracle output changed")
    initial = None
    if "initial_path" in request:
        initial = Path(request["initial_path"]).read_bytes()
        demand(digest(initial) == request["initial_sha256"], "unchanged initial body control changed")
    events = []

    def audit(event, args):
        if event in {"subprocess.Popen", "os.startfile", "os.spawn", "os.exec", "os.system", "ctypes.dlopen"}:
            events.append(event)
            raise PermissionError("reader accessed an external process or native runtime")

    sys.addaudithook(audit)
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    facts = linked_streams(archive, link)
    snapshot = "edited_body_snapshot" if request["stage"]["phase"] == "fresh-reopen" else "snapshot"
    observed = request["stage"]["snapshots"][snapshot]
    document = open_document(raw, source_format="solidworks.sldprt", strict=True)
    lite = open_document(raw, source_format="solidworks.sldprt", strict=True, include_brep=False)
    owner, atom, semantics = typed_semantics(document, lite, archive, link, observed)
    result = {"phase": request["stage"]["phase"],
              "file_sha256": digest(raw), "native_record_sha256": request["stage"]["record_sha256"],
              "linked_streams": facts, "editable_semantics": semantics,
              "physical": physical(document, atom, semantics, observed)}
    if initial is not None:
        result["refusals"] = negative(archive, link, owner, initial)
    demand(not events and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules)
           and digest(path.read_bytes()) == result["file_sha256"], "CAD runtime or source immutability failed")
    return result


def main():
    parser = ArgumentParser()
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True))
        return
    demand(args.packet is not None and args.output is not None, "use an exact disclosed packet and new receipt path")
    manifest = MANIFEST.read_bytes()
    demand(digest(manifest) == MANIFEST_SHA, "native report changed")
    receipt = json.loads(manifest)
    check_custody(args.packet, receipt)
    case, = (row for row in receipt["cases"] if row["name"] == NAME)
    paths = [args.packet / "Inspection" / NAME / row["phase"] / (NAME + "Saved.SLDPRT")
             for row in case["stages"]]
    result = []
    for path, stage in zip(paths, case["stages"], strict=True):
        request = {"path": str(path), "stage": stage}
        if stage["phase"] == "edited-fresh-reopen":
            request |= {"initial_path": str(paths[0]), "initial_sha256": case["stages"][0]["saved_sha256"]}
        guarded = subprocess.run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                                 input=json.dumps(request), text=True, capture_output=True, check=False)
        demand(guarded.returncode == 0, guarded.stdout + guarded.stderr)
        result.append(json.loads(guarded.stdout))
    demand(result[0]["editable_semantics"]["active_depth_m_hex"] != result[1]["editable_semantics"]["active_depth_m_hex"]
           and result[0]["editable_semantics"]["inactive_depth_m"] == result[1]["editable_semantics"]["inactive_depth_m"]
           and result[1]["editable_semantics"] == result[2]["editable_semantics"],
           "stored secondary cache or live edits did not meet their independent lifecycle")
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps({"schema": "kit.sw2026.saved-circle-sdk.v1", "native_report_sha256": MANIFEST_SHA,
                                 "tool_sha256": digest(HERE.read_bytes()), "fresh_processes": len(result),
                                 "linked_streams_exact": sum(len(row["linked_streams"]) for row in result),
                                 "native_process_launches": 0, "cases": result},
                                sort_keys=True, indent=2) + "\n")
    print(digest(args.output.read_bytes()))


if __name__ == "__main__":
    main()
