from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
TOOLS = HERE.parents[1]
BASE = "93743aea17b8d9c4ab396e207cd779bc543f3cb0"
BASE_TREE = "3a578b32d38cace9219136e3bdc7881cfe847afa"
FORMAT = "solidworks.sldprt"
CANDIDATE = "5c430281a3daec6bb029eb55282b0cf7ac2cc7d02d81fb26a802b0f66e47f3db"
META = "solidworks.typed_resolved_semantics"
STATUS = "local_width_depth_equation"
SOURCES = (
    "src/convert/adapters/solidworks/Core/Reading/ReadAdapter.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/DepthOwner.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Equations/CheckEqParams.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Equations/HasNamedEq.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Equations/ReadEqDormant.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Equations/ReadEqWidth.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Equations/ReadWidthDepth.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Equations/TryWidthDepth.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Equations/WidthDepthLink.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/CheckPrismEnd.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/ReadNoCache.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/ReadPrismPlan.py",
    "re/tooling/sw2026/equations/BuildNamedWidthDepth.py",
    "re/tooling/sw2026/equations/ProveNamedWidthDepth.py",
)
FAULTS = {
    "foreign_dormant_parameter": "named width depth requires a separate owned dormant dimension",
    "duplicate_dormant_identity": "named width depth requires a separate owned dormant dimension",
    "active_reverse_slot": "local width-depth equation requires an ordinary forward blind boss",
    "dormant_equation_clone": "local equation dimension does not alias its exact live owner",
    "height_dependency": "native relation is outside the enabled local width-depth expression",
}


def digest(raw):
    return sha256(raw).hexdigest()


def wire(data):
    return (dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def fingerprint(archive, raw):
    return {
        "sha256": digest(raw),
        "bytes": len(raw),
        "streams": {
            key: {"sha256": digest(value), "bytes": len(value)}
            for key, value in sorted(archive.streams.items())
        },
    }


def legacy(request, sdk):
    from convert import open_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Preparation.Equations.PrepareEqPart import (
        PrepareEqPart,
    )
    from BuildSdkWidthDepth import author_document
    from CheckScopedPlainWriter import WriterAudit
    from ProveCircleEndPort import preload

    source = author_document(request)
    options = WriteOptions(
        values={"final_destination": request["settings"]["output"]["path_name"]}
    )
    preload()
    guard = WriterAudit(sdk, Path("unused.SLDPRT"))
    sys.addaudithook(guard.observe)
    guard.phase = "prepare"
    try:
        prepared = PrepareEqPart(source, BytesIO(), request["sdk_created_at"], options)
        raw = prepared.BytesValue
        archive = SldprtArchive.from_bytes(raw)
        reports = {}
        for full in (True, False):
            projected = open_document(
                raw, source_format=FORMAT, strict=True, include_brep=full
            )
            projected.assert_valid()
            (depth,) = (
                row for row in projected.parameters if row.expression is not None
            )
            (ref,) = (
                row
                for row in projected.parameters
                if row.id in depth.expression.parameter_ids
            )
            assert ref.name == depth.name == "D1" and ref.owner_id != depth.owner_id
            assert (
                STATUS in projected.metadata[META]
                and "dormant_depth" not in projected.metadata[META][STATUS]
            )
            assert (projected.brep is not None) is full
            reports["full" if full else "design_only"] = digest(
                projected.to_json(indent=None).encode()
            )
    finally:
        guard.phase = "done"
    assert not guard.denied and not guard.target_opens
    return {
        "archive": fingerprint(archive, raw),
        "documents": reports,
        "runtime_data_reads": 0,
    }


def point(value):
    return [value.x, value.y, value.z]


def projection(document, full):
    from interchange import ParameterRole
    from interchange.Features.FeatureExtrude import ExtrudeEnd

    document.assert_valid()
    width, height, length = document.parameters
    (sketch,) = document.sketches
    (body,) = document.bodies
    (profile,) = (step for step in document.feature_timeline if step.name == "Sketch")
    (boss,) = (step for step in document.feature_timeline if step.name == "Pad")
    assert [p.name for p in (width, height, length)] == ["width", "height", "Length"]
    assert [p.value.value for p in (width, height, length)] == [40.0, 20.0, 20.0]
    assert all(p.value.unit == "mm" for p in (width, height, length))
    assert (
        width.role == height.role == ParameterRole.KDriving
        and length.role == ParameterRole.KDerived
    )
    assert (
        width.expression is height.expression is None and length.expression is not None
    )
    assert width.owner_id == height.owner_id == profile.id
    assert length.owner_id == boss.id == body.final_feature_id
    assert profile.sketch_id == boss.sketch_id == sketch.id
    assert boss.input_feature_ids == (profile.id,)
    assert sketch.parameter_ids == (width.id, height.id) and boss.parameter_ids == (
        length.id,
    )
    assert (
        length.expression.source == '"width@Sketch" / 2'
        and length.expression.parameter_ids == (width.id,)
    )
    assert length.attributes["equation_source"] == '"Length@Pad" = "width@Sketch" / 2'
    assert length.attributes["equation_configuration_id"] == 0
    assert (
        boss.definition.end_condition == ExtrudeEnd.KBlind
        and boss.definition.length.value == 20.0
    )
    assert (
        boss.definition.second_length is None
        and boss.definition.second_end_condition is None
    )
    assert not boss.definition.reversed and not boss.definition.symmetric
    assert [
        (row.kind, row.parameter_id) for row in sketch.constraints if row.parameter_id
    ] == [
        ("distance", width.id),
        ("distance", height.id),
    ]
    graph = document.metadata[META]
    assert graph["status"] == "supplemented" and graph["typed_geometry_projection"]
    assert not graph["full_linked_graph"] and not graph["public_writer_qualified"]
    eq = graph[STATUS]
    depth_owner = length.attributes["typed_archive_owner"]
    width_owner = width.attributes["typed_archive_owner"]
    height_owner = height.attributes["typed_archive_owner"]
    dormant = eq["dormant_depth"]
    assert dormant["name"] == "D2" and dormant["value_mm"] == 10.0
    assert depth_owner["dimension_id"] == 22 and depth_owner["slot"] == "f818.f18"
    assert (
        dormant["owner"]["dimension_id"] == 23
        and dormant["owner"]["slot"] == "f818.f20"
    )
    assert depth_owner["stream"] == "Contents/Config-0"
    assert dormant["owner"]["stream"] == "Contents/Config-0-ResolvedFeatures"
    assert eq["target"]["live_handle"]["object_index"] == depth_owner["handle_index"]
    assert (
        eq["dependency"]["live_handle"]["object_index"] == width_owner["handle_index"]
    )
    assert dormant["owner"]["handle_index"] != depth_owner["handle_index"]
    assert (
        eq["dependency"]["live_handle"]["object_index"] != height_owner["handle_index"]
    )
    assert (document.brep is not None) is full and document.brep_payloads == ()
    result = {
        "parameter_ids": [width.id, height.id, length.id],
        "target": depth_owner,
        "width": width_owner,
        "height": height_owner,
        "dormant": dormant,
        "relation": eq["relation"],
        "feature_operation": boss.operation.value,
        "document_sha256": digest(document.to_json(indent=None).encode()),
    }
    if full:
        assert boss.operation.value == "create" and not document.brep.validate(
            frozenset((body.id,))
        )
        topology = body.topology
        counts = [
            topology.solid_count,
            topology.shell_count,
            topology.face_count,
            topology.edge_count,
            topology.vertex_count,
        ]
        extrema = [
            point(topology.bounding_box.minimum),
            point(topology.bounding_box.maximum),
        ]
        assert counts == [1, 1, 6, 12, 8] and topology.valid
        assert topology.volume == 16000.0 and topology.surface_area == 4000.0
        assert extrema == [[0.0, 0.0, 0.0], [40.0, 20.0, 20.0]]
        result["geometry"] = {
            "counts": counts,
            "volume_mm3": topology.volume,
            "area_mm2": topology.surface_area,
            "bounds_mm": extrema,
        }
    return result


def audit_publication(document):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from CheckScopedPlainWriter import reject

    sink = BytesIO(b"caller bytes")
    sink.seek(3)
    values = {"require_native_transfers": True}
    result = {
        "registry": reject(
            lambda: write_document(
                document,
                sink,
                destination_format=FORMAT,
                allow_carrier=False,
                values=values,
            ),
            NotFoundError,
            "does not support the destination",
        ),
        "adapter": reject(
            lambda: SldprtAdapter().write(document, sink, WriteOptions(values=values)),
            NotFoundError,
            "does not support the destination",
        ),
    }
    assert sink.getvalue() == b"caller bytes" and sink.tell() == 3
    return result


def reject_owners(recipe):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import (
        SldprtArchive,
        SldprtFormatError,
    )
    from convert.adapters.solidworks.Core.Reading.ReadAdapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadWidthDepth import (
        ReadWidthDepth,
    )
    from convert.adapters.solidworks.Core.TypedResolved.ProjectTyped import ProjectTyped
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from BuildNamedWidthDepth import build_named
    from CheckScopedPlainWriter import reject

    refusals = {}
    for fault, message in FAULTS.items():
        depth = recipe.DepthValue if fault == "dormant_equation_clone" else 0.01
        raw = build_named(recipe, depth, fault)
        archive = SldprtArchive.from_bytes(raw)
        model = NativePartModel(archive, None)
        linked = ReadNativeLink(
            archive,
            model.active_configuration_id,
            RelationConfig=model.configurations[0].name,
        )
        projected = ProjectTyped(model, linked)
        typed = reject(
            lambda: ReadWidthDepth(projected, linked, archive), ValueError, message
        )
        strict = reject(
            lambda: open_document(raw, source_format=FORMAT, strict=True),
            SldprtFormatError,
            "contains no readable Parasolid payload",
        )
        design = open_document(
            raw, source_format=FORMAT, strict=True, include_brep=False
        )
        assert STATUS not in design.metadata[META]
        refusals[fault] = {
            "archive_sha256": digest(raw),
            "typed_reason": typed,
            "strict_full_reason": strict,
            "typed_design_authority": False,
        }
    return refusals


def c130(request, sdk):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
        ReadLength,
    )
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from BuildNamedWidthDepth import build_named
    from CheckScopedPlainWriter import WriterAudit
    from PlanFcstdCorner import plan_corner
    from ProveBlindDormant import CASE, SOURCE, pinned
    from ProveFcstdCorner import prewarm
    from VerifyLocalSketchExpr import guard_source

    path = Path(request["source"]).resolve(strict=True)
    compact = "".join(c for c in str(path).casefold() if c.isalnum())
    assert path.suffix.casefold() == ".fcstd"
    assert not any(marker in compact for marker in ("heldout", "holdout", "sealed"))
    pinned(path, SOURCE)
    reads, denied = guard_source(path, sdk)
    document = open_document(
        path, source_format="freecad.fcstd", strict=True, include_brep=True
    )
    document.assert_valid()
    assert document.source.sha256 == SOURCE and reads and not denied
    consumed = len(reads)
    prewarm()
    original = document.to_json(indent=None)
    guard = WriterAudit(sdk, Path("unused.SLDPRT"))
    sys.addaudithook(guard.observe)
    guard.phase = "prepare"
    try:
        intent = plan_corner(document, CASE)
        (feature,) = document.feature_timeline
        (dormant,) = (
            param
            for param in document.parameters
            if param.owner_id == feature.id
            and param.id in feature.parameter_ids
            and param.attributes.get("freecad_path") == "Length2"
        )
        assert (
            dormant.value == feature.definition.second_length
            and dormant.expression is None
        )
        assert feature.definition.second_end_condition is None
        raw = build_named(intent.recipe, ReadLength(dormant.value))
        assert digest(raw) == CANDIDATE
        full = open_document(raw, source_format=FORMAT, strict=True)
        design = open_document(
            raw, source_format=FORMAT, strict=True, include_brep=False
        )
        results = {
            "full": projection(full, True),
            "design_only": projection(design, False),
        }
        assert all(
            results["full"][key] == results["design_only"][key]
            for key in (
                "parameter_ids",
                "target",
                "width",
                "height",
                "dormant",
                "relation",
            )
        )
        assert document.to_json(indent=None) == original
        refused = {
            "intact_freecad": audit_publication(document),
            "strict_named_readback": audit_publication(full),
        }
        malformed = reject_owners(intent.recipe)
    finally:
        guard.phase = "done"
    assert (
        not guard.denied
        and not guard.target_opens
        and not denied
        and len(reads) == consumed
    )
    pinned(path, SOURCE)
    return {
        "source_sha256": SOURCE,
        "source_reads_at_intake": consumed,
        "source_dormant_id": dormant.id,
        "archive": fingerprint(SldprtArchive.from_bytes(raw), raw),
        "readback": results,
        "refusals": malformed,
        "publication_refusals": refused,
        "runtime_data_reads": 0,
    }


def launch(mode, sdk, request):
    child = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode, "--sdk", str(sdk)),
        input=wire(request),
        capture_output=True,
        timeout=120,
        check=False,
    )
    if child.returncode or child.stderr:
        sys.stderr.buffer.write(child.stderr)
        raise ValueError(f"guarded {mode} process failed")
    return loads(child.stdout)


def control(inventory, equation):
    sys.path[:0] = [str(TOOLS / "freecad_census")]
    from ProveBlindDormant import (
        CASE,
        CUSTODY,
        EQUATION,
        EQUATION_ARCHIVE,
        SOURCE,
        check_native_domain,
        pinned,
    )

    (row,) = (
        row
        for row in loads(pinned(inventory, CUSTODY))["files"]
        if row["case_id"] == CASE
    )
    assert row["sha256"] == SOURCE
    request = loads(pinned(equation, EQUATION))
    sdk = ROOT / "src"
    assert (
        check_output(("git", "rev-parse", f"{BASE}:src"), cwd=ROOT).decode().strip()
        == BASE_TREE
    )
    with TemporaryDirectory(prefix="KitNamedWidthDepth.") as folder:
        baseline = Path(folder)
        archived = check_output(("git", "archive", BASE, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(archived)) as files:
            files.extractall(baseline, filter="data")
        before = launch("legacy", baseline / "src", request)
        after = launch("legacy", sdk, request)
    assert after == before and before["archive"]["sha256"] == EQUATION_ARCHIVE
    named = launch("c130", sdk, {"source": row["source_path"]})
    assert named == launch("c130", sdk, {"source": row["source_path"]})
    return {
        "base": BASE,
        "base_src_tree": BASE_TREE,
        "request_sha256": {"c130_inventory": CUSTODY, "legacy_width_depth": EQUATION},
        "sdk_processes": 4,
        "native_processes": 0,
        "source_sha256": {name: digest((ROOT / name).read_bytes()) for name in SOURCES},
        "native_dormant_contrast": check_native_domain(),
        "c130": named,
        "canonical_d1_unchanged": after,
        "new_fcstd_publications": 0,
        "new_native_qualifications": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--equation", type=Path)
    parser.add_argument("--worker", choices=("legacy", "c130"))
    parser.add_argument("--sdk", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.path[:0] = [str(args.sdk), str(TOOLS), str(HERE.parent)]
        if args.worker == "c130":
            sys.path[:0] = [
                str(TOOLS / "freecad_census"),
                str(TOOLS / "attached_top_box_source"),
            ]
        result = (legacy if args.worker == "legacy" else c130)(
            loads(sys.stdin.buffer.read()), args.sdk
        )
    else:
        if args.inventory is None or args.equation is None:
            parser.error("--inventory and --equation are required for the controller")
        result = control(args.inventory, args.equation)
    sys.stdout.buffer.write(wire(result))
