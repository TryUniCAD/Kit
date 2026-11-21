from dataclasses import replace
from types import MappingProxyType

from ansi_normalization.Compose import compose_drawing as compose_document_drawing
from SpatialTextMut import concrete, require
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Drawing.Construction.Linked.LinkedDrawFile import (
    LinkedDrawFile,
)
from convert.adapters.solidworks.Drawing.Definition.Named.WriteNamedDef import (
    WriteNamedDef,
)


def validate_policy(policy):
    require(
        type(policy) is dict
        and set(policy) == {"policy", "file_version", "explicit_centerline"},
        "drawing load initialization requires its exact neutral policy",
    )
    require(
        type(policy["file_version"]) is int and policy["file_version"] == 19000,
        "drawing load initialization only proves ordinary version19000",
    )
    require(
        type(policy["policy"]) is str
        and policy["policy"] in ("constructor", "native-19000"),
        "unknown drawing load initialization operation",
    )
    intent = policy["explicit_centerline"]
    require(
        intent is None or type(intent) is bool,
        "centreline intent requires an explicit Boolean or no independent intent",
    )
    require(
        intent is not False,
        "explicit false centreline intent cannot be preserved by the19000 drawing loader",
    )
    require(
        policy["policy"] != "constructor" or intent is None,
        "constructor-only comparison cannot promise a separate centreline intent",
    )
    return policy["policy"]


def drawing_details(pair, mode):
    require(type(pair) is LinkedDrawFile, "drawing initialization needs its fresh pair")
    require(
        type(pair.UiGraph.VersionValue) is int and pair.UiGraph.VersionValue == 19000,
        "actual drawing archive version differs",
    )
    ui = concrete(pair.UiGraph.DocumentValue, "uiDrawingDoc_c")
    model = concrete(ui.FieldsValue["model"], "moDrawing_c")
    child = concrete(pair.ChildValue.SystemValue.RootValue, "moPart_c")
    require(
        model is pair.ModelGraph.ModelValue and model is not child,
        "drawing initialization has a different actual model owner",
    )
    wanted = "moANSI_c" if mode == "ansi" else "moISO_c"
    standard = concrete(ui.FieldsValue["fba8"], wanted)
    require(not standard.FieldsValue, "actual UI standard has another body")
    details = model.FieldsValue["fae0"]
    require(
        type(details) is dict
        and details is not child.FieldsValue["fae0"]
        and type(details["f10"]) is int
        and details["f10"] == (0 if mode == "ansi" else 1),
        "drawing detail owner or standard selector differs",
    )
    require(
        type(details["f20"]) is int and 0 <= details["f20"] <= 0xFFFFFFFF,
        "drawing detail flags require an actual unsigned word",
    )
    return details


def compose_drawing(pair, inputs, mode, initialization, policy):
    operation = validate_policy(policy)
    require(
        initialization == "document-units",
        "load experiment requires initialized styles",
    )
    pair = compose_document_drawing(pair, inputs, mode, initialization)
    details = drawing_details(pair, mode)
    before = details["f20"]
    require(
        bool(before & 0x100000) == (mode == "iso"),
        "fresh standard operation differs from its native centreline constructor rule",
    )
    after = before | 0x100000 if operation == "native-19000" else before
    report = {
        "owner": "uiDrawingDoc_c.model.fae0.f20",
        "file_version": 19000,
        "mask": 0x100000,
        "before": before,
        "after": after,
        "operation": operation,
        "changed": before != after,
        "actual_ui_model_alias": True,
        "primary_detail_distinct_from_child": True,
        "scope": "fresh generated drawing only; no runtime override APIs",
        "native_acceptance": False,
    }
    if before == after:
        return pair, report
    details["f20"] = after
    streams = dict(pair.StreamsValue)
    streams["Contents/Definition"] = WriteNamedDef(pair.UiGraph).OutputValue
    return (
        replace(
            pair,
            StreamsValue=MappingProxyType(streams),
            BytesValue=BuildSldprt(streams),
        ),
        report,
    )
