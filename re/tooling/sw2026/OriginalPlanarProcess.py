import argparse
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root), str(root / "src"), str(root / "re/tooling/sw2026")]
    from interchange import CadDocument
    from interchange.serialization.EncodeData import ToData
    from OriginalPlanarNames import project, require
    from OriginalPlanarRecipe import translate
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmInput import MakeAsmInput
    from tests.Convert.Solidworks.Research.Construction.Part.BlindCaseInput import BlindCaseInput
    from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc

    audit = BuildAudit(root / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    incoming = json.load(sys.stdin)
    require(set(incoming) == {"document_json", "case", "dimensions_m", "output"}, "the semantic translation stage requires its complete declared stdin envelope")
    document = CadDocument.from_json(incoming["document_json"])
    document.assert_valid()
    audit.BeginBuild()
    names = project(document, incoming["case"], tuple(incoming["dimensions_m"]))
    request, prediction = translate(incoming["case"], names, incoming["output"], tuple(incoming["dimensions_m"]))
    forbidden = sorted(name for name in sys.modules if name == "Swapp" or name == "pythoncom" or name.startswith("win32com"))
    require(not forbidden and not audit.DeniedReads, "the semantic translation stage read a runtime file or imported CAD automation")
    return {"schema": "kit.sw2026.original-planar-semantic-stage.v1", "passed": True,
            "worker_pid": os.getpid(), "names": names, "request": request, "prediction": prediction,
            "runtime_input_file_reads": len(audit.DeniedReads), "com_imports": forbidden,
            "source_native_payload_or_cache_values_forwarded": False,
            "native_processes_started": 0, "native_acceptance": False}


if __name__ == "__main__":
    print(json.dumps(main(), sort_keys=True, allow_nan=False))
