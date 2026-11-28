from argparse import ArgumentParser
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from subprocess import run
import sys

repo = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(repo), str(repo / "src")]

from convert import open_document
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.geometry.Models.Selection import Selection, SelectPathElem
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(raw):
    return sha256(raw).hexdigest()


def with_selection(document, selection):
    boss, cut = document.feature_timeline
    return replace(document, selections=(selection,),
                   feature_timeline=(boss, replace(cut, selection_ids=(selection.id,))))


def invoke(output, worker, label, request, expected):
    raw = encoded(request)
    (output / (label + ".Request.json")).write_bytes(raw)
    call = run([sys.executable, "-I", "-B", str(worker), str(repo)],
               input=raw, capture_output=True, timeout=90)
    (output / (label + ".stdout")).write_bytes(call.stdout)
    (output / (label + ".stderr")).write_bytes(call.stderr)
    if not expected:
        assert call.returncode and not call.stdout, label
        diagnostic = call.stderr.decode().strip().splitlines()[-1]
        assert diagnostic.startswith("ValueError:"), (label, diagnostic)
        return {"case": label, "status": call.returncode, "diagnostic": diagnostic,
                "request_sha256": digest(raw)}
    assert call.returncode == 0 and not call.stderr, (label, call.stderr.decode())
    report = json.loads(call.stdout)
    assert report["passed"] and report["runtime_input_file_reads"] == 0
    assert report["sdk_runtime_research_imports"] == 0
    return report


def inspect(selected, baseline, document):
    actual = open_document(selected, source_format="solidworks.sldprt")
    plain = open_document(baseline, source_format="solidworks.sldprt")
    assert not actual.validate() and not plain.validate() and not actual.brep_payloads
    assert actual.brep is not None and actual.brep == plain.brep
    assert actual.bodies[0].topology == plain.bodies[0].topology
    wanted_boss, wanted_cut = document.feature_timeline
    boss = next(value for value in actual.feature_timeline if value.name == wanted_boss.name)
    cut = next(value for value in actual.feature_timeline if value.name == wanted_cut.name)
    assert isinstance(wanted_cut.definition, ExtrudeFeature) and isinstance(cut.definition, ExtrudeFeature)
    assert cut.definition.length is None and cut.definition.end_condition == ExtrudeEnd.KThroughAll
    assert cut.definition.reversed == wanted_cut.definition.reversed
    assert cut.definition.second_end_condition == wanted_cut.definition.second_end_condition
    (selection,) = tuple(value for value in actual.selections if value.id == cut.id + ":stock-body")
    assert selection.id in cut.selection_ids and boss.id in cut.input_feature_ids
    assert selection.name == wanted_boss.name + " body"
    assert selection.path == (SelectPathElem("feature", boss.id, "body"),)
    assert actual.bodies[0].final_feature_id == cut.id
    evidence = actual.metadata["solidworks.typed_resolved_semantics"]["cut_body_dependency"]
    assert evidence["binding"] == "cold_selected_stock_atom" and evidence["feature_scope_code"] == 1
    return {"stock_path": [[value.entity_kind, value.entity_id, value.subelement] for value in selection.path],
            "cut_has_depth": False, "body_geometry_matches_all_body_fixture": True,
            "face_count": len(actual.brep.faces), "volume_mm3": actual.bodies[0].topology.volume}


def main():
    parser = ArgumentParser(description="Check the portable selected stock writer with fresh guarded processes")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    baseline = args.baseline.resolve(strict=True)
    output = args.output.resolve()
    prior_raw = (baseline / "Result.json").read_bytes()
    assert digest(prior_raw) == "130e70131b94102b1c67b01f565a189a6b9eee2fe577c50a692a36d7e0c6e3f1"
    prior = json.loads(prior_raw)
    worker = Path(__file__).with_name("ThroughAllNeutralProcess.py")
    output.mkdir()
    jobs = []
    cases = []
    input_hashes = {}
    for row in prior["repeat_build_cases"]:
        name = row["case"]
        raw = (baseline / (name + "A.Request.json")).read_bytes()
        input_hashes[name] = digest(raw)
        request = json.loads(raw)
        document = FromData(request["document"])
        boss, cut = document.feature_timeline
        selection = Selection("select/through-stock", boss.name + " body",
                              (SelectPathElem("feature", boss.id, "body"),))
        model = with_selection(document, selection)
        assert not model.validate()
        selected = request | {"document": ToData(model)}
        jobs.extend((name + side, selected, True) for side in (".A", ".B"))
        jobs.append((name + ".AllBodies", request, True))
        cases.append((row, model, request, selection))
    _, first, request, selection = cases[0]
    boss, cut = first.feature_timeline
    extra = replace(selection, id="select/additional-stock")
    negatives = [
        ("extra-owner", replace(first, selections=(selection, extra),
                                feature_timeline=(boss, replace(cut, selection_ids=(selection.id, extra.id))))),
        ("foreign-owner", with_selection(first, replace(selection, path=(SelectPathElem("feature", cut.id, "body"),)))),
        ("selected-face", with_selection(first, replace(selection, path=(SelectPathElem("feature", boss.id, "face"),)))),
        ("automatic-query", with_selection(first, replace(selection, query={"scope": "automatic"}))),
        ("arbitrary-caption", with_selection(first, replace(selection, name="Custom Selection Caption"))),
        ("coordinate", with_selection(first, replace(selection, point=SpaceVector(0, 0, 0)))),
        ("unprojected-attribute", with_selection(first, replace(selection, attributes={"scope-mode": "custom"}))),
        ("unbound-stock", replace(first, feature_timeline=(boss, replace(cut, selection_ids=())))),
        ("stock-selects-itself", replace(first, feature_timeline=(replace(boss, selection_ids=(selection.id,)), cut))),
    ]
    jobs.extend((name, request | {"document": ToData(model)}, False) for name, model in negatives)
    (output / "Before.json").write_bytes(encoded({"baseline_result_sha256": digest(prior_raw),
                                                "original_request_sha256": input_hashes,
                                                "worker_sha256": digest(worker.read_bytes()),
                                                "requests": {name: digest(encoded(data)) for name, data, _ in jobs}}))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda item: invoke(output, worker, *item), jobs))
    report_cases = []
    allowed_delta = {"Contents/Config-0", "Contents/Config-0-ResolvedFeatures"}
    for index, (row, document, _, _) in enumerate(cases):
        first, second, all_bodies = results[3 * index:3 * index + 3]
        assert first == second and row["sha256"] == all_bodies["sha256"]
        payload = b64decode(first.pop("generated"), validate=True)
        old = b64decode(all_bodies.pop("generated"), validate=True)
        assert digest(payload) == first["sha256"] and digest(old) == row["sha256"]
        (output / (row["case"] + ".SLDPRT")).write_bytes(payload)
        assert first["streams"].keys() == all_bodies["streams"].keys()
        changed = {name for name, value in first["streams"].items() if value != all_bodies["streams"][name]}
        assert changed == allowed_delta, changed
        report_cases.append({"case": row["case"], "sha256": first["sha256"], "bytes": first["bytes"],
                             "unchanged_all_body_sha256": all_bodies["sha256"], "repeat_build_identical": True,
                             "changed_scope_streams": sorted(changed), "public_readback": inspect(payload, old, document),
                             "streams": first["streams"]})
    changed_labels = [name for name in report_cases[0]["streams"]
                      if report_cases[0]["streams"][name]["bytes"] != report_cases[-1]["streams"][name]["bytes"]]
    assert {"Contents/Config-0-ResolvedFeatures", "swXmlContents/KeyWords"} <= set(changed_labels)
    report = {"schema":"kit.sw2026.neutral-selected-through-all.v1","passed":True,
              "guarded_workers":len(jobs),"constructor_file_reads":0,"runtime_research_imports":0,
              "baseline_result_sha256":digest(prior_raw),"method_sha256":digest(Path(__file__).read_bytes()),
              "before_sha256":digest((output/"Before.json").read_bytes()),"cases":report_cases,
              "streams_with_authored_length_changes":changed_labels,"atomic_rejections":results[3*len(cases):],
              "native_oracle_run":False,"heldout_inputs_read":0,"public_writer_qualified":False}
    result = encoded(report)
    (output / "Result.json").write_bytes(result)
    print(json.dumps({"passed":True,"workers":len(jobs),"cases":len(report_cases),
                      "rejects":len(negatives),"result_sha256":digest(result)}))


if __name__ == "__main__":
    main()
