from codecs import lookup
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parent.parent),
                str(HERE.parents[2]), str(HERE.parents[2] / "serial")]

from LocalPatternContainerProcess import audit, linked, observations_with_refusals, verify_keywords

from convert.adapters.solidworks.Container.Format import KeywordsStream
from interchange.document.Validation import DocumentAssemblyValidate, DocumentFeatureValidate, DocumentReferenceValidate
from interchange.serialization.Deserialize import FromData
from interchange.serialization.EncodeData import ToData

from CheckPatternAngleOwners import require
from EmitLocalPattern import emit_pattern
from NeutralPatternInput import register_input_types
from ProjectNeutralPattern import project


APPLICATION_MODULES = {"FreeCAD", "FreeCADGui", "Part", "adsk", "pythoncom", "win32com"}


def identity(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def modeled_request(plan):
    seed, axis, angle, annotation, pattern = plan
    return {"seed": asdict(seed), "axis": axis, "plane": asdict(angle),
            "annotation": annotation, "pattern": asdict(pattern)}


def main():
    mode = sys.argv[1:]
    require(mode in ([], ["--binary"], ["--without-axis-type"]), "unexpected neutral pattern process mode")
    register_input_types(with_axis=mode != ["--without-axis-type"])
    for encoding in ("utf-16-le", "utf-8", "latin-1", "us-ascii"):
        lookup(encoding)
    data = json.load(sys.stdin)
    audit.BeginBuild()
    request = FromData(data)
    require(ToData(request) == data, "neutral typed wire did not round trip")
    plan = project(request)
    graph, streams, binary = emit_pattern(*plan)
    link, headers = linked(binary, streams)
    owners, refused = observations_with_refusals(link, headers, plan)
    verify_keywords(streams[KeywordsStream], plan, owners)
    require(not audit.DeniedReads and len(streams) == 10 and len(refused) == 9
            and not {name.split(".")[0] for name in sys.modules} & APPLICATION_MODULES,
            "neutral proof did not retain its exact guarded archive")
    if mode == ["--binary"]:
        sys.stdout.buffer.write(binary)
        return
    receipt = {
        "native_container": {**identity(binary), "version": 4},
        "neutral_owner_counts": {name: len(getattr(request.document, name))
                                 for name in ("feature_timeline", "sketches", "support_planes", "parameters", "selections", "bodies")},
        "modeled_input": modeled_request(plan), "neutral_wire_roundtrip": True,
        "typed_replay_count": 9, "guarded_runtime_reads": 0, "application_modules_loaded": 0,
        "observed": owners, "analytic_geometry": graph.measure,
        "streams": {name: identity(payload) for name, payload in streams.items()},
        "map_counters": [link.ConfigValue.MapValue.CounterValue, link.ResolvedValue.MapValue.CounterValue],
        "refused_typed_archive_contrasts": sorted(refused),
    }
    print(json.dumps(receipt, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
