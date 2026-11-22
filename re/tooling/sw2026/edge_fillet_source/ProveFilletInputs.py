from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from json import dumps, loads
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT), str(HERE.parent)]

from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfEdgeRoles import ChmfFinLinks, ChmfLoopOwners, IsChmfEnds
from convert.adapters.solidworks.Archive.Construction.Chamfers.ChmfStockGeom import MakeChmfStock
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindByPlan
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import ReadBodyFaces
from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.PickWarmEdge import ReadWarmPick, ReadWarmPoint
from convert.adapters.solidworks.Core.TypedResolved.Fillets.ReadFilletHist import ReadFilletHist
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.JoinFilletEdge import JoinFilletEdge
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletFace import ReadFilletFace
from convert.adapters.solidworks.Core.TypedResolved.Fillets.Saved.ReadFilletReps import ReadFilletReps
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.VectorPlane import PlaneVector

from FilletModel import predict, validate_cases
from FilletPacket import job_bytes
from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc

BASE = "a6409718da5686c72695342535270dd8b210c736"
MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
SOURCE_PINS = {
    "EdgeFilletArchiveRead01.json": "e7573a71c5fb709a26ae512a332f3fe6eecca5fef949b8f98380ac7cbd1337f3",
    "EdgeFilletColdDiagnosticStage01.json": "28f9e42a15247ece8789d74c5cfc295160a21b27c716ca58682b7bf4df72ce91",
    "EdgeFilletColdDiagnosticResult01.json": "c9f32bfd24f3dbf721111f4b8097ddcad0c6f18e0c0b00c13b45fb54166aa160",
    "ChamferDistancePairSelectors01.json": "a1bdd5b12a650a36b17896cb78d287a701e2df3930c85ab038716feec26311b6",
}
INTENT_PIN = "d985611e397e943860b8b0ce4b3f9631e6c31f5355bdd784519a2b028a9a51cb"
CASE_NAMES = ("EdgeFilletAxial", "EdgeFilletTransverse")
EPOCH = 1795510277


def demand(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def pinned(path, pin):
    data = path.read_bytes()
    demand(digest(data) == pin, f"disclosed file or evidence changed: {path.name}")
    return data


def guard():
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be"):
        lookup(codec)
    for name in (
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(name)
    attempts = []

    def deny(event, _):
        if event in ("open", "os.scandir", "os.listdir", "os.system", "os.exec", "os.posix_spawn") or event.startswith(("socket.", "subprocess.", "ctypes.")):
            attempts.append(event)
            raise ValueError(f"construction boundary allowed external access: {event}")

    sys.addaudithook(deny)
    return attempts


def stamped(wrapper):
    reference = wrapper.FieldsValue["fe8"]
    return {"atom_words": [wrapper.FieldsValue[key] for key in ("f18", "f1c")],
            "ref_words": [reference.FieldsValue[key] for key in ("f70", "fe8")],
            "ref_class": reference.ClassValue.NameValue}


def saved(data, witness, option_pin):
    demand(digest(data) == witness["source_sha256"], "source bytes changed in transport")
    archive = SldprtArchive.from_bytes(data)
    history = ReadFilletHist(archive)
    header = ReadHeaderGraph(archive.require("Header2"), 19000)
    selected = JoinFilletEdge(history, header)
    stock_id = history.OwnersValue.StockValue.FieldsValue["f08"]
    stamp = history.OwnersValue.AtomValue.FieldsValue["f180"]
    epoch = DatumTime(header, stock_id)
    prior, active = (history.StagesValue[index].NodesValue for index in (1, 0))
    fins, face_slots = ReadWarmPick(prior, selected.NativeIndex)
    typed = ReadFilletReps(history, selected.RefValue, header)
    physical = tuple(ReadFilletFace(prior, slot, stock_id, epoch) for slot in face_slots)
    archived = witness["owners"]["edge_owners"]
    expected = tuple((row["owner"]["class"], row["f38"], row["f3c"])
                     for row in archived["f848_selected_edge"]["surfaces"])
    demand(typed == physical == expected, "archived selection differs from the physical positive fin")

    fillet = history.OwnersValue.FilletValue.FieldsValue
    (result,) = NativeRows(fillet["f9b8"])
    (echo,) = NativeRows(fillet["fbf0"])
    (input_row,) = NativeRows(fillet["f848"].FieldsValue["items"])
    wrappers = {"f848_selected_edge": input_row["o"], "f9b8_result_face": result["k"],
                "f9b8_detached_edge": result["v"], "fbf0_detached_edge": echo["edge"]}
    checks = {key: stamped(value) for key, value in wrappers.items()}
    demand(len({value.FieldsValue["fe8"] for value in wrappers.values()}) == 4,
           "live, resultant and detached refs do not own different identities")
    for key, fields in checks.items():
        demand(fields["ref_words"] == archived[key]["reference_words_f70_fe8"]
               and fields["atom_words"] == archived[key]["wrapper_words_f18_f1c"],
               "typed reference words differ from independently checked source")
    for key in ("f9b8_detached_edge", "fbf0_detached_edge"):
        demand(checks[key]["ref_words"] == [0, 0x200], "detached edge does not carry the observed zero cache")

    (result_face,) = tuple(
        active[slot] for slot in ReadBodyFaces(active, active[history.BodyIndex], 7)
        if active[active[slot].Integer("surface")].KindValue == 51
    )
    option = fillet["fc20"]
    demand(option["n"] == len(option["items"]) == 6 and digest(job_bytes(option["items"])) == option_pin,
           "the six saved option words differ from the prior exact archive digest")
    return {
        "case": witness["case"], "edited": witness["edited"], "source_sha256": digest(data),
        "roles": typed, "positive_fin_endpoints_m": [ReadWarmPoint(prior, fin.Integer("vertex")) for fin in fins[::-1]],
        "prior_edge_node_id": prior[selected.NativeIndex].Integer("node_id"),
        "prior_edge_slot": selected.NativeIndex, "positive_face_slots": face_slots,
        "result_face_node_id": result_face.Integer("node_id"), "result_face_slot": result_face.IndexValue,
        "body_stamp": stamp, "reference_owners": checks, "saved_options_count": option["n"],
    }


def model_stock(case):
    plain = MakePlainDoc(case["name"], *case["size_mm"])
    (sketch,) = plain.sketches
    cx, cy = case["center_mm"]

    def translate(point):
        return PlaneVector(point.x + cx, point.y + cy)

    entities = tuple(replace(entity, geometry=LineGeometry(translate(entity.geometry.start), translate(entity.geometry.end)))
                     for entity in sketch.entities)
    request = replace(plain, sketches=(replace(sketch, entities=entities),),
                      configurations=(replace(plain.configurations[0], name="Default"),))
    plan = ProjectPlain(request)
    owner = MakeBlindByPlan(request, MakePartRecipe(plan, EPOCH), plan)
    stock = MakeChmfStock(owner)
    body = stock.SolidValue
    coords = {value.id: tuple(axis / 1000.0 for axis in (value.point.x, value.point.y, value.point.z))
              for value in body.vertices}
    expected = tuple(tuple(value) for value in predict(case)["source_edge"])
    (edge,) = tuple(value for value in body.edges
                    if IsChmfEnds((coords[value.start_vertex_id], coords[value.end_vertex_id]), expected))
    uses, reciprocal = ChmfFinLinks(body)
    owners, _ = ChmfLoopOwners(body)
    (positive,) = tuple(fin for fin in uses[edge.id] if not fin.reversed)
    first_face, loop = owners[positive.id]
    index = loop.index(positive.id)
    face_ids = (first_face, *(owners[reciprocal[key]][0] for key in
                              (positive.id, loop[index - 1], loop[(index + 1) % len(loop)])))
    role_values = [stock.FaceRoles[key] for key in face_ids]
    roles = [("moEndFaceSurfIdRep_c", role.NumberValue, 0) if role.IsCap
             else ("moFromSktEntSurfIdRep_c", role.NumberValue, None) for role in role_values]
    return {"case": case["name"], "roles": roles,
            "positive_fin_endpoints_m": [coords[edge.start_vertex_id], coords[edge.end_vertex_id]],
            "generated_stock_sha256": digest(owner.BytesValue), "logical_streams": len(owner.StreamsValue)}


def worker():
    packet = loads(sys.stdin.buffer.read())
    audits = guard()
    if "modeled" in packet:
        result = model_stock(packet["modeled"])
    else:
        result = saved(bytes.fromhex(packet["source"]), packet["witness"], packet["option_pin"])
    demand(not audits, "boundary performed external accesses")
    print(dumps(result | {"guarded_external_accesses": len(audits)}, sort_keys=True))


def call_worker(packet):
    output = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=dumps(packet).encode(),
                 capture_output=True, check=False, timeout=60, cwd=ROOT)
    demand(output.returncode == 0 and not output.stderr, output.stderr.decode())
    return loads(output.stdout)


def supervise(args):
    evidence = {name: loads(pinned(MEASUREMENTS / name, pin)) for name, pin in SOURCE_PINS.items()}
    original = evidence["EdgeFilletArchiveRead01.json"]
    omit = evidence["EdgeFilletColdDiagnosticResult01.json"]
    option = evidence["EdgeFilletColdDiagnosticStage01.json"]["typed_fc20"]["identical_item_array_sha256"]
    chamfer_words = evidence["ChamferDistancePairSelectors01.json"]["cases"][0]["edge_flip_flags"]["items"]
    chamfer = digest(job_bytes(chamfer_words))
    demand(original["passed"] and len(original["results"]) == 4 and omit["comparison_valid"]
           and omit["outcome"] == "clean_cold_rebuild_and_edit_with_partition_omitted"
           and omit["phases"]["ControlBefore"]["passed"] and omit["phases"]["ControlAfter"]["passed"]
           and not omit["writer_output_count"] and chamfer != option, "expected disclosed comparison evidence differs")
    intents = loads(pinned(HERE.with_name("DisclosedFilletInputs.json"), INTENT_PIN))
    demand(intents["cohort"] == "disclosed", "this tool consumes the disclosed geometry only")
    cases = validate_cases(intents)
    demand(tuple(case["name"] for case in cases) == CASE_NAMES, "unexpected disclosed case names")
    observed = []
    for witness in original["results"]:
        name = witness["case"]
        demand(name in CASE_NAMES, "archive reports an unrecognized source name")
        stem = name + ("Edited" if witness["edited"] else "")
        data = pinned(args.capture / name / f"{stem}.SLDPRT", witness["source_sha256"])
        observed.append(call_worker({"source": data.hex(), "witness": witness, "option_pin": option}))
    modeled = [call_worker({"modeled": case}) for case in cases]
    for row, expected_side in zip(modeled, ("reciprocal", "same"), strict=True):
        (first, edited) = tuple(value for value in observed if value["case"] == row["case"])
        roles = first["roles"]
        anti = [roles[index] for index in (1, 0, 3, 2)]
        demand(roles == edited["roles"], "the native driver edit changed the recorded stock role ordering")
        relation = "same" if row["roles"] == roles else "reciprocal" if row["roles"] == anti else "different"
        demand(relation == expected_side, "the historical pure-model role contrast no longer matches")
        wanted_points = first["positive_fin_endpoints_m"] if relation == "same" else first["positive_fin_endpoints_m"][::-1]
        demand(all(abs(left - right) <= 1e-12 for a, b in zip(row["positive_fin_endpoints_m"], wanted_points, strict=True)
                   for left, right in zip(a, b, strict=True)), "positive-fin contrast does not have its expected direction")
        row["native_saved_role_relation"] = relation
    receipt = {
        "schema": "kit.sw2026.edge-fillet-construction-boundary.v1", "base_revision": BASE,
        "evidence_input_sha256": SOURCE_PINS | {"disclosed_intent": INTENT_PIN},
        "proof_sha256": digest(HERE.read_bytes()), "saved_option_array_sha256": option,
        "same_encoding_chamfer_options_sha256": chamfer, "physical_saved_reads": observed, "model_only_stock_workers": modeled,
        "new_native_processes": 0, "fillet_writer_output_count": 0, "heldout_sources_read": 0,
        "guarded_processes": len(observed) + len(modeled),
        "guarded_external_accesses": sum(row["guarded_external_accesses"] for row in (*observed, *modeled)),
    }
    with args.report.open("xb") as stream:
        stream.write(job_bytes(receipt))
    print(digest(args.report.read_bytes()))


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker()
    else:
        demand(args.capture is not None and args.report is not None, "--capture and new --report are required")
        supervise(args)


if __name__ == "__main__":
    main()
