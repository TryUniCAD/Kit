from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from math import isclose
from pathlib import Path, PureWindowsPath
from subprocess import run
from zlib import ZLIB_RUNTIME_VERSION
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
from CheckScopedPlainWriter import WriterAudit, reject

FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
NATIVE_PIN = "6538bdc0dfa5d1b82fab03bde1d742f98fabd8c9299c1a18c2e55f5248b429c9"
GENERATION_PIN = "f8b77a00518ea5e8918fbb4dbebc466611c9c38f6e676f09da1f9f3b09a026fb"
GEOMETRY_PIN = "6d803680a917fdaf9295ae9d40acdca758ca7edbfcd087788e00216119b9c774"
FILES = ("EqualNeutral.json", "TwoDistancesNeutral.json")


def demand(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(path, expected):
    data = path.read_bytes()
    demand(digest(data) == expected, "disclosed artifact differs from its custody hash: " + path.name)
    return loads(data)


def build_request(slot):
    reports = ROOT / "re/solidworks/measurements/2026"
    terminal = pinned(reports / "ChamferDistancePairDisclosedNative01.json", NATIVE_PIN)
    generation = pinned(reports / "ChamferDistancePairGenerated01.json", GENERATION_PIN)
    geometry = pinned(reports / "SdkPublicChamferDistanceRead01.json", GEOMETRY_PIN)
    case = generation["candidates"][slot]
    source = ROOT / "re/solidworks/v2026/corpus/chamfer-distance-neutral" / FILES[slot]
    neutral = pinned(source, case["neutral_sha256"])
    (expected,) = tuple(row for row in geometry["results"] if row["archive_sha256"] == case["archive_sha256"])
    envelope = {"written_at": neutral["epoch"], "receipt": {
        "schema": "kit.sw2026.distance-pair-publication.v1",
        "generation": generation, "native_result": terminal, "native_result_sha256": NATIVE_PIN}}
    return {"neutral": neutral, "case": case, "expected": expected, "evidence": envelope}


def edited_intent(document, equal):
    stock, step = document.feature_timeline
    changes = {parameter.id: parameter for parameter in document.parameters}
    driver_id = step.parameter_ids[-1]
    driver = changes[driver_id]
    value = replace(driver.value, value=driver.value.value + 0.75)
    changes[driver_id] = replace(driver, value=value)
    definition = replace(step.definition, **({"distance": value} if equal else {"second_distance": value}))
    return replace(document, parameters=tuple(changes.values()),
                   feature_timeline=(stock, replace(step, definition=definition))), value.value


def verify_read(document, expected):
    from interchange.Features.FeatureKinds import ChamferFeature

    steps = {step.id: step for step in document.feature_timeline}
    stock = steps[expected["stock_id"]]
    finish = steps[expected["feature_id"]]
    demand(isinstance(finish.definition, ChamferFeature)
           and finish.input_feature_ids == (stock.id,) and stock.operation.value == "create"
           and finish.definition.mode == ("equal_distance" if expected["mode_word"] == 18 else "two_distances"),
           "cold read lost the actual stock and distance operation")
    params = {value.id: value for value in document.parameters}
    drivers = tuple(params[key] for key in finish.parameter_ids)
    demand([[p.name, p.value.value, p.attributes["persistent_dimension_id"], p.id] for p in drivers]
           == expected["drivers"] and all(p.owner_id == finish.id and p.value.unit == "mm" for p in drivers)
           and len(finish.selection_ids) == len(document.selections) == 2
           and tuple(value.id for value in document.selections) == finish.selection_ids,
           "cold read lost the live dimension names, values, persistent owners or physical picks")
    body, = document.bodies
    demand(body.final_feature_id == finish.id and body.name == stock.name,
           "cold read changed the one modified stock body")
    topology = body.topology
    counts = [topology.solid_count, topology.shell_count,
              topology.face_count, topology.edge_count, topology.vertex_count]
    demand(counts == expected["topology"], "cold distance topology differs from the measured scope")
    demand(document.brep is not None and document.brep.bodies[0].design_body_id == body.id and not document.brep_payloads,
           "analytic brep did not bind to the actual neutral body")
    centroid = body.attributes["solidworks.body_centroid_mm"]
    centroid = [centroid.x, centroid.y, centroid.z] if hasattr(centroid, "x") else list(centroid)
    observed = [topology.volume, topology.surface_area, *centroid]
    desired = [expected["volume_mm3"], expected["area_mm2"], *expected["centroid_mm"]]
    demand(all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-10) for a, b in zip(observed, desired, strict=True)),
           "cold analytic distance volume, area or center differs")
    return {"topology": counts, "volume_mm3": topology.volume,
            "area_mm2": topology.surface_area, "centroid_mm": centroid,
            "drivers": [p.name for p in drivers]}


def worker(request):
    sys.path.insert(0, str(ROOT / "src"))
    audit = WriterAudit(ROOT / "src", HERE.parent / "ChamferUnused.SLDPRT")
    sys.addaudithook(audit.observe)
    from convert import open_document, write_document
    from convert.adapters.solidworks.Container.Container import BuildSldprt
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.Chamfers.PrepChmfPart import PrepChmfPart
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.document.Models.DocumentModel import CadDocument
    for module in ("interchange.brep.Validation.BrepValidate", "interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1", "cp1252"):
        lookup(codec)
    spec, case, expected = (request[key] for key in ("neutral", "case", "expected"))
    doc = CadDocument.from_json(dumps(spec["document"]))
    writer = SldprtWriter()
    audit.phase = "cold"
    values = {"final_destination": spec["locator"], OPTION: request["evidence"], "require_native_transfers": True}
    prepared = PrepChmfPart(doc, BytesIO(), spec["epoch"], WriteOptions(values={
        "final_destination": spec["locator"]}))
    raw = prepared.BytesValue
    demand({name: digest(data) for name, data in prepared.StreamsValue.items()} == case["streams"],
           "direct regeneration differs from the measured logical streams")
    exact = digest(raw) == case["archive_sha256"]
    accepted_routes = check_public(doc, values, writer, write_document, WriteOptions, raw, case, exact)
    reading = open_document(raw, source_format=FORMAT, strict=True)
    measured = verify_read(reading, expected)
    semantic = open_document(raw, source_format=FORMAT, strict=True, include_brep=False)
    demand(semantic.brep is None and semantic.feature_timeline == reading.feature_timeline
           and semantic.parameters == reading.parameters and semantic.selections == reading.selections,
           "geometry-free strict read changes the actual portable edit semantics")
    readback_routes = check_public(reading, values, writer, write_document, WriteOptions, raw, case, exact)
    assert_edited_readback_refuses(reading, values, writer, write_document, WriteOptions)
    malformed = BuildSldprt(dict(prepared.StreamsValue) | {
        "Contents/Config-0-Partition": b"unknown cache carrier",
    }, FormatVersion=4)
    check_unresolved_read(malformed, open_document)
    detection = check_detected_rows(doc, prepared, spec["epoch"], open_document)
    edited, changed_value = edited_intent(doc, case["mode_word"] == 18)
    variant = PrepChmfPart(edited, BytesIO(), spec["epoch"], WriteOptions(values={
        "final_destination": spec["locator"]}))
    edited_read = open_document(variant.BytesValue, source_format=FORMAT, strict=True)
    changed_step = next(step for step in edited_read.feature_timeline
                        if step.id == expected["feature_id"])
    last_id = changed_step.parameter_ids[-1]
    demand(next(value for value in edited_read.parameters if value.id == last_id).value.value == changed_value
           and edited_read.bodies[0].topology.volume != reading.bodies[0].topology.volume,
           "edited neutral driver did not regenerate its own measured-mode geometry")
    refusals = check_refusals(doc, edited, spec, values, writer, write_document, WriteOptions)
    demand(not audit.denied and not audit.target_opens,
           "writer, linked strict read or refusal attempted runtime external access")
    audit.phase = "done"
    return {"archive_sha256": digest(raw), "expected_native_sha256": case["archive_sha256"],
            "bytes": len(raw), "mode_word": case["mode_word"], "deflate": ZLIB_RUNTIME_VERSION,
            "native_acceptance_routes": accepted_routes, "codec_refused": not exact,
            "readback_native_acceptance_routes": readback_routes,
            "exact_native_transfer_evidence": exact,
            "owned_selection_count": len(reading.selections),
            "altered_readback_refused": True,
            "unsupported_history_read_guarded": True, "discovery_refusals": detection,
            "qualified_logical_streams": len(prepared.StreamsValue),
            "strict_geometry": measured, "semantic_read_matches": True,
            "edited_private_sha256": digest(variant.BytesValue), "edited_private_driver_mm": changed_value,
            "refusals": refusals, "runtime_reads": 0, "native_processes_started": 0}


def check_public(doc, values, writer, write_document, WriteOptions, raw, case, exact):
    registry, direct = BytesIO(), BytesIO()

    def registry_write():
        return write_document(doc, registry, destination_format=FORMAT, allow_carrier=False, values=values)

    def direct_write():
        return writer.write(doc, direct, WriteOptions(values=values))

    if not exact:
        demand("zlib-ng" in ZLIB_RUNTIME_VERSION, "unexplained difference in the measured archive envelope")
        for route in (registry_write, direct_write):
            reject(route, ValueError, "no unique exact native measurement")
        demand(registry.getvalue() == direct.getvalue() == b"", "alternate codec emitted unmeasured output")
        return 0
    from convert.adapters.base.WritePolicy import GetDocumentCaps

    results = (registry_write(), direct_write())
    demand(results[0].transfers == results[1].transfers
           and {value.CapabilityData for value in results[1].transfers} == GetDocumentCaps(doc)
           and all(value.mode.value == "native" for value in results[1].transfers),
           "configured SDK routes disagree on explicit native capability transfer")
    demand(registry.getvalue() == direct.getvalue() == raw
           and all(value.vendor_loadable and value.application_usable and not value.dropped
                   and value.bytes_written == len(raw)
                   and value.metadata[OPTION]["generated_sha256"] == case["archive_sha256"]
                   for value in results), "public publication differs from the exact native measurement")
    return len(results)


def assert_edited_readback_refuses(document, values, writer, write_document, WriteOptions):
    body, = document.bodies
    modified = (
        replace(document, metadata=dict(document.metadata) | {"extra_authored_state": "non-default"}),
        replace(document, bodies=(replace(body, topology=replace(
            body.topology, volume=body.topology.volume + 1.0)),)),
    )
    for source in modified:
        registry, direct = BytesIO(), BytesIO()
        message = "cold readback differs from its regenerated part"
        reject(lambda: write_document(source, registry, destination_format=FORMAT,
                                      allow_carrier=True, values=values), ValueError, message)
        reject(lambda: writer.write(source, direct, WriteOptions(values=values)), ValueError, message)
        demand(registry.getvalue() == direct.getvalue() == b"",
               "unverified source semantics reached either destination")


def check_unresolved_read(payload, open_document):
    reject(lambda: open_document(payload, source_format=FORMAT, include_brep=False),
           ValueError, "chamfer history requires the verified cold stock")
    observed = open_document(payload, source_format=FORMAT, strict=False, include_brep=False)
    demand(observed.brep is None and any(
        value.code == "sldprt.chamfer_history_unresolved" and value.severity.value == "warning"
        for value in observed.diagnostics
    ), "permissive inspection hid an unsupported chamfer history")
    return observed


def check_detected_rows(document, part, epoch, open_document):
    from xml.etree.ElementTree import fromstring
    from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindByPlan
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Container.Format import KeywordsStream
    from convert.adapters.solidworks.Core.Adapter import DecodePartBase
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from interchange.Features.FeatureKinds import NativeFeature

    plan = part.PlanValue
    stock = MakeBlindByPlan(document, MakePartRecipe(plan, epoch), plan)
    keywords = part.StreamsValue[KeywordsStream]
    xml = fromstring(keywords[1:])
    (chamfer,) = (row for row in xml.iter("Feature") if row.get("Type") == "Chamfer")
    identity = int(chamfer.attrib["id"])
    chamfer.set("Type", "Opaque")
    cases = (
        ("class_alias", dict(part.StreamsValue) | {KeywordsStream: FrameKeywords(xml, False)},
         "Opaque", "Chamfer_c"),
        ("keyword_only", dict(stock.StreamsValue) | {KeywordsStream: keywords}, "Chamfer", ""),
    )
    for _, streams, kind, class_name in cases:
        payload = BuildSldprt(streams, FormatVersion=4)
        model = DecodePartBase(SldprtArchive.from_bytes(payload), None)[0]
        (feature,) = (row for row in model.features if row.object_id == identity)
        demand((feature.kind, feature.class_name) == (kind, class_name)
               and (feature.native_offset is not None) == bool(class_name)
               and not any(row.kind == "chamfer" for row in model.operations),
               "contrast did not isolate the intended discovery route")
        result = check_unresolved_read(payload, open_document)
        (step,) = (row for row in result.feature_timeline if row.id == f"sldprt:feature:{identity}")
        demand(isinstance(step.definition, NativeFeature),
               "unresolved chamfer discovery invented a portable definition")
    return [label for label, *_ in cases]


def check_refusals(doc, edited, spec, values, writer, write_document, WriteOptions):
    wrong = ({key: value for key, value in values.items() if key != OPTION},
             "requires an offline native measurement receipt")
    destination = PureWindowsPath(spec["locator"]).name
    wrong_path = values | {"final_destination": str(PureWindowsPath("C:/UnmeasuredOutput") / destination)}
    cases = (
        ("missing_receipt", doc, *wrong),
        ("changed_model", edited, values, "no unique exact native measurement"),
        ("wrong_locator", doc, wrong_path, "no unique exact native measurement"),
    )
    for _, model, options, message in cases:
        target, direct = BytesIO(), BytesIO()
        reject(lambda: write_document(model, target, destination_format=FORMAT, allow_carrier=True, values=options),
               ValueError, message)
        reject(lambda: writer.write(model, direct, WriteOptions(values=options)), ValueError, message)
        demand(target.getvalue() == direct.getvalue() == b"", "a refused chamfer write changed a destination")
    return [label for label, _, _, _ in cases]


def supervise(slot):
    packet = build_request(slot)
    status = run((sys.executable, "-I", "-B", str(HERE), "--worker"), cwd=ROOT,
                 input=dumps(packet, allow_nan=False), text=True, capture_output=True, timeout=90, check=False)
    demand(status.returncode == 0 and not status.stderr, status.stderr)
    return loads(status.stdout)


def main():
    parser = ArgumentParser()
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--worker", action="store_true")
    choices.add_argument("--slot", type=int, choices=(0, 1))
    args = parser.parse_args()
    result = worker(loads(sys.stdin.read())) if args.worker else supervise(args.slot)
    print(dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
