from argparse import ArgumentParser
from base64 import b64decode, b64encode
from dataclasses import replace
from json import loads
from pathlib import Path
from subprocess import check_output, run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TOOLS = HERE.parents[2]
sys.path[:0] = [
    str(ROOT / "src"),
    str(TOOLS),
    str(TOOLS / "equations"),
    str(HERE.parent),
    str(HERE.parents[1]),
    str(TOOLS / "attached_top_box_source"),
]

from ProveBlindDormant import CASE, CUSTODY, EPOCH, SOURCE, pinned, wire
from ProveC130Owners import NAMED_ARCHIVE, build_part
from ProveNamedWidthDepth import audit_publication, digest, fingerprint, projection

BASE = "9dca0bd65a4762962b0d71b896cdd354eb405a98"
MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
BASELINE_RECEIPT = "160f60518f6e0e8a8137f90ce9171628f9908671f076e1a4f28cec870fc71ba3"
COMBINED_ARCHIVE = "a320ec8d8ec09844934b7e3c625d4722527542603cfc1ec82feb6f6fcd44bd4a"
AXIS_STREAMS = (
    "Contents/CMgr",
    "Contents/Config-0-ModelHeader",
    "Contents/Config-0-ResolvedFeatures",
    "Header2",
    "swXmlContents/KeyWords",
)
PREFIX = "src/convert/adapters/solidworks/"
RULES = (
    "Archive/Construction/Datums/PrincipalAxes/EmitAxesPart.py",
    "Archive/Construction/Datums/PrincipalAxes/FinishAxesPart.py",
    "Core/TypedResolved/Equations/ReadEqFeatures.py",
    "Core/TypedResolved/Equations/ReadWidthDepth.py",
    "Core/TypedResolved/Geometry/Axes/ReadAxisGeom.py",
    "Core/TypedResolved/Geometry/CheckPrismScope.py",
    "Core/TypedResolved/Geometry/ReadNoCache.py",
)


def checked_axes(document):
    from convert.adapters.freecad.Native import LoadNative, NativeObjectA, NativeSource
    from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.ProjectBoxAxes import (
        ProjectBoxAxes,
    )
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadOriginAxes import (
        ReadOriginAxes,
    )

    package = NativeDocPair(document)
    assert package is not None and package[0].sha256 == document.source.sha256
    archive = LoadNative(package[0].data)
    assert (
        NativeSource(package[0].data, document.source.path, archive) == document.source
    )
    assert tuple(document.metadata["freecad"]["objects"]) == tuple(
        NativeObjectA(row) for row in archive.objects
    )
    axis_source = ReadOriginAxes(document, CheckPlanes=True)
    return axis_source, ProjectBoxAxes(axis_source)


def derived_axes(document, source, axes):
    from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
        AnchorPartInput,
    )
    from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyKeys import (
        ReadBodyKeys,
    )
    from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.CheckAxisInput import (
        CheckAxisInput,
    )
    from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.FinishAxesPart import (
        FinishAxesPart,
    )
    from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
        PersistentIds,
    )
    from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeAnchorPart import (
        MakeAnchorPart,
    )
    from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
        RectDimInput,
    )
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import (
        MakePartRecipe,
    )

    plan = source.corner.recipe
    settings = MakePartRecipe(plan, EPOCH)
    CheckAxisInput(axes, settings)
    allocator = PersistentIds()
    margin = min(plan.WidthValue, plan.HeightValue) / 4
    anchor = AnchorPartInput(
        "corner",
        RectDimInput(
            (plan.WidthValue / 2, -margin),
            (plan.WidthValue + margin, plan.HeightValue / 2),
            settings.DesignIntent,
            settings.SelectedLeader,
            False,
        ),
    )
    stock = MakeAnchorPart(
        settings,
        plan,
        anchor,
        WidthDepth=True,
        AllocatorValue=allocator,
        DormantDepth=source.dormant_m,
        BodyName=source.body_name,
    )
    assert digest(stock.BytesValue) == NAMED_ARCHIVE
    owners = {row.id: row for row in document.parameters}
    ordinate_keys = ReadBodyKeys(
        replace(
            document,
            parameters=tuple(owners[key] for key in source.corner.source_parameter_ids),
        ),
        plan,
        settings,
    )
    return FinishAxesPart(
        stock, settings, allocator, axes, ordinate_keys, PartRelations=True
    )


def target_axes(archive, plan):
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import (
        ReadHeaderGraph,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.Axes.ReadPrismAxes import (
        ReadPrismAxes,
    )
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import (
        IndexFeatures,
    )
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import (
        ReadNativeName,
    )

    link = ReadNativeLink(archive, 0, RelationConfig=plan.ConfigName)
    features = IndexFeatures(link)
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    axes = ReadPrismAxes(link, header, features)
    return axes, [
        {
            "feature_id": NativeNodeId(axis.NodeValue),
            "name": ReadNativeName(axis.NodeValue),
            "plane_ids": [NativeNodeId(pick.PlaneValue) for pick in axis.PicksValue],
            "plane_names": [
                ReadNativeName(pick.PlaneValue) for pick in axis.PicksValue
            ],
            "segment_mm": [
                [coordinate * 1000 for coordinate in point]
                for point in (axis.StartValue, axis.EndValue)
            ],
        }
        for axis in axes.AxesValue
    ]


def source_axes_match(source_axes, intent, matched):
    for original, planned, current in zip(
        source_axes.AxisValues, intent.AxisValues, matched, strict=True
    ):
        assert current["name"] == planned.NameValue == original.LabelValue
        assert (
            len(set(current["plane_ids"])) == 2
            and planned.IsVisible == original.RecordShown
        )
        current["source_object_id"] = original.RecordId
        current["source_role"] = original.RoleName
        current["source_direction"] = list(planned.DirectionValue)
        current["source_model_visible"] = original.RecordShown


def verify_axis_read(document, matched, full):
    from interchange.Features.FeaturePlaneAxis import PlaneAxis

    expected_ids = [f"sldprt:feature:{row['feature_id']}" for row in matched]
    steps = tuple(step for step in document.feature_timeline if step.id in expected_ids)
    assert [step.id for step in steps] == expected_ids, [
        (step.id, step.name) for step in document.feature_timeline
    ]
    if full:
        assert steps == document.feature_timeline[-3:]
        assert len({key for axis in steps for key in axis.selection_ids}) == 6
    assert [step.name for step in steps] == [row["name"] for row in matched]
    assert not any(step.suppressed for step in steps)
    picks = {pick.id: pick for pick in document.selections}
    for step, row in zip(steps, matched, strict=True):
        if not full:
            assert not isinstance(step.definition, PlaneAxis)
            continue
        definition = step.definition
        assert isinstance(definition, PlaneAxis)
        assert step.input_feature_ids == tuple(
            f"sldprt:feature:{key}" for key in row["plane_ids"]
        )
        assert step.selection_ids == (
            definition.FirstPlaneSelectionId,
            definition.SecondPlaneSelectionId,
        )
        assert step.attributes["solidworks.native_axis_hidden"] is False
        assert [
            [point.x, point.y, point.z]
            for point in (definition.StartMm, definition.EndMm)
        ] == row["segment_mm"]
        for key, target, name in zip(
            step.selection_ids, row["plane_ids"], row["plane_names"], strict=True
        ):
            pick = picks[key]
            (path,) = pick.path
            assert (
                pick.name == name and pick.query["native_owner_id"] == row["feature_id"]
            )
            assert (
                pick.query["native_target_id"] == target and pick.provenance is not None
            )
            assert (
                path.entity_kind == "support_plane"
                and path.entity_id == f"sldprt:plane:{target}"
            )
    return {
        "feature_ids": expected_ids,
        "timeline_order": [step.order for step in steps],
        "typed_plane_axes": sum(
            isinstance(step.definition, PlaneAxis) for step in steps
        ),
        "ordered_plane_selections": sum(len(step.selection_ids) for step in steps),
    }


def verify_public_read(raw, matched, source):
    from convert import open_document

    outcome, equations = {}, {}
    diagnostic_fields = ("document_sha256", "feature_operation", "geometry")
    for mode, full in (("design_only", False), ("full", True)):
        public = open_document(
            raw, source_format="solidworks.sldprt", strict=True, include_brep=full
        )
        assert (
            len(public.feature_timeline) == 22
            and len(public.sketches) == len(public.bodies) == 1
        )
        assert public.bodies[0].name == (source.body_name if full else "Body 1")
        axis_read = verify_axis_read(public, matched, full)
        model_read = projection(public, full)
        portable = type(public).from_json(public.to_json(indent=None))
        assert (
            portable.parameters == public.parameters
            and portable.feature_timeline == public.feature_timeline
        )
        assert (
            portable.selections == public.selections
            and portable.sketches == public.sketches
        )
        equations[mode] = {
            key: value
            for key, value in model_read.items()
            if key not in diagnostic_fields
        }
        outcome[mode] = {
            **axis_read,
            **{key: model_read[key] for key in diagnostic_fields if key in model_read},
            "feature_count": len(public.feature_timeline),
            "body_name": public.bodies[0].name,
            "json_parameter_feature_selection_equality": True,
        }
    assert equations["full"] == equations["design_only"]
    outcome["shared_equation_owners"] = equations["full"]
    return outcome, public


def wrong_axis_owner(axes, archive):
    from convert.adapters.solidworks.Core.TypedResolved.Equations.ReadEqFeatures import (
        ReadEqFeatures,
    )
    from CheckScopedPlainWriter import reject

    link = axes.LinkValue
    fields = axes.AxesValue[0].PicksValue[0].ComponentValue.FieldsValue
    owner = fields["owner"]
    assert owner is link.ConfigValue.RootValue
    fields["owner"] = axes.AxesValue[1].NodeValue
    try:
        return reject(
            lambda: ReadEqFeatures(link, archive),
            ValueError,
            "angular datum requires its actual local selection",
        )
    finally:
        fields["owner"] = owner


def hidden_axis_refusal(axes, archive):
    from convert import open_document
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import (
        BuildSldprt,
        SldprtFormatError,
    )
    from CheckScopedPlainWriter import reject

    link = axes.LinkValue
    resolved = link.ResolvedValue
    fields = axes.AxesValue[0].NodeValue.FieldsValue
    assert fields["hidden"] == 0
    streams = dict(archive.streams)
    fields["hidden"] = 1
    try:
        streams[link.StreamName] = WriteResolMut(
            resolved.RootsValue,
            resolved.ExtraFields,
            19000,
            link.ConfigValue.MapValue,
            resolved.ContextValue,
        )[0]
    finally:
        fields["hidden"] = 0
    raw = BuildSldprt(streams, FormatVersion=4)
    return {
        "sha256": digest(raw),
        "strict_full": reject(
            lambda: open_document(raw, source_format="solidworks.sldprt", strict=True),
            SldprtFormatError,
            "contains no readable Parasolid payload",
        ),
    }


def feature_inputs(source):
    corner = source.corner
    return {
        "body": source.body_roles,
        "source_support_plane": corner.source_support_id,
        "shared_endpoint_constraints": list(corner.local_rule_ids),
        "unary_line_constraints": list(corner.axis_rule_ids),
        "dimension_constraints": list(corner.driver_rule_ids),
        "origin_constraint": corner.origin_rule_id,
        "width_height_primary_source_ids": list(corner.source_parameter_ids),
        "dormant_length_source_id": source.pad_parameters["Length2"]["parameter_id"],
    }


def worker(raw_request):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from C130GeometryOwners import geometry_owners
    from C130SourceOwners import source_owners
    from CheckScopedPlainWriter import WriterAudit
    from ProveFcstdCorner import prewarm
    from VerifyLocalSketchExpr import guard_source
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import (
        MakePartRecipe,
    )

    source_path = Path(raw_request["source"]).resolve(strict=True)
    isolated = "".join(mark for mark in str(source_path).casefold() if mark.isalnum())
    assert source_path.suffix.casefold() == ".fcstd"
    assert not any(mark in isolated for mark in ("heldout", "holdout", "sealed"))
    pinned(source_path, SOURCE)
    source_reads, denied = guard_source(source_path, ROOT / "src")
    document = open_document(
        source_path,
        source_format="freecad.fcstd",
        strict=True,
        include_brep=True,
        include_tessellation=True,
    )
    assert document.source.sha256 == SOURCE
    document.assert_valid()
    consumed = len(source_reads)
    intake = document.to_json(indent=None)
    prewarm()
    guard = WriterAudit(ROOT / "src", Path("unused.SLDPRT"))
    sys.addaudithook(guard.observe)
    guard.phase = "prepare"
    try:
        source = source_owners(document, CASE)
        source_axes, intent = checked_axes(document)
        stock = build_part(source, source.body_name)
        assert digest(stock.BytesValue) == NAMED_ARCHIVE
        stock_full = open_document(
            stock.BytesValue, source_format="solidworks.sldprt", strict=True
        )
        stock_only = SldprtArchive.from_bytes(stock.BytesValue)
        baseline_projection = projection(stock_full, True)
        combined = derived_axes(document, source, intent)
        target = SldprtArchive.from_bytes(combined.BytesValue)
        axes, matched = target_axes(target, source.corner.recipe)
        source_axes_match(source_axes, intent, matched)
        refused_owner = wrong_axis_owner(axes, target)
        refused_visibility = hidden_axis_refusal(axes, target)
        outcome, public = verify_public_read(combined.BytesValue, matched, source)
        assert baseline_projection["geometry"] == outcome["full"]["geometry"]
        assert stock_full.brep == public.brep
        assert stock_full.sketches == public.sketches
        changed_streams = tuple(
            key
            for key in sorted(target.streams)
            if stock_only.streams.get(key) != target.streams[key]
        )
        assert (
            set(stock_only.streams) == set(target.streams)
            and changed_streams == AXIS_STREAMS
        )
        lineage = geometry_owners(document, public)
        assert document.to_json(indent=None) == intake
        retained = audit_publication(document)
        locator = MakePartRecipe(source.corner.recipe, EPOCH).OutputValue
    finally:
        guard.phase = "done"
    assert (
        consumed
        and consumed == len(source_reads)
        and not denied
        and not guard.denied
        and not guard.target_opens
    )
    pinned(source_path, SOURCE)
    return {
        "source_sha256": SOURCE,
        "original_retained": True,
        "runtime_data_reads": 0,
        "native_processes": 0,
        "whole_source_admitted": False,
        "source_origin": {
            "object_id": source_axes.OriginId,
            "label": source_axes.OriginLabel,
            "model_visible": source_axes.RecordShown,
        },
        "source_feature_inputs": feature_inputs(source),
        "source_shape_correspondence": lineage,
        "source_axis_targets": matched,
        "bad_axis_owner_refusal": refused_owner,
        "hidden_axis_strict_refusal": refused_visibility,
        "original_boundary": retained,
        "public_readback": outcome,
        "baseline_archive": fingerprint(stock_only, stock.BytesValue),
        "stock_sketch_unchanged": True,
        "axis_stream_differences": list(changed_streams),
        "target_self_path": locator.PathName,
        "target_self_saved_at": locator.SavedAt,
        "combined_archive": fingerprint(target, combined.BytesValue),
        **(
            {"scratch_candidate_b64": b64encode(combined.BytesValue).decode("ascii")}
            if raw_request["emit"]
            else {}
        ),
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        result = worker(loads(sys.stdin.buffer.read()))
    else:
        assert args.inventory is not None
        if args.candidate is not None:
            assert not args.candidate.resolve().is_relative_to(ROOT)
            assert (
                not args.candidate.exists()
                and args.candidate.suffix.casefold() == ".sldprt"
            )
        (row,) = (
            entry
            for entry in loads(pinned(args.inventory, CUSTODY))["files"]
            if entry["case_id"] == CASE
        )
        assert row["sha256"] == SOURCE
        outcomes = [
            run(
                (sys.executable, "-I", "-B", str(HERE), "--worker"),
                input=wire(
                    {"source": row["source_path"], "emit": args.candidate is not None}
                ),
                check=False,
                capture_output=True,
                timeout=120,
            )
            for _ in range(2)
        ]
        for child in outcomes:
            if child.returncode or child.stderr:
                sys.stderr.buffer.write(child.stderr)
                raise ValueError("guarded C130 axis process failed")
        assert outcomes[0].stdout == outcomes[1].stdout
        case = loads(outcomes[0].stdout)
        baseline = loads(
            pinned(MEASUREMENTS / "SdkC130SourceOwners01.json", BASELINE_RECEIPT)
        )
        assert case["baseline_archive"] == baseline["c130"]["named_archive"]
        assert case["combined_archive"]["sha256"] == COMBINED_ARCHIVE
        if args.candidate is not None:
            candidate = b64decode(case.pop("scratch_candidate_b64"), validate=True)
            assert digest(candidate) == COMBINED_ARCHIVE
            with args.candidate.open("xb") as destination:
                destination.write(candidate)
        manifest = {
            PREFIX + path: digest((ROOT / (PREFIX + path)).read_bytes())
            for path in RULES
        }
        manifest[str(HERE.relative_to(ROOT))] = digest(HERE.read_bytes())
        assert (
            check_output(("git", "merge-base", "HEAD", BASE), cwd=ROOT).decode().strip()
            == BASE
        )
        result = {
            "guarded_processes": len(outcomes),
            "corpus_credit": 0,
            "scope": CASE,
            "base_revision": BASE,
            "source_custody_sha256": CUSTODY,
            "previous_stock_proof_sha256": BASELINE_RECEIPT,
            "changed_code_sha256": manifest,
            "case": case,
        }
    sys.stdout.buffer.write(wire(result))


if __name__ == "__main__":
    main()
