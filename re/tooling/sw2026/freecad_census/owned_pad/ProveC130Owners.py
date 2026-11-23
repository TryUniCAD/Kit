from argparse import ArgumentParser
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
from json import loads
from pathlib import Path
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TOOLS = HERE.parents[2]
sys.path[:0] = [
    str(TOOLS),
    str(TOOLS / "equations"),
    str(HERE.parent),
    str(HERE.parents[1]),
]
from ProveBlindDormant import (
    CASE,
    CUSTODY,
    EQUATION,
    EQUATION_ARCHIVE,
    EPOCH,
    SOURCE,
    pinned,
)
from ProveNamedWidthDepth import (
    FORMAT,
    audit_publication,
    digest,
    fingerprint,
    launch,
    projection,
    wire,
)

BASE = "6d85ed1cb9ff6c033c5a0017dbfc49ffb52bc146"
BASE_TREE = "dd55dbf729a584a9fbac325303909eb8515c1a67"
NAMED_ARCHIVE = "5380e278a2bfd9745ddb5557b4f3584c21a96a2f26c5f243ce8b4065783093f9"
CONTROL_RECEIPT = "13cdf1ab5fabf48af184cce0f9440a2cb492408ace7498eabb9145c003d120c4"
CHANGED = ["Contents/Config-0", "Contents/Config-0-ResolvedFeatures"]
PRODUCTION = (
    "Archive/Construction/BodyNames/FinishNamedPart.py",
    "Archive/Construction/Part/FinishBlindMut.py",
    "Archive/Construction/Part/SelectBlindEnd.py",
    "Archive/Construction/RectangleAnchors/MakeAnchorPart.py",
    "Core/Reading/ReadAdapter.py",
    "Core/TypedResolved/Equations/WithEqDormant.py",
)


def build_part(source, body_name):
    from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
        AnchorPartInput,
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
    return MakeAnchorPart(
        settings,
        plan,
        anchor,
        WidthDepth=True,
        DormantDepth=source.dormant_m,
        BodyName=body_name,
    )


def replace_property(document, object_name, key, field, value, *, change_row=None):
    metadata = deepcopy(document.metadata["freecad"])
    (actual,) = (owner for owner in metadata["objects"] if owner["name"] == object_name)
    prop = actual["properties"][key]
    prop["children"][0]["attributes"][field] = value
    section = {"freecad": actual}
    if object_name == "Pad":
        (owner,) = document.feature_timeline
        changes = {
            "feature_timeline": (
                replace(owner, attributes={**owner.attributes, **section}),
            )
        }
    elif object_name == "Body":
        (owner,) = document.bodies
        changes = {
            "bodies": (replace(owner, attributes={**owner.attributes, **section}),)
        }
    else:
        raise ValueError("unsupported synthetic property owner")
    if change_row is not None:
        changes["parameters"] = tuple(
            (
                replace(
                    row,
                    value=replace(row.value, value=change_row),
                    attributes={**row.attributes, "freecad_property": prop},
                )
                if row.owner_id == owner.id and row.attributes["freecad_path"] == key
                else row
            )
            for row in document.parameters
        )
    return replace(
        document, metadata={**document.metadata, "freecad": metadata}, **changes
    )


def negative_cases(document, source, preferred):
    from C130GeometryOwners import geometry_owners
    from C130SourceOwners import source_owners
    from CheckScopedPlainWriter import reject

    label = replace(
        document, bodies=(replace(document.bodies[0], name="Foreign caption"),)
    )
    tip = replace_property(document, "Body", "Tip", "value", "Sketch")
    wrong_profile = replace_property(document, "Pad", "Profile", "value", "Origin")
    refine = replace_property(
        document, "Pad", "Refine", "value", "true", change_row=True
    )
    multi = replace_property(
        document, "Pad", "AllowMultiFace", "value", "false", change_row=False
    )
    reports = {}
    for key, malformed, expected in (
        ("body_label", label, "FreeCAD property Label"),
        ("wrong_tip", tip, "FreeCAD property Tip"),
        ("wrong_profile", wrong_profile, "Pad Profile differs"),
        ("refine_policy", refine, "Pad Refine differs"),
        ("multi_face_policy", multi, "Pad AllowMultiFace differs"),
    ):
        reports[key] = reject(
            lambda: source_owners(malformed, CASE), ValueError, expected
        )
    original, *middle, substitute, archive, binding = document.brep_payloads
    assert (
        original.id == "freecad:brep:Body:Shape"
        and substitute.id == "freecad:brep:Pad:Shape"
    )
    assert original.sha256 != substitute.sha256
    fake = replace(original, data=substitute.data, sha256=substitute.sha256)
    crossed = replace(
        document, brep_payloads=(fake, *middle, substitute, archive, binding)
    )
    reports["same_geometry_wrong_payload_owner"] = reject(
        lambda: geometry_owners(crossed, preferred), ValueError, "exact original member"
    )
    reports["invalid_target_label"] = reject(
        lambda: build_part(source, " invalid "), ValueError, "valid ASCII body label"
    )
    return reports


def inspect_atom_and_ends(named, unnamed, full, design):
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Reading.ReadAdapter import NativePartModel
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdOutput import (
        ReadColdOutput,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import (
        ReadPrismParam,
    )
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import (
        IndexFeatures,
    )
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )

    archive = SldprtArchive.from_bytes(named.BytesValue)
    model = NativePartModel(archive, None)
    linked = ReadNativeLink(
        archive,
        model.active_configuration_id,
        RelationConfig=model.configurations[0].name,
    )
    cold = ReadColdOutput(linked)
    assert (
        cold is not None
        and cold.NameValue == full.bodies[0].name
        and full.bodies[0].name != design.bodies[0].name
    )
    owners = IndexFeatures(linked)
    atom, boss = cold.AtomValue, cold.BossValue
    manager = linked.ConfigValue.RootValue.FieldsValue["fd88"]
    old_manager = unnamed.SystemValue.RootValue.FieldsValue["fd88"]
    feature_id = model.operations[0].object_id
    assert boss is owners[feature_id] and manager["atoms"][0]["o"] is atom
    assert boss.FieldsValue["f528"]["items"][0]["o"] is atom
    assert atom.FieldsValue["f12c"] == atom.FieldsValue["f130"] == feature_id
    assert atom.FieldsValue["f140"] == manager["f260"] == old_manager["f260"] + 1
    assert boss.FieldsValue["f498"] == [{"v": atom.FieldsValue["f140"]}]
    assert full.brep.bodies[0].design_body_id == full.bodies[0].id
    assert full.bodies[0].final_feature_id == f"sldprt:feature:{feature_id}"
    end = ReadExtrude(linked, boss, owners).EndValue.FieldsValue
    assert [end[name] for name in ("f08", "f0c", "f8c")] == [1, 0, 0]
    assert end["f90"] is end["f138"] is None
    assert [ReadPrismParam(end[key], True)[2] for key in ("fc8", "fd0")] == [0.0, 0.0]
    return {
        "body_name": cold.NameValue,
        "cold_design_body_id": full.bodies[0].id,
        "cold_body_atom_id": atom.FieldsValue["f140"],
        "creator_feature_id": feature_id,
        "creator_and_result_alias_actual_atom": True,
        "design_only_body_label": design.bodies[0].name,
        "end_mode": [end["f08"], end["f0c"], end["f8c"]],
        "draft_radians": [0.0, 0.0],
    }


def worker(path):
    sys.path[:0] = [str(ROOT / "src"), str(TOOLS / "attached_top_box_source")]
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from C130GeometryOwners import geometry_owners
    from C130SourceOwners import source_owners
    from CheckScopedPlainWriter import WriterAudit
    from ProveFcstdCorner import prewarm
    from VerifyLocalSketchExpr import guard_source

    path = Path(path).resolve(strict=True)
    isolated = "".join(x for x in str(path).casefold() if x.isalnum())
    assert not any(marker in isolated for marker in ("heldout", "holdout", "sealed"))
    pinned(path, SOURCE)
    source_reads, denied = guard_source(path, ROOT / "src")
    document = open_document(
        path,
        source_format="freecad.fcstd",
        strict=True,
        include_brep=True,
        include_tessellation=True,
    )
    assert document.source.sha256 == SOURCE
    document.assert_valid()
    consumed = len(source_reads)
    before = document.to_json(indent=None).encode()
    prewarm()
    guard = WriterAudit(ROOT / "src", Path("unused.SLDPRT"))
    sys.addaudithook(guard.observe)
    guard.phase = "prepare"
    try:
        source = source_owners(document, CASE)
        named = build_part(source, source.body_name)
        unnamed = build_part(source, source.corner.recipe.FeatureName)
        assert digest(named.BytesValue) == NAMED_ARCHIVE
        full = open_document(named.BytesValue, source_format=FORMAT, strict=True)
        design = open_document(
            named.BytesValue, source_format=FORMAT, strict=True, include_brep=False
        )
        observed = {
            "full": projection(full, True),
            "design_only": projection(design, False),
        }
        compared = geometry_owners(document, full)
        native = inspect_atom_and_ends(named, unnamed, full, design)
        assert native["body_name"] == source.body_name
        assert observed["full"]["dormant"]["value_mm"] == source.dormant_m * 1000
        original_id = source.pad_parameters["Length2"]["parameter_id"]
        (original,) = (row for row in document.parameters if row.id == original_id)
        assert original.owner_id == source.body_roles["tip_feature"] and original.expression is None
        portable = observed["full"]["portable_dormant_parameter"]
        assert portable == observed["design_only"]["portable_dormant_parameter"]
        assert portable["value_mm"] == original.value.value
        for projected in (full, design):
            restored = type(projected).from_json(projected.to_json(indent=None))
            assert restored.parameters == projected.parameters
            assert restored.feature_timeline == projected.feature_timeline
        observed["dormant_source_join"] = {
            "source_parameter_id": original.id,
            "source_owner_id": original.owner_id,
            "target_parameter_id": portable["id"],
            "target_owner_id": portable["owner_id"],
            "portable_json": True,
        }
        changed_depth = source.dormant_m * 0.75
        changed = build_part(replace(source, dormant_m=changed_depth), source.body_name)
        changed_read = open_document(changed.BytesValue, source_format=FORMAT, strict=True)
        (changed_row,) = (row for row in changed_read.parameters if row.id == portable["id"])
        (changed_boss,) = (row for row in changed_read.feature_timeline if row.id == portable["owner_id"])
        assert changed_row.value == changed_boss.definition.second_length
        assert changed_row.value.value == changed_depth * 1000 and changed_row.value != original.value
        assert changed_boss.definition.second_end_condition is None and changed_read.brep == full.brep
        assert changed_read.bodies == full.bodies and changed.BytesValue != named.BytesValue
        observed["varied_model_dormant_value"] = {
            "value_mm": changed_row.value.value, "archive_sha256": digest(changed.BytesValue),
            "same_geometry_and_owner": True,
        }
        assert tuple(unnamed.StreamsValue) == tuple(named.StreamsValue)
        delta = [
            key
            for key in named.StreamsValue
            if named.StreamsValue[key] != unnamed.StreamsValue[key]
        ]
        assert sorted(delta) == CHANGED
        refusals = negative_cases(document, source, full)
        publication = {
            "intact_fcstd": audit_publication(document),
            "named_native_readback": audit_publication(full),
        }
        assert document.to_json(indent=None).encode() == before
    finally:
        guard.phase = "done"
    assert (
        consumed > 0
        and len(source_reads) == consumed
        and not denied
        and not guard.denied
        and not guard.target_opens
    )
    pinned(path, SOURCE)
    return {
        "original_sha256": SOURCE,
        "original_intake_reads": consumed,
        "unchanged_model_sha256": digest(before),
        "source_document_label": source.document_label,
        "source_body": source.body_roles,
        "source_pad_rows": source.pad_parameters,
        "lineage": compared,
        "native_part": native,
        "named_archive": fingerprint(
            SldprtArchive.from_bytes(named.BytesValue), named.BytesValue
        ),
        "derived_body_archive": fingerprint(
            SldprtArchive.from_bytes(unnamed.BytesValue), unnamed.BytesValue
        ),
        "named_stream_changes": sorted(delta),
        "readback": observed,
        "refusals": refusals,
        "publication_refusals": publication,
        "runtime_data_reads": 0,
    }


def run_worker(path):
    child = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker"),
        input=wire({"source": path}),
        capture_output=True,
        timeout=120,
    )
    if child.returncode or child.stderr:
        sys.stderr.buffer.write(child.stderr)
        raise ValueError("guarded C130 owner process failed")
    return loads(child.stdout)


def run_census(inventory, equation):
    (row,) = (
        entry
        for entry in loads(pinned(inventory, CUSTODY))["files"]
        if entry["case_id"] == CASE
    )
    assert row["sha256"] == SOURCE
    joint = run_worker(row["source_path"])
    assert joint == run_worker(row["source_path"])
    original = loads(
        pinned(
            ROOT / "re/solidworks/measurements/2026/SdkNamedWidthDepth01.json",
            CONTROL_RECEIPT,
        )
    )
    observed = joint["derived_body_archive"]
    assert observed["sha256"] == original["c130"]["archive"]["sha256"]
    assert observed["streams"] == original["c130"]["archive"]["streams"]
    request = loads(pinned(equation, EQUATION))
    assert (
        check_output(("git", "rev-parse", f"{BASE}:src"), cwd=ROOT).decode().strip()
        == BASE_TREE
    )
    with TemporaryDirectory(prefix="KitC130OwnerBase.") as folder:
        frozen = Path(folder)
        raw = check_output(("git", "archive", BASE, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(raw)) as archive:
            archive.extractall(frozen, filter="data")
        old = launch("legacy", frozen / "src", request)
        current = launch("legacy", ROOT / "src", request)
    assert old == current and old["archive"]["sha256"] == EQUATION_ARCHIVE
    source_files = [
        ROOT / "src/convert/adapters/solidworks" / name for name in PRODUCTION
    ] + [
        HERE,
        HERE.with_name("C130SourceOwners.py"),
        HERE.with_name("C130GeometryOwners.py"),
    ]
    return {
        "base": BASE,
        "base_src_tree": BASE_TREE,
        "source_custody_manifest": CUSTODY,
        "runtime_data_reads": 0,
        "sdk_processes": 4,
        "native_processes": 0,
        "c130": joint,
        "ordinary_equation_unchanged": current,
        "old_c130_receipt": CONTROL_RECEIPT,
        "evidence_sources": {
            str(path.relative_to(ROOT)): digest(path.read_bytes())
            for path in source_files
        },
        "original_source_admitted": False,
        "corpus_credit": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--equation", type=Path)
    args = parser.parse_args()
    if args.worker:
        result = worker(loads(sys.stdin.buffer.read())["source"])
    else:
        if args.inventory is None or args.equation is None:
            parser.error("--inventory and --equation are needed")
        result = run_census(args.inventory, args.equation)
    sys.stdout.buffer.write(wire(result))
