from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from gzip import decompress
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from math import tau
from os import O_RDWR, O_WRONLY
from pathlib import Path
from subprocess import run, TimeoutExpired
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import fromstring, tostring
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from CheckThinSuiteCase import CASES, FIXTURE, FIXTURE_SHA, measure, read, verify_owner
from ProveMeasuredPrincipalRevolve import ROOT, WriterAudit, digest
from ProveMeasuredThinRevolve import emit
from ThinPathLease import MARKER, own_root, prove_lease
from ThinProofModel import neutral

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import (
    ProjectRevolve,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevPart import (
    MakeRevPart,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Container.Parasolid import HasPayload
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Adapter import NativePartModel
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import (
    ReadRevOwners,
)
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Features.ThinRevolve import ThinRevolve
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import (
    ConstraintRef,
    SketchEntity,
    SketchRelation,
)
from interchange.geometry.Models.VectorPlane import PlaneVector


class SavedReadAudit(WriterAudit):
    layout = ROOT / "src/convert/adapters/solidworks/Config/RootLayout.json"

    def __init__(self, output_dir):
        super().__init__(output_dir)
        self.layout_reads = 0

    def observe(self, event, args):
        if (
            self.enabled
            and event == "open"
            and isinstance(args[0], str)
            and Path(args[0]) == self.layout
            and not args[2] & (O_WRONLY | O_RDWR)
        ):
            self.layout_reads += 1
            return
        return super().observe(event, args)


def lease_contrasts(path):
    root = path / "measured-directory"
    code = (
        "from pathlib import Path; import sys,time; "
        "p=Path(sys.argv[1]); p.mkdir(); (p / 'partial.SLDPRT').write_bytes(b'child output'); "
        "print('partial artifact written', flush=True); time.sleep(15)"
    )
    try:
        with own_root(root) as token:
            prove_lease(root, token)
            run(
                [sys.executable, "-I", "-B", "-c", code, str(root / "Candidates")],
                capture_output=True,
                timeout=1.5,
                check=True,
            )
    except TimeoutExpired as error:
        assert error.stdout == b"partial artifact written\n" and not root.exists()
    else:
        raise AssertionError("timeout sentinel completed")
    with own_root(root) as token:
        prove_lease(root, token)
    assert not root.exists()

    root.mkdir()
    control = root / "retained.SLDPRT"
    control.write_bytes(b"existing independent control")
    try:
        with own_root(root):
            raise AssertionError("an existing root was claimed")
    except FileExistsError:
        assert control.read_bytes() == b"existing independent control"
        assert set(root.iterdir()) == {control}

    original = path / "initial-owned-root"
    try:
        with own_root(original) as token:
            original.rename(path / "renamed-root")
            original.mkdir()
            (original / MARKER).write_text(token, encoding="ascii")
            foreign = original / "replacement.SLDPRT"
            foreign.write_bytes(b"independent replacement")
    except ValueError as error:
        assert str(error) == "thin suite will not clean a replaced root"
        assert foreign.read_bytes() == b"independent replacement"
    else:
        raise AssertionError("foreign replacement was cleaned")
    return {
        "timeout_after_output": True,
        "same_root_retry": True,
        "existing_root_preserved": True,
        "replacement_root_preserved": True,
    }


def checked_asset(root, job, name):
    path = root.resolve(strict=True) / "Packet" / name
    assert path.resolve(strict=True) == path and not path.is_symlink()
    raw = path.read_bytes()
    assert digest(raw) == job["files"][name]
    return raw


def warm_thin(audit, raw):
    archive = SldprtArchive.from_bytes(raw)
    config = NativePartModel(archive, None).active_configuration_id
    partitions = [value.name for value in archive.records if HasPayload(value.data)]
    assert partitions == [f"Contents/Config-{config}-Partition"]
    try:
        audit.run(lambda: ReadNativeLink(archive, config))
    except ValueError as error:
        assert (
            str(error)
            == "unsupported SOLIDWORKS body class moLinkedAtomIdNode_c schema 1"
        )
        boundary = str(error)
    else:
        raise AssertionError("saved thin linked boundary changed")
    for full in (True, False):
        try:
            audit.run(lambda: read(raw, full))
        except SldprtFormat as error:
            assert str(error) == "saved thin revolve has unverified editable history"
        else:
            raise AssertionError("cached thin revolve lost its strict refusal")
        fallback = audit.run(lambda: read(raw, full, strict=False))
        assert (fallback.brep is not None) is full and len(fallback.bodies) == 1
        assert all(
            not isinstance(step.definition, ThinRevolve)
            for step in fallback.feature_timeline
        )
    raw_mode = audit.run(
        lambda: SldprtAdapter().read(
            BytesIO(raw),
            ReadOptions(extract_raw_brep=True, include_brep=True, strict=True),
        )
    )
    assert raw_mode.brep_payloads
    return {
        "sha256": digest(raw),
        "bytes": len(raw),
        "typed_warm_decode_boundary": boundary,
        "cache_stream": partitions[0],
        "strict_refusals": 2,
        "partial_permissive_reads": 2,
        "raw_payloads": len(raw_mode.brep_payloads),
    }


def cold_measured(audit, group):
    case, expected, options = measure(group)
    author = neutral(case)
    author.assert_valid()
    GetDocumentCaps(author)
    sink = BytesIO()
    result = audit.run(lambda: emit(author, sink, options, "registry"))
    payload = sink.getvalue()
    assert (
        digest(payload) == expected
        and result.vendor_loadable
        and result.application_usable
    )
    for full in (True, False):
        verify_owner(audit.run(lambda: read(payload, full)), author, case, full)
    return {"sha256": expected, "strict_typed_reads": 2}


def ordinary_document(plane, angle):
    seed = neutral(
        {
            "name": "OrdinaryLegacy" + plane.title(),
            "plane": plane,
            "reverse": False,
            "axis_x_m": 0.003,
            "axis_axial_m": [-0.009, 0.025],
            "axial_m": [-0.002, 0.010],
            "profile_radius_m": 0.014,
            "angle_deg": 90,
            "wall_mode": "one",
            "wall_m": [0.002],
        }
    )
    (sketch,) = seed.sketches
    axis = sketch.entities[1]
    points = ((17.0, -2.0), (21.0, -2.0), (21.0, 10.0), (17.0, 10.0))
    lines = tuple(
        SketchEntity(
            f"profile/{index}",
            GeometryKind.KLine,
            LineGeometry(PlaneVector(*start), PlaneVector(*end)),
        )
        for index, (start, end) in enumerate(
            zip(points, (*points[1:], points[0]), strict=True)
        )
    )
    relations = tuple(
        SketchRelation(
            f"relation/{index}",
            "horizontal" if index % 2 == 0 else "vertical",
            (ConstraintRef(line.id),),
        )
        for index, line in enumerate(lines)
    )
    loop = replace(
        sketch,
        entities=(*lines, axis),
        constraints=relations,
        closed_profile_entity_ids=(tuple(line.id for line in lines),),
    )
    (feature,) = seed.feature_timeline
    driver = seed.parameters[0]
    driver = replace(driver, value=replace(driver.value, value=angle))
    return replace(
        seed,
        sketches=(loop,),
        parameters=(driver,),
        feature_timeline=(
            replace(
                feature,
                name="OrdinaryRevolve",
                definition=feature.definition.SweepValue,
                parameter_ids=(driver.id,),
            ),
        ),
        bodies=(replace(seed.bodies[0], name="OrdinaryRevolve"),),
    )


def omitted_keyword_sketch(data):
    archive = SldprtArchive.from_bytes(data)
    keyword = archive.require(KeywordsStream)
    tree = fromstring(keyword[1:])
    count = 0
    for parent in tree.iter():
        for child in tuple(parent):
            if child.tag == "Sketch":
                count += 1
                parent.remove(child)
    assert count == 1
    return BuildSldprt(
        {**archive.streams, KeywordsStream: keyword[:1] + tostring(tree)},
        FormatVersion=4,
    )


def legacy_contrast(audit, plane, angle):
    document = ordinary_document(plane, angle)
    plan = ProjectRevolve(document)
    settings = MakePartRecipe(plan, 1795406400)
    data = audit.run(lambda: MakeRevPart(document, settings)).BytesValue
    variants = (data, omitted_keyword_sketch(data))
    cases = []
    for index, payload in enumerate(variants):
        archive = SldprtArchive.from_bytes(payload)
        model = NativePartModel(archive, None)
        assert len(model.sketches) == 1 - index and len(model.operations) == 1
        link = ReadNativeLink(archive, 0)
        (owner,) = ReadRevOwners(link)
        assert owner.AngleValue.RadiansValue == angle
        design = audit.run(lambda: read(payload, False))
        assert design.brep is None and len(design.sketches) == 1 - index
        try:
            audit.run(lambda: read(payload, True))
        except SldprtFormat as error:
            assert str(error) == "cache-free revolve has unverified typed history"
            assert "requires a partial Top or Right support" in str(error.__cause__)
        else:
            raise AssertionError(
                "previously unsupported ordinary geometry was checked in"
            )
        cases.append(
            {
                "sha256": digest(payload),
                "legacy_sketches": len(model.sketches),
                "linked_profiles": 1,
                "strict_design_read": True,
                "strict_geometry_refused": True,
            }
        )
    return cases


def main():
    parser = ArgumentParser()
    parser.add_argument("--front", type=Path, required=True)
    parser.add_argument("--principal", type=Path, required=True)
    args = parser.parse_args()
    assert digest(FIXTURE.read_bytes()) == FIXTURE_SHA
    packet = loads(decompress(FIXTURE.read_bytes()))
    import_module("interchange.brep.Validation.BrepValidate")
    for encoding in ("utf-8", "utf-16-le", "ascii"):
        lookup(encoding)
    with TemporaryDirectory(prefix="KitThinReview-") as directory:
        base = Path(directory)
        audit = WriterAudit(base / "guarded-sink")
        leases = lease_contrasts(base)
        saved_audit = SavedReadAudit(base / "guarded-saved-read")
        result = {"cache_free": {}, "saved_thin": {}}
        for group in CASES:
            job = loads(packet[group]["job"])
            root = getattr(args, group)
            result["cache_free"][group] = cold_measured(audit, group)
            raw = checked_asset(root, job, f"Sources/{CASES[group]}.SLDPRT")
            result["saved_thin"][group] = warm_thin(saved_audit, raw)
        control = checked_asset(
            args.front, loads(packet["front"]["job"]), "Control.SLDPRT"
        )
        for full in (True, False):
            native = saved_audit.run(lambda: read(control, full))
            assert len(native.bodies) == 1 and (native.brep is not None) is full
        result["cached_ordinary_control"] = {
            "sha256": digest(control),
            "strict_reads": 2,
        }
        result["ordinary_legacy"] = {
            "front_partial": legacy_contrast(audit, "front", tau / 4),
            "top_full_turn": legacy_contrast(audit, "top", tau),
        }
        result["lease"] = leases
        result["guarded_runtime"] = audit.report()
        result["saved_read_runtime"] = saved_audit.report() | {
            "installed_grammar_reads": saved_audit.layout_reads
        }
    print(dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
