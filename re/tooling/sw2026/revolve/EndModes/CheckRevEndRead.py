from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from math import tau
from pathlib import Path
from subprocess import run
from sys import executable, path, stdin

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve()
path[:0] = [
    str(ROOT / "src"),
    str(ROOT),
    str(HERE.parent),
    str(HERE.parent.parent / "PrincipalReader"),
]

from AuditPrincipalReader import check_projection, make_guard
from MakePrincipalCold import make_cold
from RevolveSectorMath import (
    authored_sector,
    check_brep,
    check_measures,
    same_point,
    xyz,
)
from convert import open_document
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    IsCacheAbsent,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import (
    PrismNodes,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.CheckRevAngles import (
    CheckRevAngles,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.ReadRevGeom import (
    KRevolveGeomClasses,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.Geometry.BuildRevBodyGeom import (
    BuildRevBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import (
    ReadRevOwners,
)
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.RevolveSpan import GetAngleSpan
from interchange.document.Behavior.DocumentIo import FromJson, ToJson
from interchange.document.Models.DocumentModel import CadDocument

BASE = "b18caa86c15d2c65ad95c9a572bbc9d06701da8c"
PORTABLE = "f9a0e264b0171e3b39cff19701fef179223d66bf"
DISCOVERY = "c83d0c4a1aad8e6e05bd40d80988a47b91fdc6e202403b398e169010d723969c"
RECOVERY = "1ee1be8250ed342bcf912c1758eb9a994b9ac9857b69ab9960a4152a3b445061"
WIRE = "68a596627dc3f3c5f2ff30efb7d3b6238936ff015874020213e5be57bc3edac4"
GENERATED = "9f14cec8aebf970eb461b4b2e4decc2dd1f73bdec27db71a7e7d6db3c5831061"
GENERATED_TREE = "1082f9bb9b69d0b2f2ba10c0902e7694cbe9a860"
CASES = ("EndSingle", "EndMidplane", "EndTwo", "EndTwoReverse")
MODES = {
    "single": ("one_sided", "single_blind", 0),
    "midplane": ("symmetric_full", "mid_plane", 1),
    "two": ("two_sided", "two_blind_ends", 2),
}
REVOLVE_OWNER_PREFIX = "src/convert/adapters/solidworks/Core/TypedResolved/Revolves"
READER_PATHS = (
    "src/interchange/Features/FeatureAngleRev.py",
    "src/interchange/Features/RevolveSpan.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/BodyNames/Revolves/ReadRevolveBody.py",
) + tuple(
    f"{REVOLVE_OWNER_PREFIX}/{name}.py"
    for name in (
        "Geometry/BuildRevBodyGeom",
        "Geometry/CheckRevAngles",
        "Geometry/MakeRevMerid",
        "Geometry/ReadRevGeom",
        "Projection/ApplyRevDoc",
        "Projection/BindRevParams",
        "Projection/BindRevStep",
        "Projection/MakeRevParam",
        "Projection/ReportRevolve",
        "ReadRevAngle",
        "ReadRevDim",
        "ReadRevEnd",
        "ReadRevMode",
        "ReadRevolve",
        "RevolveEnd",
        "RevolveOwner",
    )
)
VIEWS = {
    "default": {},
    "history": {"include_brep": False, "include_tessellation": False},
}
LEGACY = {
    "x": (
        "1a55827ff53acecbc66c75f890676aff9e16ab9433c830af13bd749f4943a61b",
        "d4cb71ccad4fc083ac8f323c378e61181e49d22f82fd083b4fb97367edea5eaf",
        "4453cbfdf334b6cec5171a55737660878b0ada8e2095664f9c822f88ebc557f1",
    ),
    "y": (
        "e02ce73c671f83aabe9222293c1e92424cb0207e277acf7f6739f56194943273",
        "2b12e09177233666586ba87079c436994aacfaf014797de0c0dbe1f01428b7be",
        "485ec0f992819addf5f2aff8877a86afef33fbb67772f332ecbd777f03fa314d",
    ),
    "z": (
        "1c8ea239e6848d132ec387572d98622bdfafaf05ae1a6b3530ce655f81539907",
        "65370d8414f6852747cc0a73044c3e3d5401a6aae19a01ba7671ad1d7546a17d",
        "46b41d24b7dc6666fb924941a12d82915a583652ff4612be4fedbe633de11607",
    ),
}
LEGACY_SINGLE = (
    "bc443aa00e016fabf15db7e1be865c6d4a348f059b9672769302810e2058248c",
    "07e485bd6575f5742fe585af82dffed573c3dba47e4f20543f898a5781b97fb0",
)


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(pathname, expected):
    raw = pathname.read_bytes()
    assert digest(raw) == expected, pathname
    return raw


def receipt(name, expected):
    return loads(
        pinned(ROOT / "re/solidworks/measurements/2026" / f"{name}.json", expected)
    )


def check_driver(owned, parameter, feature, wire, slot):
    assert (
        parameter.id
        == f"{feature.id.replace(':feature:', ':parameter:')}:{wire['name']}"
    )
    assert (
        parameter.owner_id == feature.id
        and parameter.name == owned.NameValue == wire["name"]
    )
    assert (
        parameter.role is ParameterRole.KDriving
        and parameter.value.kind is ValueKind.KAngle
    )
    assert (
        parameter.value.unit == "rad"
        and parameter.value.value == owned.RadiansValue == wire["radians"]
    )
    attributes = parameter.attributes
    assert attributes["native_dimension_id"] == wire["dimension_id"]
    assert attributes["native_display_index"] == wire["owners"][0]["object_index"]
    assert attributes["native_handle_index"] == wire["owners"][1]["object_index"]
    assert attributes["typed_archive_owner"] == wire["owners"][3] | {
        "slot": f"f8d8.{slot}",
        "value_field": "f58",
    }


def check_owners(link, owner, wire, expected, generated):
    end = owner.EndValue
    assert end.IntervalValue == expected["interval_radians"]
    angles = [end.AlongValue] + (
        [end.AgainstValue] if end.AgainstValue is not None else []
    )
    branches = [
        wire["angle_owners"][slot]
        for slot in ("f18", "f20")
        if wire["angle_owners"][slot] is not None
    ]
    for angle, branch in zip(angles, branches, strict=True):
        chain = (
            angle.DisplayValue,
            angle.HandleValue,
            angle.DimensionValue,
            angle.ParameterValue,
        )
        assert [dict(NativeNodeSpan(link, node)) for node in chain] == branch["owners"]
    feature = owner.NodeValue
    assert all(
        feature.FieldsValue[key] == word for key, word in wire["feature_words"].items()
    )
    fields = feature.FieldsValue["f8d8"].FieldsValue
    assert all(fields[key] == word for key, word in wire["end_words"].items())
    assert fields["f18"] is end.AlongValue.DisplayValue
    assert fields["f20"] is (
        None if end.AgainstValue is None else end.AgainstValue.DisplayValue
    )
    loop = owner.ProfileGraph.LoopValue
    if generated is None:
        assert tuple(sorted(loop.PointsValue)) == (0, 1, 6, 7) and loop.OrderValue == (
            0,
            3,
            2,
            1,
        )
    else:
        assert tuple(sorted(loop.PointsValue)) == loop.OrderValue == (0, 1, 2, 3)
    return angles


def check_document(document, wire, spec, angles):
    document.assert_valid()
    encoded = ToJson(document)
    assert ToJson(FromJson(CadDocument, encoded)) == encoded
    (feature,) = tuple(
        value
        for value in document.feature_timeline
        if type(value.definition) is AngularRevolve
    )
    definition = feature.definition
    side, label, _ = MODES[spec["mode"]]
    assert definition.SideMode == side
    (summary,) = document.metadata["solidworks.typed_revolve_semantics"]["revolutions"]
    assert (
        summary["scope"] == f"ordinary_modern_{label}_rectangular_boss_top_upward_axis"
    )
    assert (
        not summary["public_writer_qualified"]
        and not summary["full_native_tree_qualified"]
    )
    x0 = spec["axis_x_m"] * 1000.0
    live_axis = tuple((x0, value * 1000.0) for value in spec["axis_axial_m"])
    assert same_point(xyz(definition.AxisOrigin), (x0, 0, -live_axis[0][1]))
    assert xyz(definition.AxisDirection) == (0, 0, 1 if spec["reverse"] else -1)
    sketch = next(item for item in document.sketches if item.id == feature.sketch_id)
    selection = next(
        item for item in document.selections if item.id == definition.AxisSelectionId
    )
    (line,) = [item for item in sketch.entities if item.construction]
    assert tuple(item.entity_id for item in selection.path) == (sketch.id, line.id)
    assert len(sketch.entities) == 5 and len(sketch.constraints) == 4
    for a, b in zip((line.geometry.start, line.geometry.end), live_axis, strict=True):
        assert same_point((a.x, a.y), b)
    ids = (definition.AlongParameterId,) + (
        ()
        if definition.AgainstParameterId is None
        else (definition.AgainstParameterId,)
    )
    assert ids == feature.parameter_ids and len(ids) == len(angles)
    parameters = {
        row.id: row for row in document.parameters if row.owner_id == feature.id
    }
    assert parameters.keys() == set(ids)
    for angle, identity, slot in zip(
        angles, ids, ("f18", "f20")[: len(ids)], strict=True
    ):
        check_driver(
            angle, parameters[identity], feature, wire["angle_owners"][slot], slot
        )
    (body,) = document.bodies
    assert body.final_feature_id == feature.id
    return body, digest(encoded.encode())


def refuse(action, message):
    try:
        action()
    except ValueError as error:
        assert message in str(error), str(error)
        return str(error)
    raise AssertionError(f"expected refusal: {message}")


def check_neutral_modes(document):
    (feature,) = tuple(
        value
        for value in document.feature_timeline
        if type(value.definition) is AngularRevolve
    )
    (primary,) = tuple(
        value for value in document.parameters if value.owner_id == feature.id
    )
    total = primary.value.value
    second_id = primary.id + "-authored"
    modes = {}
    for mode, second, expected in (
        ("one_sided", None, (0.0, total)),
        ("symmetric_full", None, (-total / 2, total / 2)),
        ("symmetric", total, (-total, total)),
        ("two_sided", 0.75, (-0.75, total)),
    ):
        definition = replace(
            feature.definition,
            SideMode=mode,
            AgainstParameterId=None if second is None else second_id,
        )
        parameters = document.parameters
        parameter_ids = (primary.id,)
        if second is not None:
            parameters += (
                replace(
                    primary,
                    id=second_id,
                    name="D2",
                    value=replace(primary.value, value=second),
                ),
            )
            parameter_ids += (second_id,)
        edited = replace(feature, definition=definition, parameter_ids=parameter_ids)
        model = replace(
            document,
            parameters=parameters,
            feature_timeline=tuple(
                edited if row is feature else row for row in document.feature_timeline
            ),
        )
        encoded = ToJson(model)
        assert ToJson(FromJson(CadDocument, encoded)) == encoded
        assert GetAngleSpan(total, second, mode) == expected
        modes[mode] = expected
    modes["signed_one_sided"] = GetAngleSpan(-total, None, "one_sided")
    assert modes["signed_one_sided"] == (-total, 0)
    modes["refusals"] = {
        "total_angle_has_extra_link": refuse(
            lambda: replace(
                feature.definition,
                SideMode="symmetric_full",
                AgainstParameterId=second_id,
            ),
            "against parameter disagree",
        ),
        "total_angle_not_positive": refuse(
            lambda: GetAngleSpan(0, None, "symmetric_full"), "positive total angle"
        ),
        "total_angle_over_turn": refuse(
            lambda: GetAngleSpan(2 * tau, None, "symmetric_full"), "at most one turn"
        ),
        "legacy_halves_disagree": refuse(
            lambda: GetAngleSpan(total, 0.75, "symmetric"), "angles must agree"
        ),
    }
    return modes


def check_native_refusals(link, owner):
    feature = owner.NodeValue.FieldsValue
    end = feature["f8d8"].FieldsValue
    along, against = owner.EndValue.AlongValue, owner.EndValue.AgainstValue
    changes = [
        (
            "legacy_feature_display",
            feature,
            "f808",
            along.DisplayValue,
            "modern angular branch",
        ),
        ("legacy_feature_mode", feature, "f820", 1, "direction type"),
        ("wrong_end_condition", end, "f10", 6, "secondary owner disagree"),
        ("reference_end", end, "f118", along.DisplayValue, "alternate angular end"),
        (
            "nonfinite_primary",
            along.ParameterValue.FieldsValue,
            "f58",
            float("inf"),
            "finite",
        ),
    ]
    if owner.EndValue.ModeValue == "symmetric_full":
        changes.extend(
            (
                (
                    "unexpected_mid_plane_secondary",
                    end,
                    "f20",
                    along.DisplayValue,
                    "secondary owner disagree",
                ),
                ("reversed_mid_plane", feature, "f824", 1, "reversed mid plane"),
                (
                    "full_mid_plane",
                    along.ParameterValue.FieldsValue,
                    "f58",
                    tau,
                    "partial turn",
                ),
            )
        )
    if against is not None:
        changes.extend(
            (
                ("missing_secondary", end, "f20", None, "secondary owner disagree"),
                (
                    "aliased_secondary",
                    end,
                    "f20",
                    along.DisplayValue,
                    "distinct D1 and D2",
                ),
                (
                    "same_dimension_id",
                    against.DimensionValue.FieldsValue,
                    "f50",
                    along.DimensionValue.FieldsValue["f50"],
                    "distinct D1 and D2",
                ),
                (
                    "foreign_secondary_class",
                    end,
                    "f20",
                    along.ParameterValue,
                    "moDisplayAngularDim_c",
                ),
                (
                    "nonpositive_secondary",
                    against.ParameterValue.FieldsValue,
                    "f58",
                    0,
                    "positive angle",
                ),
                (
                    "total_over_turn",
                    against.ParameterValue.FieldsValue,
                    "f58",
                    tau,
                    "at most one turn",
                ),
            )
        )
    errors = {}
    for name, fields, key, value, message in changes:
        previous = fields[key]
        try:
            fields[key] = value
            errors[name] = refuse(lambda: ReadRevOwners(link), message)
        finally:
            fields[key] = previous
    return errors


def check_cold_inventory(archive, link, owner, generated):
    assert IsCacheAbsent(archive)
    assert (
        generated["path_and_stream_equal"]
        and generated["runtime_external_access_attempts"] == 0
    )
    for name, row in generated["streams"].items():
        payload = archive.require(name)
        assert (
            row["byte_identity"]
            and len(payload) == row["bytes"]
            and digest(payload) == row["sha256"]
        )
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    nodes = PrismNodes(link, manager, AllowedClasses=KRevolveGeomClasses)
    direct = owner.AngleValue.DisplayValue
    detached = "duplicate or detached angle owners"
    errors = {
        "duplicate_map_owner": refuse(
            lambda: CheckRevAngles((*nodes, direct), owner.EndValue), detached
        ),
        "missing_map_owner": refuse(
            lambda: CheckRevAngles(
                tuple(row for row in nodes if row is not direct), owner.EndValue
            ),
            detached,
        ),
        "detached_map_owner": refuse(
            lambda: CheckRevAngles(
                tuple(replace(direct) if row is direct else row for row in nodes),
                owner.EndValue,
            ),
            detached,
        ),
    }
    return errors


def check_end_part(raw, spec, wire, oracle, audit, generated=None):
    expected = authored_sector(spec)
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    (owner,) = ReadRevOwners(link)
    angles = check_owners(link, owner, wire, expected, generated)
    assert owner.IsReverse is spec["reverse"] is oracle["reverse"]
    assert MODES[spec["mode"]][2] == oracle["api_mode"]
    assert [row.RadiansValue for row in angles] + (
        [0.0] if len(angles) == 1 else []
    ) == oracle["angles_radians"]
    assert owner.EndValue.ModeValue == MODES[spec["mode"]][0]
    result = {}
    for name, options in VIEWS.items():
        count = audit["grammar_reads"]
        doc = open_document(
            raw, source_format="solidworks.sldprt", strict=True, **options
        )
        body, fingerprint = check_document(doc, wire, spec, angles)
        result[name] = {
            "document_sha256": fingerprint,
            "layout_reads": audit["grammar_reads"] - count,
        }
        if name == "history":
            assert doc.brep is None and not doc.brep_payloads
            if spec["name"] == "EndSingle" and generated is None:
                result["neutral_modes"] = check_neutral_modes(doc)
            continue
        assert body.name == "OrdinaryBossRevolve"
        check_brep(doc.brep, body.id, expected)
        computed = any(
            row.code == "sldprt.brep_reconstructed" for row in doc.diagnostics
        )
        if generated is not None:
            assert (
                computed and not doc.brep_payloads and result[name]["layout_reads"] == 0
            )
            check_measures(body.topology, expected, oracle)
            continue
        assert doc.metadata["solidworks.native_body_names"]["status"] == "complete"
        assert not computed and tuple(row.kind for row in doc.brep_payloads) == (
            "partition",
            "deltas",
        )
        result[name]["native_payload_digests"] = [
            row.sha256 for row in doc.brep_payloads
        ]
        before = audit["grammar_reads"]
        cold = BuildRevBody(owner, body.id)
        assert (
            cold.ProducerValue is owner.NodeValue and audit["grammar_reads"] == before
        )
        check_brep(cold.BrepValue, body.id, expected)
        check_measures(cold.TopologyValue, expected, oracle)
    if generated is not None:
        result["angular_inventory_refusals"] = check_cold_inventory(
            archive, link, owner, generated
        )
        result["operator_receipt_stream_digests_checked"] = len(generated["streams"])
    else:
        if spec["name"] == "EndSingle":
            assert (
                tuple(result[key]["document_sha256"] for key in VIEWS) == LEGACY_SINGLE
            )
        result["typed_refusals"] = check_native_refusals(link, owner)
    result["geometry"] = expected
    result["driver_roles"] = [(row.NameValue, row.RadiansValue) for row in angles]
    result["active_point_slots"] = sorted(owner.ProfileGraph.LoopValue.PointsValue)
    result["line_order"] = owner.ProfileGraph.LoopValue.OrderValue
    return result


def check_legacy(axis, raw, spec, audit):
    plane = {"x": "right", "y": "top", "z": "front"}[axis]
    local = tuple((spec["axis_x_mm"], row) for row in spec["axis_span_mm"])
    result = {}
    for name, options in VIEWS.items():
        before = audit["grammar_reads"]
        doc = open_document(
            raw, source_format="solidworks.sldprt", strict=True, **options
        )
        check_projection(
            doc, plane, spec["support_id"], local, spec["angle_rad"], spec["reverse"]
        )
        result[name] = {
            "document_sha256": digest(ToJson(doc).encode()),
            "layout_reads": audit["grammar_reads"] - before,
        }
        if name == "default":
            assert (
                doc.brep is not None
                and not doc.brep_payloads
                and doc.bodies[0].name == "OrdinaryBossRevolve"
            )
            assert any(
                item.code == "sldprt.brep_reconstructed" for item in doc.diagnostics
            )
            assert result[name]["layout_reads"] == 0
    assert (digest(raw), *(result[key]["document_sha256"] for key in VIEWS)) == LEGACY[
        axis
    ]
    return result


def warm_codecs():
    for encoding in (
        "ascii",
        "latin-1",
        "cp1252",
        "utf-8",
        "utf-8-sig",
        "utf-16-le",
        "utf-16-be",
    ):
        lookup(encoding)
    for name in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.AngleRevValidate",
        "interchange.document.Validation.DistExtValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Validation.PlaneRevValidate",
    ):
        import_module(name)


def worker(request):
    warm_codecs()
    generated = request.get("generated")
    if "axis" not in request:
        raw = pinned(Path(request["path"]), request["wire"]["source_sha256"])
    state, audit = make_guard(ROOT / "src")
    state["enabled"] = True
    if "axis" in request:
        axis = request["axis"]
        raw, spec = make_cold(axis, axis in ("x", "y"))
        assert audit["grammar_reads"] == 0
        result = check_legacy(axis, raw, spec, audit)
    else:
        result = check_end_part(
            raw, request["spec"], request["wire"], request["oracle"], audit, generated
        )
    assert not audit["unexpected_attempts"], audit
    return {"archive_sha256": digest(raw), "guard": audit, "result": result}


def isolated(request):
    result = run(
        (executable, "-I", "-B", str(HERE), "--worker"),
        input=dumps(request),
        text=True,
        capture_output=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        request.get("axis", request.get("path")),
        result.stderr,
    )
    return loads(result.stdout)


def audit_disclosed(discovery_root, generated_dir):
    discovery = receipt("RevolveEndSourceDiscovery01", DISCOVERY)
    recovery = receipt("RevolveEndSourceRecovery01", RECOVERY)
    wire_receipt = receipt("RevolveEndOwners01", WIRE)
    for packet in (discovery, recovery):
        assert packet["control-before"]["passed"] and packet["control-after"]["passed"]
        assert packet["oracle_sha256"] == wire_receipt["oracle_executable_sha256"]
    assert discovery["build"] == wire_receipt["oracle_version"] == "34.5.2.0604"
    authored = loads(
        pinned(discovery_root / "Tool" / "Spec.json", discovery["spec_sha256"])
    )
    assert authored["split"] == "discovery"
    original_cases = {row["name"]: row for row in discovery["sources"]}
    wire_cases = {row["case"]: row for row in wire_receipt["cases"]}
    specs = {row["name"]: row for row in authored["cases"]}
    assert (
        tuple(specs) == CASES
        and original_cases.keys() == specs.keys() == wire_cases.keys()
    )
    assert (
        recovery["passed"]
        and recovery["sources"][0]["native_sha256"]
        == wire_cases["EndMidplane"]["source_sha256"]
    )
    built = loads(pinned(generated_dir / "BuildReceipt.json", GENERATED))
    assert (
        built["source_tree"] == GENERATED_TREE
        and built["spec_sha256"] == discovery["spec_sha256"]
    )
    assert built["cases"].keys() == specs.keys()
    requests = []
    for name in CASES:
        record, wire, spec = original_cases[name], wire_cases[name], specs[name]
        assert record["native_sha256"] == wire["source_sha256"]
        author = next(phase for phase in record["phases"] if phase["phase"] == "author")
        assert author["passed"] and author["checks"] == author["checks_passed"]
        native = author["observations"]["authored"]
        requests.append(
            (
                name,
                {
                    "path": str(discovery_root / "Capture" / name / f"{name}.SLDPRT"),
                    "wire": wire,
                    "spec": spec,
                    "oracle": native,
                },
            )
        )
        generated = built["cases"][name]
        candidate = generated["ends"] | {
            "angle_owners": generated["ends"]["angles"],
            "source_sha256": generated["archive_sha256"],
        }
        requests.append(
            (
                f"Cold{name}",
                {
                    "path": str(generated_dir / f"{name}.SLDPRT"),
                    "wire": candidate,
                    "spec": spec,
                    "oracle": native,
                    "generated": generated,
                },
            )
        )
    requests += [(f"LegacyCold{axis.upper()}", {"axis": axis}) for axis in LEGACY]
    outputs = {name: isolated(request) for name, request in requests}
    return {
        "schema": "kit.sw2026.ordinary-revolve-end-reader.v1",
        "base_revision": BASE,
        "portable_contract_revision": PORTABLE,
        "oracle_version": discovery["build"],
        "oracle_sha256": discovery["oracle_sha256"],
        "prior_evidence_sha256": {
            "discovery": DISCOVERY,
            "recovery": RECOVERY,
            "typed_wire": WIRE,
            "disclosed_spec": discovery["spec_sha256"],
            "generated": GENERATED,
        },
        "generated_source_revision": built["source_revision"],
        "generated_source_tree": built["source_tree"],
        "tool_sha256": {
            str(tool.relative_to(ROOT)): digest(tool.read_bytes())
            for tool in (
                HERE,
                HERE.parent / "RevolveSectorMath.py",
                HERE.parent.parent / "PrincipalReader/AuditPrincipalReader.py",
                HERE.parent.parent / "PrincipalReader/MakePrincipalCold.py",
            )
        },
        "reader_source_sha256": {
            name: digest((ROOT / name).read_bytes()) for name in READER_PATHS
        },
        "fresh_workers": len(outputs),
        "heldout_sources_read": 0,
        "new_native_processes": 0,
        "writer_acceptance": False,
        "cases": outputs,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--discovery-root", type=Path)
    parser.add_argument("--generated-dir", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        result = worker(loads(stdin.read()))
    else:
        assert (
            args.discovery_root is not None
        ), "supply the checksum-bound disclosed discovery directory"
        assert (
            args.generated_dir is not None
        ), "supply the checksum-bound generated asset directory"
        result = audit_disclosed(args.discovery_root, args.generated_dir)
    print(dumps(result, indent=2, allow_nan=False, sort_keys=True))


if __name__ == "__main__":
    main()
