from argparse import ArgumentParser
from base64 import b64decode, b64encode
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from importlib import import_module
from io import BytesIO
from math import radians
from pathlib import Path, PureWindowsPath
from struct import unpack
from subprocess import check_output, run
import json
import sys

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(HERE), str(HERE.parent / "PrincipalWriter")]

from AuditRevEndOwners import digest, guard_runtime, observe_ends
from BuildPrincipalRevolves import authored_neutral
from RevolveStreamAudit02 import stream_audit
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseXml
from convert.adapters.solidworks.Core.Preparation.Revolve.PlanPublicRevolve import PlanPublicRevolve
from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


MODES = {"single": "one_sided", "midplane": "symmetric_full", "two": "two_sided"}


def source_model(case, destination, epoch):
    def millimetres(values):
        return [value * 1000.0 for value in values]

    spec = {"name": case["name"], "radial_mm": millimetres(case["radius_m"]), "axial_mm": millimetres(case["axial_m"]),
            "axis_x_mm": case["axis_x_m"] * 1000.0, "axis_span_mm": millimetres(case["axis_axial_m"]),
            "angle_deg": case["angle_deg"], "edit_angle_deg": case["edit_angle_deg"], "reverse": case["reverse"],
            "created_at": epoch, "self_path": destination}
    document = authored_neutral(spec, case["plane"], None)
    feature = document.feature_timeline[0]
    params = document.parameters
    against = None
    if case["mode"] == "two":
        against = "parameter/against"
        params += (replace(params[0], id=against, name="D2",
                           value=replace(params[0].value, value=radians(case["second_deg"]))),)
    definition = replace(feature.definition, SideMode=MODES[case["mode"]], AgainstParameterId=against)
    step = replace(feature, definition=definition, parameter_ids=tuple(param.id for param in params))
    return replace(document, parameters=params, feature_timeline=(step,))


def inspect_generated(raw, case):
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    feature, = (node for node in link.ResolvedValue.RootsValue if node.ClassValue.NameValue == "moRevolution_c")
    ends = observe_ends(link, feature)
    expected = {"single": (1, 0, 0), "midplane": (0, 6, 0), "two": (0, 0, 0)}[case["mode"]]
    assert tuple(ends["end_words"][key] for key in ("f08", "f0c", "f10")) == expected
    assert ends["feature_words"]["f820"] == 0 and ends["feature_words"]["f824"] == int(case["reverse"])
    angles = [("D1", radians(case["angle_deg"]))]
    if case["mode"] == "two":
        angles.append(("D2", radians(case["second_deg"])))
    observed = []
    end_fields = feature.FieldsValue["f8d8"].FieldsValue
    for slot, row in ends["angles"].items():
        if row is None:
            assert end_fields[slot] is None
            continue
        display = end_fields[slot].FieldsValue
        cached, = unpack("<d", display["f5b0"]["data"])
        assert cached == row["radians"] and display["f1018"] == (0x18 if slot == "f18" else 0x1C)
        observed.append((row["name"], row["radians"]))
    assert angles == observed
    root = ParseXml(archive.require(KeywordsStream))
    keyword, = (element for element in root if element.attrib.get("Type") == "Revolve")
    order = [key.attrib["Name"] for key in keyword if key.tag == "Dimension"]
    expected_order = [name for name, _ in angles]
    if len(expected_order) == 2 and not case["reverse"]:
        expected_order.reverse()
    assert order == expected_order
    linked, history = stream_audit(archive, link)
    assert len(linked) == 8 and len(history) == 2
    assert all(row["qualified"] for row in history.values())
    return {"ends": ends, "keyword_dimension_order": order, "streams": linked | history}


def worker(request):
    for module in (
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.AngleRevValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Validation.PlaneRevValidate",
        "interchange.document.Validation.DistExtValidate",
    ):
        import_module(module)
    case, destination, epoch = (request[key] for key in ("case", "destination", "epoch"))
    blocked = guard_runtime()
    document = source_model(case, destination, epoch)
    path = PrepareRevolve(document, destination, epoch)
    output = BytesIO()
    named = PrepareRevolve(document, output, epoch, WriteOptions(values={"final_destination": destination}))
    assert path.BytesValue == named.BytesValue and not output.getvalue()
    if case["mode"] == "single":
        assert PlanPublicRevolve(document) is not None
    else:
        try:
            PlanPublicRevolve(document)
        except ValueError as error:
            assert str(error) == "public native revolve end mode requires native acceptance"
        else:
            raise ValueError("unqualified public end mode was admitted")
    result = inspect_generated(path.BytesValue, case)
    assert not blocked
    result.update(archive_sha256=digest(path.BytesValue), path_and_stream_equal=True, runtime_external_access_attempts=0,
                  output=b64encode(path.BytesValue).decode("ascii"))
    return result


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def build_one(request):
    child = run((sys.executable, "-I", "-B", __file__, "--worker"), input=encode(request), capture_output=True, timeout=120)
    if child.returncode or child.stderr:
        raise ValueError(request["case"]["name"] + ": " + child.stderr.decode())
    result = json.loads(child.stdout)
    raw = b64decode(result.pop("output"), validate=True)
    assert digest(raw) == result["archive_sha256"] and result["runtime_external_access_attempts"] == 0
    return raw, result


def main(spec_path, output, guest, epoch):
    assert output.is_absolute() and not output.is_relative_to(ROOT) and guest.is_absolute()
    raw_spec = spec_path.read_bytes()
    spec = json.loads(raw_spec)
    assert spec["split"] == "discovery"
    cases = spec["cases"]
    requests = [{"case": case, "destination": str(guest / (case["name"] + ".SLDPRT")), "epoch": epoch} for case in cases]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(build_one, requests))
    output.mkdir(parents=True)
    for case, (raw, _) in zip(cases, results, strict=True):
        (output / (case["name"] + ".SLDPRT")).write_bytes(raw)
    info = {"schema": "kit.sw2026.ordinary-end-generated-discovery.v1", "spec_sha256": digest(raw_spec),
            "source_revision": check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip(),
            "source_tree": check_output(("git", "rev-parse", "HEAD:src"), cwd=ROOT, text=True).strip(),
            "tool_sha256": digest(Path(__file__).read_bytes()),
            "cases": {case["name"]: proof for case, (_, proof) in zip(cases, results, strict=True)}}
    (output / "BuildReceipt.json").write_bytes(encode(info))
    print(json.dumps({"built": len(cases), "runtime_external_access_attempts": 0}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--guest", type=PureWindowsPath)
    parser.add_argument("--epoch", type=int, default=1760000000)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(encode(worker(json.load(sys.stdin))))
    else:
        assert args.spec and args.output and args.guest
        main(args.spec, args.output, args.guest, args.epoch)
