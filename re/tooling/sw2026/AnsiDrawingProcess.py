from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != TOOLS]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path.append(str(TOOLS))

from base64 import b64encode
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json

from DrawingSdkLinkedInput import linked_input
from OriginPairChild import make_child
from OriginChildShape import inspect_child
from OriginPairChecks import check_display
from SpatialTextMut import require, text_rows
from ansi_pair.Compose import child_mut, drawing_mut
from ansi_pair.Readback import fields
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
from convert.adapters.solidworks.Drawing.Construction.Profiles.MakeOriginFile import (
    MakeOriginFile,
)
from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors

AUDIT = BuildAudit(TOOLS / "serial/defs")
sys.addaudithook(AUDIT.InspectEvent)


def streams(value):
    return {
        name: {
            "bytes": len(data),
            "sha256": sha256(data).hexdigest(),
            "base64": b64encode(data).decode("ascii"),
        }
        for name, data in sorted(value.StreamsValue.items())
    }


def main():
    request = json.load(sys.stdin)
    require(
        set(request) == {"schema", "mode", "origin_request"}
        and request["schema"] == "kit.sw2026.ansi-drawing-request.v1",
        "ANSI full-pair request shape differs",
    )
    mode, job = request["mode"], request["origin_request"]
    require(mode in ("iso", "ansi"), "ANSI full-pair mode is unsupported")
    wanted_code, wanted_ui = (0, "moANSI_c") if mode == "ansi" else (1, "moISO_c")
    require(
        type(job["part"]["settings"]["styles"]["standard"]) is int
        and type(job["native"]["options"]["styles"]["standard"]) is int
        and job["part"]["settings"]["styles"]["standard"]
        == job["native"]["options"]["styles"]["standard"]
        == wanted_code,
        "complete authored part/drawing detail selectors disagree",
    )
    require(
        job["part"]["settings"]["definition"]["drafting_standard"]
        == job["native"]["ui"]["drafting_standard"]
        == wanted_ui,
        "complete authored part/drawing UI owners disagree",
    )
    require(
        job["origin_display"]
        == {"selection": "actual-child-origin", "population_argument": 0}
        and type(job["origin_display"]["population_argument"]) is int,
        "ANSI full pair needs the actual proved origin population operation",
    )
    seed = deepcopy(job)
    seed["part"]["settings"]["styles"]["standard"] = seed["native"]["options"][
        "styles"
    ]["standard"] = 1
    seed["part"]["settings"]["definition"]["drafting_standard"] = seed["native"]["ui"][
        "drafting_standard"
    ] = "moISO_c"
    for name in ("utf-16-le", "utf-8", "latin-1"):
        lookup(name)
    AUDIT.BeginBuild()
    child, settings, keys = make_child(seed)
    native = linked_input(
        {name: seed[name] for name in set(seed) - {"child_policy", "origin_display"}}
    )
    pair = MakeOriginFile(native, child)
    child = child_mut(child, settings, keys, mode)
    pair = drawing_mut(replace(pair, ChildValue=child), native, mode)
    loaded_child, loaded_drawing, presentation = fields(
        child.BytesValue,
        pair.BytesValue,
        native.DrawingValue.Sheets[0].Views[0].OrientationName,
        mode,
    )
    profile = check_display(
        loaded_drawing.GraphValue,
        loaded_child.ResolvedValue.RootsValue,
        loaded_child.ConfigValue.HeaderValue,
    )
    shape = inspect_child(
        loaded_child.ResolvedValue.RootsValue, job["child_policy"]["kind"]
    )
    require(
        shape
        == inspect_child(child.ResolvedValue.RootsValue, job["child_policy"]["kind"]),
        "ANSI operation changed child intent",
    )
    imports = sorted(
        name
        for name, module in tuple(sys.modules.items())
        if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
        and name
        not in {
            "__main__",
            "OriginPairChild",
            "OriginPairChecks",
            "OriginChildShape",
            "SpatialTextMut",
            "DrawingSdkLinkedInput",
            "DrawingSdkInput",
            "SdkBlindPartSettings",
        }
        and not name.startswith(("ansi_pair", "ansi_style"))
    )
    require(
        not AUDIT.DeniedReads and not imports,
        "ANSI pair crossed its input or implementation boundary",
    )
    return {
        "schema": "kit.sw2026.ansi-drawing-result.v1",
        "passed": True,
        "mode": mode,
        "child_base64": b64encode(child.BytesValue).decode("ascii"),
        "drawing_base64": b64encode(pair.BytesValue).decode("ascii"),
        "child_sha256": sha256(child.BytesValue).hexdigest(),
        "child_bytes": len(child.BytesValue),
        "drawing_sha256": sha256(pair.BytesValue).hexdigest(),
        "drawing_bytes": len(pair.BytesValue),
        "child_streams": streams(child),
        "drawing_streams": streams(pair),
        "presentation": presentation,
        "child_shape": shape,
        "profile": profile,
        "text_after": text_rows(child.ProfileValue.ProfileValue),
        "orientation": native.DrawingValue.Sheets[0].Views[0].OrientationName,
        "native_child_path": native.DrawingValue.ModelRefs[0].SourcePath,
        "native_drawing_path": native.FileValue.PathName,
        "runtime_input_file_access_attempts": len(AUDIT.DeniedReads),
        "sdk_research_imports": imports,
        "native_acceptance": False,
        "heldout_acceptance": False,
        "source_original_admission": False,
        "public_drawing_writer_changed": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(main(), sort_keys=True, ensure_ascii=False, allow_nan=False))
    except Exception as error:
        print(
            json.dumps(
                {
                    "passed": False,
                    "exception": type(error).__name__,
                    "diagnostic": str(error),
                    "runtime_input_file_access_attempts": len(AUDIT.DeniedReads),
                    "native_acceptance": False,
                }
            )
        )
        raise SystemExit(3)
