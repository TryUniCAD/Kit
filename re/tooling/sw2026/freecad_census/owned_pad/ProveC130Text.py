from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from io import BytesIO
from json import loads
from pathlib import Path
from subprocess import run
from xml.etree import ElementTree
from zipfile import ZipFile
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TOOLS = HERE.parents[2]
sys.path[:0] = [str(ROOT / "src"), str(TOOLS), str(TOOLS / "equations"),
                str(HERE.parent), str(HERE.parents[1]),
                str(HERE.parents[1] / "ancestry"), str(TOOLS / "attached_top_box_source")]

from ProveBlindDormant import CASE, CUSTODY, EPOCH, digest, pinned, wire
from ProveC130Axes import COMBINED_ARCHIVE, checked_axes, derived_axes, target_axes, verify_public_read
from ProvePadAncestry import SOURCES
from C130SourceOwners import source_owners

BASE = "4f7ce7b398c7e2493f8fa4351190e30e41a7bc45"
MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
PRIOR_AXES = "8098b0872d6b0823020c329fa419d8729eff2668f190f7e86bc5f38be727159a"
PRESENTED_ARCHIVE = "274e756af72fe345f5b338a59c56e6a7a77b4f6eceac14d49cb80253ec9221a3"
CODE_ROOT = ROOT / "src/convert/adapters/solidworks"
CODE_PATHS = (
    "Core/Preparation/FreecadBox/Source/MakeFcDocText.py",
    "Core/Preparation/FreecadBox/Source/ReadBoxText.py",
    "Core/Preparation/FreecadPad/CheckPadOwners.py",
    "Core/Preparation/FreecadPad/ReadPadDoc.py",
    "Core/Preparation/FreecadPad/ReadPadText.py",
    "Core/Properties/WithPartProps.py",
    "Core/Reading/ReadAdapter.py",
)


def independent_text(raw, release):
    with ZipFile(BytesIO(raw)) as archive:
        xml = ElementTree.fromstring(archive.read("Document.xml"))
        screen_owner = "GuiDocument.xml" in archive.namelist()
    rows = {row.attrib["name"]: row[0].attrib["value"]
            for row in xml.findall("./Properties/Property")
            if len(row) == 1 and row[0].tag == "String"
            and row.attrib["type"] == "App::PropertyString"}
    summary = {"title": rows["Label"], "comments": rows["Comment"]}
    if rows["CreatedBy"]:
        summary["author"] = rows["CreatedBy"]
    literal = {"FreeCAD " + key: rows[key] for key in (
        "Company", "CreationDate", "Id", "LastModifiedBy",
        "LastModifiedDate", "License", "LicenseURL",
    ) if rows[key]}
    assert release == xml.attrib["ProgramVersion"]
    literal.update({
        "FreeCAD Uid": xml.find("./Properties/Property[@name='Uid']/Uuid").attrib["value"],
        "FreeCAD Source Version": release,
        "FreeCAD Source Schema": xml.attrib["SchemaVersion"],
        "FreeCAD Show Hidden": xml.find("./Properties/Property[@name='ShowHidden']/Bool").attrib["value"],
    })
    assert not screen_owner
    return summary, literal


def text_fingerprint(values):
    return {key: {"utf8_bytes": len(value.encode("utf-8")),
                  "sha256": digest(value.encode("utf-8"))}
            for key, value in values.items()}


def project_streams(presentation, summary, custom):
    from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePartProps import MakePartProps
    from convert.adapters.solidworks.Core.Properties.ReadCoreProps import ReadCoreProps
    from convert.adapters.solidworks.Core.Properties.ReadCustomProps import ReadCustomProps

    streams = MakePartProps(presentation)
    assert set(streams) == {"docProps/core.xml", "docProps/custom.xml"}
    assert ReadCoreProps(streams["docProps/core.xml"]) == summary
    assert ReadCustomProps(streams["docProps/custom.xml"], False) == custom
    return {key: {"sha256": digest(payload), "bytes": len(payload)}
            for key, payload in streams.items()}


def compose(document, source, axes, presentation):
    from convert.adapters.solidworks.Archive.Construction.BodyNames.ReadBodyKeys import ReadBodyKeys
    from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.CheckAxisInput import CheckAxisInput
    from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.FinishAxesPart import FinishAxesPart
    from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
    from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeAnchorPart import MakeAnchorPart
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.BoxAnchorInput import BoxAnchorInput
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

    plan = source.corner.recipe
    input_value = replace(MakePartRecipe(plan, EPOCH), PropertiesValue=presentation)
    anchor = BoxAnchorInput(plan, TopAttached=False)
    anchor = replace(anchor, DimensionsValue=replace(
        anchor.DimensionsValue, DesignIntent=input_value.DesignIntent,
        SelectedLeader=input_value.SelectedLeader))
    CheckAxisInput(axes, input_value)
    allocator = PersistentIds()
    stock = MakeAnchorPart(input_value, plan, anchor, WidthDepth=True,
                           AllocatorValue=allocator, DormantDepth=source.dormant_m,
                           BodyName=source.body_name)
    owner_parameters = {row.id: row for row in document.parameters}
    driver_document = replace(document, parameters=tuple(
        owner_parameters[key] for key in source.corner.source_parameter_ids))
    dimensions = ReadBodyKeys(driver_document, plan, input_value)
    return FinishAxesPart(stock, input_value, allocator, axes, dimensions, PartRelations=True)


def with_wrong_title(document):
    metadata = deepcopy(document.metadata["freecad"])
    (record,) = (row for row in metadata["document_properties"]["children"]
                 if row["attributes"]["name"] == "Label")
    record["children"][0]["attributes"]["value"] += " forged"
    return replace(document, metadata={**document.metadata, "freecad": metadata})


def refuse_source(document):
    from CheckScopedPlainWriter import reject
    from convert.adapters.solidworks.Core.Preparation.FreecadPad.ReadPadText import ReadPadText

    return {
        "conflicting_document_title": reject(
            lambda: ReadPadText(with_wrong_title(document)), ValueError,
            "disagrees with its actual saved owner"),
        "missing_binding": reject(
            lambda: ReadPadText(replace(document, brep_payloads=tuple(
                row for row in document.brep_payloads if row.id != "freecad:native-document-binding"))),
            ValueError, "requires the intact document binding"),
        "conflicting_body_authority": reject(
            lambda: ReadPadText(replace(document, bodies=(replace(
                document.bodies[0], final_feature_id=document.sketches[0].id),))),
            ValueError, "lost its actual creating feature"),
    }


def target_text(raw, summary, custom):
    from convert import open_document

    observed = {}
    modes = (("design_only", False), ("full", True))
    for key, full in modes:
        document = open_document(raw, source_format="solidworks.sldprt",
                                 strict=True, include_brep=full)
        assert document.metadata["document_summary"] == summary
        assert document.metadata["custom_properties"] == custom
        assert document.metadata["solidworks.part_text_properties"]["status"] == "complete"
        snapshot = type(document).from_json(document.to_json(indent=None))
        assert snapshot.metadata["document_summary"] == summary
        assert snapshot.metadata["custom_properties"] == custom
        assert snapshot.parameters == document.parameters
        assert snapshot.feature_timeline == document.feature_timeline
        observed[key] = digest(document.to_json(indent=None).encode("utf-8"))
    return observed


def malformed_text(streams):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import BuildSldprt

    invalid = {**streams, "docProps/custom.xml": b"<unclosed"}
    blob = BuildSldprt(invalid, FormatVersion=4)
    value = open_document(blob, source_format="solidworks.sldprt", strict=True)
    assert value.brep is not None and value.bodies[0].topology.volume == 16000.0
    assert "document_summary" not in value.metadata and "custom_properties" not in value.metadata
    assert value.metadata["solidworks.part_text_properties"]["status"] == "unsupported"
    (cause,) = (row for row in value.diagnostics
                if row.code == "solidworks.part_text_properties_unavailable")
    assert len(value.parameters) == 4 and len(value.feature_timeline) == 22
    return {"diagnostic": cause.code, "geometry_and_four_drivers_retained": True}


def full_candidate(document, presentation, emit):
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Properties.ReadPartText import ReadPartText
    from ProveNamedWidthDepth import audit_publication, fingerprint

    source = source_owners(document, CASE)
    _, axes = checked_axes(document)
    baseline = derived_axes(document, source, axes)
    assert digest(baseline.BytesValue) == COMBINED_ARCHIVE
    candidate = compose(document, source, axes, presentation)
    assert digest(candidate.BytesValue) == PRESENTED_ARCHIVE
    added = tuple(sorted(candidate.StreamsValue.keys() - baseline.StreamsValue.keys()))
    assert added == ("docProps/core.xml", "docProps/custom.xml")
    changed = [key for key, data in baseline.StreamsValue.items()
               if candidate.StreamsValue[key] != data]
    assert changed == [], changed
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    _, associations = target_axes(archive, source.corner.recipe)
    projection, readback = verify_public_read(candidate.BytesValue, associations, source)
    try:
        ReadPartText(readback, archive)
    except ValueError as error:
        unlinked_reason = str(error)
    else:
        raise AssertionError("ordinary config attempted without its actual relation context")
    target_documents = target_text(candidate.BytesValue, presentation.SummaryFields,
                                   presentation.DocumentFields)
    return {
        "baseline": COMBINED_ARCHIVE,
        "archive": fingerprint(archive, candidate.BytesValue),
        "old_streams_exact": len(baseline.StreamsValue),
        "added_text_streams": added,
        "target_document_sha256": target_documents,
        "unlinked_property_refusal": unlinked_reason,
        "axis_picks": projection["full"]["ordered_plane_selections"],
        "geometry": projection["full"]["geometry"],
        "bad_text": malformed_text(candidate.StreamsValue),
        "intact_source_refusals": audit_publication(document),
        **({"scratch_candidate_b64": b64encode(candidate.BytesValue).decode("ascii")}
           if emit else {}),
    }


def worker(request):
    from convert import open_document
    from CheckScopedPlainWriter import WriterAudit
    from ProveFcstdCorner import prewarm
    from VerifyLocalSketchExpr import guard_source
    from convert.adapters.solidworks.Core.Preparation.FreecadPad.ReadPadText import ReadPadText

    case = request["case"]
    path = Path(request["path"]).resolve(strict=True)
    compact = "".join(character for character in str(path).casefold() if character.isalnum())
    assert path.suffix.casefold() == ".fcstd"
    assert not any(mark in compact for mark in ("holdout", "heldout", "sealed"))
    raw = pinned(path, SOURCES[case])
    source_reads, denied = guard_source(path, ROOT / "src")
    document = open_document(path, source_format="freecad.fcstd", strict=True,
                             include_brep=True, include_tessellation=True)
    consumed = len(source_reads)
    assert document.source.sha256 == SOURCES[case] and consumed and not denied
    expected_summary, expected_custom = independent_text(raw, document.source.application_version)
    intake = document.to_json(indent=None)
    prewarm()
    lookup("utf-8-sig")
    audit = WriterAudit(ROOT / "src", Path("unused.SLDPRT"))
    sys.addaudithook(audit.observe)
    audit.phase = "prepare"
    try:
        presentation = ReadPadText(document)
        assert presentation.SummaryFields == expected_summary
        assert presentation.DocumentFields == expected_custom
        assert presentation.ConfigurationFields == {}
        assert ReadPadText(type(document).from_json(intake)) == presentation
        streams = project_streams(presentation, expected_summary, expected_custom)
        rejected = refuse_source(document)
        outcome = full_candidate(document, presentation, request["emit"]) if case == CASE else None
        if outcome is not None:
            assert all(outcome["archive"]["streams"][key] == value for key, value in streams.items())
        assert document.to_json(indent=None) == intake
    finally:
        audit.phase = "done"
    assert consumed == len(source_reads) and not denied and not audit.denied and not audit.target_opens
    assert pinned(path, SOURCES[case]) == raw
    flags = {row.attributes["freecad_path"]: row.value.value for row in document.parameters
             if row.attributes.get("freecad_path") in ("Refine", "AllowMultiFace")}
    return {
        "source_sha256": SOURCES[case],
        "summary": text_fingerprint(expected_summary),
        "custom": text_fingerprint(expected_custom),
        "typed_text_streams": streams,
        "source_only_policies": flags,
        "refusals": rejected,
        "matches_exact_saved_text": True,
        "intact_neutral_json_reprojection": True,
        "runtime_input_file_reads": 0,
        "generated": outcome,
    }


def main(inventory, candidate):
    assert inventory is not None
    if candidate is not None:
        assert not candidate.resolve().is_relative_to(ROOT)
        assert candidate.suffix.casefold() == ".sldprt" and not candidate.exists()
    rows = loads(pinned(inventory, CUSTODY))["files"]
    previous = loads(pinned(MEASUREMENTS / "SdkC130EquationAxes01.json", PRIOR_AXES))
    assert previous["case"]["combined_archive"]["sha256"] == COMBINED_ARCHIVE
    outcomes = {}
    for key, source_hash in SOURCES.items():
        (row,) = (entry for entry in rows if entry["case_id"] == key)
        assert row["sha256"] == source_hash
        inputs = wire({"case": key, "path": row["source_path"], "emit": candidate is not None})
        children = tuple(run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                             input=inputs, capture_output=True, timeout=120) for _ in range(2))
        for child in children:
            if child.returncode or child.stderr:
                sys.stderr.buffer.write(child.stderr)
                raise ValueError("guarded C130 presentation process failed")
        assert children[0].stdout == children[1].stdout
        outcomes[key] = loads(children[0].stdout)
    assert outcomes[CASE]["summary"]["comments"] != outcomes["C123-P01"]["summary"]["comments"]
    assert len({report["summary"]["comments"]["sha256"] for report in outcomes.values()}) == len(SOURCES)
    if candidate is not None:
        payload = b64decode(outcomes[CASE]["generated"].pop("scratch_candidate_b64"), validate=True)
        assert digest(payload) == PRESENTED_ARCHIVE
        with candidate.open("xb") as output:
            output.write(payload)
    return {
        "schema": "kit.sw2026.freecad-pad-presentation.v1",
        "base": BASE,
        "source_manifest_sha256": CUSTODY,
        "baseline_axis_receipt_sha256": PRIOR_AXES,
        "changed_code_sha256": {
            str(path.relative_to(ROOT)): digest(path.read_bytes())
            for path in (*(CODE_ROOT / entry for entry in CODE_PATHS), HERE)},
        "cases": outcomes,
        "fresh_workers": 2 * len(outcomes),
        "native_processes": 0,
        "whole_source_qualified": False,
        "corpus_credit": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    sys.stdout.buffer.write(wire(worker(loads(sys.stdin.buffer.read()))
                                 if args.worker else main(args.inventory, args.candidate)))
