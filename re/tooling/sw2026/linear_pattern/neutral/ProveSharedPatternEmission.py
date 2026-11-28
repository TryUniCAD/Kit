from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from subprocess import run
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1])]


def wire(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False, ensure_ascii=False, indent=2) + "\n").encode()


def digest(value):
    return sha256(value).hexdigest()


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def read_presentation(value):
    from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import PatDriveStyle
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAngleStyle import PatAngleStyle
    from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import PatPresentInput
    from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import AnnoViewInput

    label = value["angle"]
    return PatPresentInput(
        PatAngleStyle(label["parameter_id"], label["annotation_view"], label["design_intent"],
                      label["selected_leader"], tuple(label["shifted_point_m"])),
        value["count_parameter_id"], value["pitch_parameter_id"],
        tuple(PatDriveStyle(row["name"], row["annotation_view"], tuple(row["label_m"]),
                            row["design_intent"], row["selected_leader"]) for row in value["styles"]),
        tuple(AnnoViewInput(row["name"], tuple(map(tuple, row["basis"]))) for row in value["views"]),
        value["active"], tuple(value["shown"]),
    )


def worker():
    from LocalPatternContainerProcess import linked
    from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
    from convert.adapters.solidworks.Archive.Construction.Patterns.Emission.EmitPatArchive import EmitPatArchive
    from convert.adapters.solidworks.Archive.Construction.Patterns.Graph.MakePatGraph import MakePatGraph
    from convert.adapters.solidworks.Core.Preparation.Patterns.PlanLinPattern import PlanLinPattern
    from interchange import PlaneAxis
    from interchange.document.Behavior import DocumentIo
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.document.Validation import DocumentAssemblyValidate, DocumentFeatureValidate, DocumentReferenceValidate
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    for codec in ("utf-8", "utf-16-le", "latin-1", "us-ascii"):
        lookup(codec)
    request = json.load(sys.stdin)
    present = read_presentation(request["presentation"])
    target = SelfFileInput(request["target"]["PathName"], request["target"]["SavedAt"])
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    document_wire = wire(request["document"])
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    document = CadDocument.from_json(document_wire.decode())
    require(type(document.feature_timeline[2].definition) is PlaneAxis, "actual finite axis type changed")
    graph = MakePatGraph(PlanLinPattern(document, target, present))
    streams, payload = EmitPatArchive(graph)
    link, headers = linked(payload, streams)
    require(len(streams) == 10 and len(graph.RootsValue) == len(link.ResolvedValue.RootsValue) == 24
            and len(headers) == 2, "complete pattern stream and root inventories differ")
    require(wire(document.to_dict()) == document_wire and not audit.DeniedReads,
            "pattern construction changed the document or read a runtime input")
    print(json.dumps({"bytes": len(payload), "sha256": digest(payload),
                      "streams": {key: digest(content) for key, content in streams.items()},
                      "configuration_map": link.ConfigValue.MapValue.CounterValue,
                      "resolved_map": link.ResolvedValue.MapValue.CounterValue,
                      "runtime_reads": len(audit.DeniedReads)}, sort_keys=True))


def execute(request):
    return run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=wire(request),
               cwd=ROOT, capture_output=True, check=False, timeout=60)


def supervise(disclosed, output):
    from ProveNeutralPattern import EXPECTED, author_document, validated_disclosed

    _, expected = validated_disclosed(disclosed)
    cases, original = {}, None
    for name, states in sorted(expected.items()):
        measured = {}
        for kind, state in sorted(states.items()):
            authored = author_document(state["modeled_input"])
            request = {"document": authored.document.to_dict(), "target": asdict(authored.output),
                       "presentation": asdict(authored.presentation)}
            result = execute(request)
            require(result.returncode == 0 and not result.stderr, result.stderr.decode())
            row = json.loads(result.stdout)
            require(row["sha256"] == state["native_container"]["sha256"]
                    and row["bytes"] == state["native_container"]["bytes"] and not row["runtime_reads"],
                    "shared planner and emitter differ from the complete frozen disclosed file")
            prior_streams = {key: value["sha256"] for key, value in state["streams"].items()}
            require(prior_streams == row["streams"], "shared generated native stream changed")
            measured[kind] = row
            if kind == "original" and original is None:
                original = state["modeled_input"]
        cases[name] = measured
    require(len(cases) == 2 and all(len(states) == 3 for states in cases.values()), "incomplete model comparison")
    negative = json.loads(wire(original))
    negative["pattern"]["pitch_m"] = 0.875
    authored = author_document(negative)
    request = {"document": authored.document.to_dict(), "target": asdict(authored.output),
               "presentation": asdict(authored.presentation)}
    refusal = execute(request)
    require(refusal.returncode != 0 and not refusal.stdout and
            "wholly interior to the plate" in refusal.stderr.decode(), "excessive pitch did not fail before emission")
    report = {"schema": "kit.sw2026.shared-pattern-emission.v1", "disclosed_authority": EXPECTED,
              "complete_pattern_states": 6, "linked_streams": 60, "guarded_processes": 7,
              "runtime_file_reads": 0, "protected_inputs_read": 0, "additional_native_processes": 0,
              "public_writer_registered": False, "overhanging_footprint_refused": True, "cases": cases,
              "observer_sha256": digest(HERE.read_bytes())}
    with output.open("xb") as handle:
        handle.write(wire(report))
    print(digest(output.read_bytes()))


def main():
    if sys.argv[1:] == ["--worker"]:
        worker()
    else:
        parser = ArgumentParser(description="Reproduce complete local pattern files from shared SDK preparation")
        parser.add_argument("--disclosed", required=True, type=Path)
        parser.add_argument("--output", required=True, type=Path)
        args = parser.parse_args()
        supervise(args.disclosed, args.output)


if __name__ == "__main__":
    main()
