from __future__ import annotations

import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parents[2]
sys.path[:] = [value for value in sys.path if Path(value or ".").resolve() != TOOLS]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
sys.path.append(str(TOOLS))

from base64 import b64decode
from io import StringIO
import json

from AnsiNormalizationPrepare import main as prepare_pair
from SpatialTextMut import concrete, require
from ansi_pair.Readback import fields


def main():
    source = json.load(sys.stdin)
    require(
        source["schema"] == "kit.sw2026.ansi-load-result.v1"
        and source["passed"] is True,
        "load initialization preparation requires a complete pair",
    )
    policy = source["drawing_load"]
    require(
        type(policy) is dict
        and set(policy) == {"policy", "file_version", "explicit_centerline"}
        and type(policy["file_version"]) is int
        and policy["file_version"] == 19000
        and policy["policy"] in ("constructor", "native-19000")
        and (
            policy["explicit_centerline"] is None
            or policy["explicit_centerline"] is True
        ),
        "independent drawing load policy differs",
    )
    require(
        source["mode"] in ("iso", "ansi")
        and (
            policy["policy"] != "constructor" or policy["explicit_centerline"] is None
        ),
        "independent constructor policy has a conflicting intent",
    )
    child, drawing, observed = fields(
        b64decode(source["child_base64"], validate=True),
        b64decode(source["drawing_base64"], validate=True),
        source["orientation"],
        source["mode"],
    )
    ui = concrete(drawing.GraphValue.DocumentValue, "uiDrawingDoc_c")
    model = concrete(ui.FieldsValue["model"], "moDrawing_c")
    child_model = concrete(child.ConfigValue.RootValue, "moPart_c")
    require(
        model is not child_model
        and model.FieldsValue["fae0"] is not child_model.FieldsValue["fae0"]
        and observed == source["presentation"],
        "independent drawing detail graph aliases or full presentation differ",
    )
    operation = source["drawing_load_operation"]
    actual = model.FieldsValue["fae0"]["f20"]
    require(
        type(actual) is int
        and 0 <= actual <= 0xFFFFFFFF
        and operation["after"] == actual
        and type(operation["before"]) is int
        and type(operation["after"]) is int
        and operation["mask"] == 0x100000
        and operation["owner"] == "uiDrawingDoc_c.model.fae0.f20"
        and operation["actual_ui_model_alias"] is True
        and operation["primary_detail_distinct_from_child"] is True,
        "independent actual detail mask or ownership report differs",
    )
    wanted = 1 if source["mode"] == "iso" or policy["policy"] == "native-19000" else 0
    require(
        bool(actual & 0x100000) == bool(wanted)
        and bool(source["presentation"]["child_details"]["f20"] & 0x100000)
        == (source["mode"] == "iso"),
        "load initialization changed the wrong model detail owner",
    )
    expected = operation["before"]
    if policy["policy"] == "native-19000":
        expected |= 0x100000
    require(
        expected == operation["after"]
        and operation["operation"] == policy["policy"]
        and operation["changed"] is (operation["before"] != operation["after"]),
        "load initialization changed flags outside its exact operation",
    )
    original_stdin = sys.stdin
    try:
        sys.stdin = StringIO(
            json.dumps(dict(source, schema="kit.sw2026.ansi-normalization-result.v1"))
        )
        result = prepare_pair()
    finally:
        sys.stdin = original_stdin
    result.update(
        schema="kit.sw2026.ansi-load-preparation.v1",
        drawing_load=policy,
        drawing_load_operation=operation,
        full_presentation_retention_required=True,
    )
    return result


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
                    "native_acceptance": False,
                }
            )
        )
        raise SystemExit(3)
