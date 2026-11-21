from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict, replace
from importlib import import_module
import json
from math import isclose, tau
from pathlib import Path, PureWindowsPath

from BuildLocalCylinder import (
    CASES,
    expected_measures,
    measure_neutral,
    read_typed,
    write_typed,
)
from BuildLocalCylinderPart import (
    make_part,
    ordered_payloads,
    planar_delta,
    raw_document,
)
from LocalBodyEnvelope import LocalBody, encode
from VerifyBareImportPackage import fingerprint, guard_build, require
from convert import open_document
from convert.Geometry.Parasolid import DecodeBrepModel
from convert.Geometry.Revolve.SweepVector import DotVector
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KLocalBodyStream,
    KPartitionStream,
)
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Adapter import NativePartModel
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.Local.ReadLocalOwner import (
    ReadLocalOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.Cylinder.CheckCylOwner import (
    CheckCylOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.FindLocalOwner import (
    FindLocalOwner,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalPayload import (
    ReadLocalState,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.Enums.EnumDocument import Severity
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface

ROOT = Path(__file__).resolve().parents[4]
RECEIPTS = ROOT / "re/solidworks/measurements/2026"
LOCAL = "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody"
OWNERS = (
    "src/convert/adapters/solidworks/Core/Adapter.py",
    "src/convert/adapters/solidworks/Archive/Partition/ReadXmtHistory.py",
    "src/convert/Geometry/Parasolid.py",
    "src/convert/adapters/solidworks/Archive/Partition/CheckXmtMarks.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/BodyNames/Local/ReadLocalOwner.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/ReadNativeLink.py",
    "re/tooling/sw2026/imported_body_source/BuildLocalCylinder.py",
    "re/tooling/sw2026/imported_body_source/BuildLocalCylinderPart.py",
    "re/tooling/sw2026/imported_body_source/VerifyBareImportPackage.py",
    *(
        f"{LOCAL}/{file}.py"
        for file in (
            "ReadLocalBodyBrep",
            "ReadLocalBodyNodes",
            "ReadLocalImport",
            "ReadLocalPayload",
        )
    ),
    *(
        f"{LOCAL}/Cylinder/{file}.py"
        for file in (
            "AddCylGeomMut",
            "CheckCylBrep",
            "CheckCylFrame",
            "CheckCylGraph",
            "CheckCylOwner",
            "CheckCylRing",
            "CheckCylRims",
            "ReadLocalCyl",
        )
    ),
)
STOCK_PHASES = {"CylinderZ": "StockZBefore", "CylinderReverseY": "StockReverseYAfter"}
PART_BODY = "sldprt:body:1"


def read_exact(path, digest):
    require(
        not path.is_symlink() and path.is_file(),
        f"expected a disclosed regular file: {path}",
    )
    data = path.read_bytes()
    require(
        fingerprint(data)["sha256"] == digest, f"disclosed file digest changed: {path}"
    )
    return data


def disclosed_inputs(packet, saved_dir, stock_dir):
    compact = json.loads(
        (RECEIPTS / "GeneratedLocalCylinderPartNative01.json").read_bytes()
    )
    stock = json.loads((RECEIPTS / "ImportedBodyTopologyNative01.json").read_bytes())
    native = json.loads(
        read_exact(packet / "Result.json", compact["full_native_result_sha256"])
    )
    host = json.loads(read_exact(packet / "Build.json", compact["host_build_sha256"]))
    require(
        native["passed"]
        and native["controls_healthy"]
        and native["distinct_native_processes"] == 10
        and native["inputs_and_saved_copies_unchanged"]
        and native["oracle_version"] == "34.5.2.0604"
        and stock["controls_healthy"]
        and not native["heldout_cases"],
        "native packet is outside the disclosed accepted cylinder paths",
    )
    phases = {phase["name"]: phase for phase in native["phases"]}
    cases = {}
    for name in CASES:
        case = host["cases"][name]
        initial, saved = phases[name], phases[name + "Reopen"]
        require(
            initial["input_path"] == case["native_path"]
            and initial["passed"]
            and saved["passed"],
            f"native case {name} changed its locator",
        )
        filename = name + ".SLDPRT"
        cases[name] = (
            case,
            read_exact(packet / "Candidates" / filename, case["part"]["sha256"]),
            read_exact(saved_dir / filename, initial["saved_sha256"]),
            initial["cold"],
            saved["cold"],
        )
    controls = {}
    for name, phase_name in STOCK_PHASES.items():
        phase = phases[phase_name]
        observed = stock["observations"][name]
        digest = observed["source"]["sha256"]
        require(
            phase["passed"] and phase["source_sha256"] == digest,
            f"stock measurement identity changed: {name}",
        )
        controls[name] = (
            read_exact(stock_dir / (name + ".SLDPRT"), digest),
            phase["cold"],
            observed,
        )
    return cases, controls, native["tolerances"], compact


def read_public(data, *, strict=True, include_brep=True):
    return open_document(
        data,
        source_format="solidworks.sldprt",
        strict=strict,
        include_brep=include_brep,
        include_tessellation=False,
    )


def coordinates(vector):
    return (vector.x, vector.y, vector.z)


def compare_tuple(actual, expected, tolerance, label):
    require(
        all(
            isclose(left, right, abs_tol=tolerance, rel_tol=0.0)
            for left, right in zip(actual, expected, strict=True)
        ),
        f"analytic comparison disagrees: {label}",
    )


def compare_shape(model, measures, native, tolerance):
    require(
        (native["solids"], native["faces"], native["edges"], native["vertices"])
        == (1, 3, 2, 0)
        and all(not use.reversed for use in model.face_uses),
        "native topology or neutral shell orientation differs",
    )
    for key, native_key, scale in (
        ("volume_mm3", "volume_m3", 1e9),
        ("area_mm2", "area_m2", 1e6),
    ):
        require(
            isclose(
                measures[key],
                native[native_key] * scale,
                abs_tol=tolerance[native_key] * scale,
                rel_tol=tolerance["relative_mass"],
            ),
            f"analytic comparison disagrees: {key}",
        )
    position = tolerance["position_m"] * 1000.0
    direction = tolerance["direction"]
    compare_tuple(
        measures["centroid_mm"],
        (point * 1000.0 for point in native["com_m"]),
        position,
        "centre of mass",
    )
    for actual, expected in zip(
        measures["bounds_mm"], native["extreme_bounds_m"], strict=True
    ):
        compare_tuple(
            actual, (point * 1000.0 for point in expected), position, "bounds"
        )
    (side,) = (
        surface for surface in model.surfaces if type(surface) is CylinderSurface
    )
    mantle = native["mantle_parameters"]
    compare_tuple(
        coordinates(side.origin),
        (point * 1000.0 for point in mantle[:3]),
        position,
        "axis origin",
    )
    compare_tuple(coordinates(side.axis), mantle[3:6], direction, "signed axis")
    compare_tuple((side.radius,), (mantle[6] * 1000.0,), position, "radius")
    caps = sorted(
        (surface for surface in model.surfaces if type(surface) is PlaneSurface),
        key=lambda surface: DotVector(surface.origin, side.axis),
    )
    circles = sorted(model.curves, key=lambda curve: DotVector(curve.center, side.axis))
    for actual, cap, circle, rim in zip(
        caps, native["caps"], circles, native["cap_rims"], strict=True
    ):
        compare_tuple(
            coordinates(actual.origin),
            (point * 1000.0 for point in cap["plane_parameters"][3:]),
            position,
            "cap station",
        )
        compare_tuple(
            coordinates(actual.normal), cap["outward_normal"], direction, "outward cap"
        )
        compare_tuple(
            coordinates(circle.center),
            (point * 1000.0 for point in rim["center_m"]),
            position,
            "rim centre",
        )
        compare_tuple(coordinates(circle.axis), rim["normal"], direction, "rim sense")
        compare_tuple(
            (circle.radius,), (rim["radius_m"] * 1000.0,), position, "rim radius"
        )
        compare_tuple(
            (0.0, tau), rim["trim"], tolerance["period_rad"], "native full turn"
        )


def inspect_case(data, phase, tolerance, *, cold):
    archive = SldprtArchive.from_bytes(data)
    intake, kernel, group, selected = ordered_payloads(data, archive)
    document = read_public(data)
    model = document.brep
    require(
        model is not None and document.brep_payloads == intake.brep_payloads,
        "selected strict payloads differ from raw intake",
    )
    (design,) = document.bodies
    (kernel_body,) = model.bodies
    (feature,) = (
        step for step in document.feature_timeline if step.kind == FeatureKind.IMPORTED
    )
    native_feature = phase["feature"]
    feature_id, feature_name = (
        (native_feature["native_id"], native_feature["name"])
        if isinstance(native_feature, dict)
        else (phase["feature_id"], native_feature)
    )
    require(
        feature.id == f"sldprt:feature:{feature_id}"
        and feature.name == feature_name == group
        and design.id == PART_BODY
        and feature.attributes["native_object_id"] == feature_id,
        "public inspection lost the selected design body or native import feature",
    )
    ordinary = DecodeBrepModel(kernel)
    if cold:
        topology = design.topology
        require(
            ordinary is None
            and intake.brep is None
            and design.final_feature_id == feature.id
            and design.provenance == feature.provenance
            and kernel_body.design_body_id == PART_BODY
            and (
                topology.solid_count,
                topology.shell_count,
                topology.face_count,
                topology.edge_count,
                topology.vertex_count,
            )
            == (1, 1, 3, 2, 2)
            and not model.validate(frozenset({PART_BODY})),
            "strict cold geometry did not bind one complete solid to its native owner",
        )
        metadata = read_public(data, include_brep=False)
        (config,) = metadata.configurations
        require(
            metadata.brep is None
            and not metadata.brep_payloads
            and config.active
            and config.name == phase["configuration"],
            "metadata observed a different physical configuration",
        )
    else:
        require(
            model == ordinary
            and kernel_body.design_body_id == ""
            and design.topology.solid_count == 0,
            "marked ordinary geometry changed precedence or ownership",
        )
    counts, measures = measure_neutral(
        replace(model, bodies=(replace(kernel_body, design_body_id=""),))
    )
    require(
        all(entry.severity is Severity.INFO for entry in document.diagnostics),
        "accepted public geometry produced a warning or error",
    )
    compare_shape(model, measures, phase.get("shape", phase.get("geometry")), tolerance)
    link = ReadNativeLink(archive, 0)
    atom, owner = ReadLocalOwner(link, group, selected)
    require(
        owner == feature_id and (atom.FieldsValue["f180"] == 0) == cold,
        "physical atom or typed feature did not match the read route",
    )
    return {
        "part": fingerprint(data),
        "kernel": fingerprint(kernel),
        "feature": feature.id,
        "design_body": design.id,
        "kernel_design_body": kernel_body.design_body_id,
        "summary_solids": design.topology.solid_count,
        "counts": counts,
        "measured": measures,
        "ordinary_geometry": ordinary is not None,
        "selected_mark": selected,
        "atom_id": atom.FieldsValue["f140"],
        "atom_tag": atom.FieldsValue["f180"],
        "sdk_info": [entry.message for entry in document.diagnostics],
    }


def publish_fault(archive, name, data):
    streams = dict(archive.streams)
    if data is None:
        del streams[name]
    else:
        require(data != streams[name], f"fault did not change {name}")
        streams[name] = data
    return BuildSldprt(
        streams, FileId=archive.file_id, FormatVersion=archive.format_version
    )


def typed_fault(archive, target):
    link = ReadNativeLink(archive, 0)
    config, resolved = link.ConfigValue, link.ResolvedValue
    (owner,) = (
        node
        for node in resolved.RootsValue
        if node.ClassValue.NameValue == "moBaseBody_c"
    )
    activation = config.RootValue.FieldsValue["fe38"]
    if target == "activation":
        activation.FieldsValue["f18"] -= 1
        config_bytes, _ = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
        return publish_fault(archive, link.ConfigName, config_bytes)
    if target == "selected":
        owner.FieldsValue["f3d0"].FieldsValue["f18"] = activation.FieldsValue["f18"]
    if target == "atom":
        owner.FieldsValue["f498"][0]["v"] += 1
    if target == "marked":
        atom = owner.FieldsValue["f528"]["items"][0]["o"]
        tag = atom.FieldsValue["f140"]
        atom.FieldsValue.update(f180=tag, f1b0=tag)
        config_bytes, config = WriteConfigMut(
            config.RootValue, 19000, config.HeaderValue
        )
        if config_bytes != archive.require(link.ConfigName):
            return publish_fault(archive, link.ConfigName, config_bytes)
    resolved_bytes, _ = WriteResolMut(
        resolved.RootsValue,
        resolved.ExtraFields,
        19000,
        config.MapValue,
        resolved.ContextValue,
    )
    return publish_fault(archive, link.StreamName, resolved_bytes)


def graph_fault(archive, group, kernel, target):
    header, nodes, _ = read_typed(kernel)
    first_fin = next(node for node in nodes.values() if node.KindValue == 17)
    first_rim = next(node for node in nodes.values() if node.KindValue == 31)
    if target == "fin":
        changed = replace(
            first_fin,
            FieldsValue=dict(first_fin.FieldsValue, forward=first_fin.Integer("other")),
        )
    elif target == "vertex":
        changed = replace(
            first_fin,
            FieldsValue=dict(first_fin.FieldsValue, vertex=first_rim.IndexValue),
        )
    elif target == "inventory":
        mantle = next(node for node in nodes.values() if node.KindValue == 51)
        side = nodes[mantle.Integer("owner")]
        tail = nodes[nodes[side.Integer("loop")].Integer("next")]
        extra = replace(
            tail,
            IndexValue=len(nodes) + 1,
            FieldsValue=dict(
                tail.FieldsValue, node_id=nodes[1].Integer("highest_node_id") + 1
            ),
        )
        nodes[extra.IndexValue] = extra
        changed = replace(
            tail, FieldsValue=dict(tail.FieldsValue, next=extra.IndexValue)
        )
    else:
        changed = replace(
            first_rim,
            FieldsValue=dict(
                first_rim.FieldsValue, radius=first_rim.FieldsValue["radius"] * 2.0
            ),
        )
    nodes[changed.IndexValue] = changed
    return publish_fault(
        archive, KLocalBodyStream, encode(LocalBody(group, write_typed(header, nodes)))
    )


def check_refusal(data, reason):
    try:
        read_public(data)
    except SldprtFormat as error:
        require(
            str(error) == "SLDPRT local geometry rejected: " + reason,
            f"unexpected strict fault: {error}",
        )
    else:
        raise ValueError(f"strict cold reader accepted a changed {reason}")
    partial = read_public(data, strict=False)
    metadata = read_public(data, include_brep=False)
    intake = raw_document(data)
    diagnostics = tuple(
        item
        for item in partial.diagnostics
        if item.code == "sldprt.local_geometry_rejected"
    )
    require(
        partial.brep is intake.brep is metadata.brep is None
        and len(diagnostics) == 1
        and diagnostics[0].severity == Severity.WARNING
        and reason in diagnostics[0].message
        and diagnostics[0].attributes["stream"] == KLocalBodyStream
        and not metadata.brep_payloads
        and partial.brep_payloads == intake.brep_payloads,
        "a changed capsule altered the partial metadata or raw intake boundary",
    )
    return {
        "diagnostic": str(diagnostics[0].message),
        "raw_payloads": len(intake.brep_payloads),
    }


def faults(data):
    archive = SldprtArchive.from_bytes(data)
    intake, kernel, group, _ = ordered_payloads(data, archive)
    _, selected, prior = ReadLocalState(
        intake.brep_payloads, archive.require(KPartitionStream)
    )
    owner = FindLocalOwner(NativePartModel(archive, None), archive)
    require(
        owner is not None and owner.native_offset is not None,
        "faults require the actual typed owner",
    )
    link = ReadNativeLink(archive, 0)
    (typed,) = (
        node
        for node in link.ResolvedValue.RootsValue
        if node.ClassValue.NameValue == "moBaseBody_c"
    )
    try:
        CheckCylOwner(
            archive,
            replace(owner, native_offset=typed.EndOffset),
            group,
            selected,
            prior,
        )
    except ValueError as error:
        require(
            str(error) == "local cylinder has a foreign feature or marked atom",
            str(error),
        )
        marker = str(error)
    else:
        raise ValueError("typed feature beyond its wire span was accepted")
    return {
        "physical_span": marker,
        **{
            name: check_refusal(mutated, reason)
            for name, mutated, reason in (
                (
                    "missing_history",
                    publish_fault(archive, KPartitionStream, None),
                    "local body rollback history is missing",
                ),
                (
                    "wrong_group",
                    publish_fault(
                        archive,
                        KLocalBodyStream,
                        encode(LocalBody("Unowned geometry", kernel)),
                    ),
                    "local body storage key differs from its resolved import",
                ),
                (
                    "wrong_activation",
                    typed_fault(archive, "activation"),
                    "local cylinder activation does not own the rollback predecessor",
                ),
                (
                    "wrong_selected_mark",
                    typed_fault(archive, "selected"),
                    "native feature does not own the stored local group and mark",
                ),
                (
                    "wrong_atom_identifier",
                    typed_fault(archive, "atom"),
                    "local body atom identities disagree",
                ),
                (
                    "marked_atom_on_bare_boundary",
                    typed_fault(archive, "marked"),
                    "local cylinder has a foreign feature or marked atom",
                ),
                (
                    "crossed_fin",
                    graph_fault(archive, group, kernel, "fin"),
                    "local body has inconsistent fin ownership",
                ),
                (
                    "foreign_vertex",
                    graph_fault(archive, group, kernel, "vertex"),
                    "local cylinder has unqualified bare ownership or identities",
                ),
                (
                    "extra_resident_loop",
                    graph_fault(archive, group, kernel, "inventory"),
                    "local cylinder has an unqualified resident node inventory",
                ),
                (
                    "unequal_rim_radius",
                    graph_fault(archive, group, kernel, "radius"),
                    "local cylinder has inconsistent radius or signed frame",
                ),
            )
        },
    }


def main():
    parser = ArgumentParser(
        description="Verify disclosed local cylinder readback against fresh generated parts and native controls"
    )
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--saved", type=Path, required=True)
    parser.add_argument("--stock", type=Path, required=True)
    args = parser.parse_args()
    cases, controls, tolerance, compact = disclosed_inputs(
        args.packet, args.saved, args.stock
    )
    owners = {
        name: fingerprint((ROOT / name).read_bytes())["sha256"] for name in OWNERS
    }
    proof = fingerprint(Path(__file__).read_bytes())
    for codec in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16-le", "cp1252"):
        lookup(codec)
    for module in (
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Models.DocumentWalk",
    ):
        import_module(module)
    results = {}
    with guard_build():
        generated = {}
        for name, (case, original, saved, cold, reopened) in cases.items():
            model = CASES[name]
            require(
                json.loads(json.dumps(asdict(model))) == case["input"],
                f"neutral model differs from frozen case {name}",
            )
            part, kernel, labels, settings, ambient = make_part(
                model, PureWindowsPath(case["native_path"])
            )
            require(
                part.BytesValue == original and fingerprint(kernel) == case["kernel"],
                f"fresh construction differs for {name}",
            )
            generated[name] = part.BytesValue
            cold_read = inspect_case(part.BytesValue, cold, tolerance, cold=True)
            saved_read = inspect_case(saved, reopened, tolerance, cold=False)
            require(
                cold_read["measured"] == expected_measures(model)
                and saved_read["measured"] == cold_read["measured"],
                f"independent authored model disagrees with {name} reads",
            )
            planar = planar_delta(part, labels, settings, ambient)
            require(
                planar == case["same_locator_planar_control"],
                f"planar read changed for {name}",
            )
            results[name] = {
                "generated": cold_read,
                "native_saved": saved_read,
                "planar_control": planar,
            }
        for name, (source, observed, envelope) in controls.items():
            actual = inspect_case(source, observed, tolerance, cold=False)
            require(
                actual["kernel"]["sha256"] == envelope["local_transmit"]["sha256"],
                f"stock transmit changed: {name}",
            )
            results[name] = actual
        refused = faults(generated["TranslatedZ"])
    print(
        json.dumps(
            {
                "schema": "kit.sw2026.local-cylinder-strict-readback.v1",
                "proof": proof,
                "owning_sources_sha256": owners,
                "native_result_sha256": compact["full_native_result_sha256"],
                "runtime_reader_reads": 0,
                "native_processes_started": 0,
                "heldout_inputs": 0,
                "fresh_generated_inputs_exact": len(cases),
                "ordinary_native_marked_controls": len(cases) + len(controls),
                "same_locator_planar_controls": len(cases),
                "cases": results,
                "refusals": refused,
            },
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
