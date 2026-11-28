from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != TOOLS]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path.append(str(TOOLS))

from codecs import lookup
from copy import deepcopy
from dataclasses import replace
import json

from DrawingSdkLinkedInput import part_settings
from EpochClocks import require
from OriginPairChild import make_child
from convert.adapters.solidworks.Archive.Construction.Part.MakeRectDimPart import MakeRectDimPart
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import RectDimInput
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors
from interchange.serialization.Deserialize import FromData
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

AUDIT = BuildAudit(TOOLS / "serial/defs")
sys.addaudithook(AUDIT.InspectEvent)


def main():
    request = json.load(sys.stdin)
    require(set(request) == {"mode", "request"}
            and request["mode"] in ("published-earlier-modified", "published-independent-history"),
            "published guard process requires its exact declared mode")
    value = request["request"]
    job = deepcopy(value["origin_request"])
    mode = request["mode"]
    expected = ("header modification time precedes document creation" if mode == "published-earlier-modified"
                else "part provenance must agree across folders header and history")
    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        lookup(encoding)
    AUDIT.BeginBuild()
    try:
        if mode == "published-earlier-modified":
            provenance = job["part"]["settings"]["provenance"]
            provenance["modified_at"] = value["clock_plan"]["ModifiedAt"]
            require(provenance["modified_at"] < provenance["created_at"], "guard probe did not supply the intended temporal refusal")
            make_child(job)
        else:
            settings = part_settings(job)
            settings = replace(settings, HistoryValue=replace(settings.HistoryValue,
                                                                CreatedAt=value["clock_plan"]["VersionHistoryFirstEventAt"]))
            require(settings.HistoryValue.CreatedAt != settings.HeaderValue.CreatedAt,
                    "guard probe did not supply independent history provenance")
            policy = job["child_policy"]
            inputs = RectDimInput(tuple(policy["width_text_m"]), tuple(policy["height_text_m"]),
                                  settings.DesignIntent, settings.SelectedLeader, policy["route_centerline"])
            MakeRectDimPart(FromData(job["part"]["document"]), settings, inputs)
    except ValueError as error:
        require(str(error) == expected and not AUDIT.DeniedReads,
                "published factory did not preserve its exact prior refusal: " + str(error))
        return {"passed": True, "mode": mode, "expected_refusal": True, "diagnostic": str(error),
                "runtime_input_file_access_attempts": len(AUDIT.DeniedReads),
                "native_acceptance": False, "production_guards_changed": False}
    raise ValueError("published factory unexpectedly admitted the unqualified clock model")


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, allow_nan=False))
    except Exception as error:
        print(json.dumps({"passed": False, "exception": type(error).__name__, "diagnostic": str(error),
                          "runtime_input_file_access_attempts": len(AUDIT.DeniedReads), "native_acceptance": False}))
        raise SystemExit(3)
