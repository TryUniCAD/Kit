from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring

from Core import Obj
from Streams import StreamDoc, store_rooted

FILE_VERSION = 19000
COUNTER_SEED = 101
LICENSE_ORIGINS = frozenset((0, 10, 20, 30, 40, 50))
KEYWORD_TAGS = frozenset(("Feature", "Sketch", "Extrusion"))


def integer(value, name, low=0, high=0xFFFFFFFF):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def boolean(value, name):
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def text(value, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text")
    if any(not (ord(c) in (9, 10, 13) or 0x20 <= ord(c) <= 0xD7FF or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF) for c in value):
        raise ValueError(f"{name} contains a character outside XML 1.0")
    return value


def sequence(value, name):
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{name} must be a sequence")
    return tuple(value)


def fields(value, name, required, optional=()):
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a semantic mapping")
    if any(not isinstance(key, str) for key in value):
        raise ValueError(f"{name} field names must be text")
    missing = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if missing or extra:
        raise ValueError(f"{name} fields differ: missing {sorted(missing)!r}, unsupported {sorted(extra)!r}")
    return value


def string_array(*, values):
    values = sequence(values, "string array")
    return Obj("su_CStringArray", {"n": len(values), "items": [{"s": text(s, "array string")} for s in values]})


def object_list(*, values):
    values = sequence(values, "object list")
    if any(not isinstance(value, Obj) for value in values):
        raise ValueError("object list entries must be freshly constructed archive objects")
    return Obj("suObList", {"n": len(values), "items": [{"o": value} for value in values]})


def stamp(*, status, user_index, company_index, timestamp, comment):
    if integer(status, "revision status", high=0xFFFF) != 0:
        raise ValueError("only the recovered fresh-state revision status 0 is supported")
    return {
        "f08": status,
        "f0c": integer(user_index, "user index", high=0xFFFE),
        "f10": integer(company_index, "company index", high=0xFFFE),
        "f18": integer(timestamp, "stamp timestamp"),
        "f20": text(comment, "revision comment"),
    }


def semantic_stamp(value):
    value = fields(value, "stamp", ("status", "user_index", "company_index", "timestamp", "comment"))
    return stamp(**value)


def header(*, next_id, user_names, company_names, revision_logs, created_at, modified_at, updated_at, model_present, component_count, update_stamp, body_stamp, license_flags, license_type):
    next_id = integer(next_id, "next persistent id", low=1, high=0x7FFFFFFF)
    users = tuple(text(s, "user name") for s in sequence(user_names, "user names"))
    companies = tuple(text(s, "company name") for s in sequence(company_names, "company names"))
    if not users or not companies or len(users) > 0xFFFF or len(companies) > 0xFFFF:
        raise ValueError("header user/company tables must each contain 1..65535 authored names")
    if len(set(users)) != len(users) or len(set(companies)) != len(companies):
        raise ValueError("fresh header user/company tables must contain unique authored names")
    users_object = string_array(values=users)
    companies_object = string_array(values=companies)
    created_at = integer(created_at, "creation timestamp")
    modified_at = integer(modified_at, "modification timestamp", low=created_at)
    updated_at = integer(updated_at, "update timestamp")
    model_present = boolean(model_present, "owning model presence")
    component_count = integer(component_count, "component count", high=0x7FFFFFFF)
    if component_count:
        raise ValueError("component reference metadata is outside the recovered fresh-part header construction")
    if integer(license_flags, "license flags") or integer(license_type, "license type"):
        raise ValueError("nonzero header license metadata has no recovered construction domain; provenance must not be cleared")
    logs = []
    seen = set()
    for value in sequence(revision_logs, "revision logs"):
        value = fields(value, "revision log", ("object_id", "stamps"), ("name",))
        owner = integer(value["object_id"], "revision log object id", high=next_id - 1)
        if owner in seen:
            raise ValueError("revision log object ids must be unique")
        seen.add(owner)
        entries = [semantic_stamp(v) for v in sequence(value["stamps"], "revision stamps")]
        if not entries:
            raise ValueError("a revision log must contain an authored stamp")
        for entry in entries:
            if entry["f0c"] >= len(users) or entry["f10"] >= len(companies):
                raise ValueError("revision stamp index lies outside its header name table")
        if text(value.get("name", ""), "revision log name"):
            raise ValueError("nonempty moLogs_c.f50 semantics are not recovered")
        stamps = [Obj("moStamp_c", entry) for entry in entries]
        logs.append(Obj("moLogs_c", {"n": len(stamps), "items": [{"o": s} for s in stamps], "f48": owner, "f50": ""}))
    if not logs:
        raise ValueError("fresh header construction requires an explicit revision log")
    if logs[0].f["items"][0]["o"].f["f18"] != created_at:
        raise ValueError("creation timestamp must match the first revision log's first stamp")
    f = {name: 0 for name in (
        "f58", "f60", "f64", "f68", "f78", "fc0", "fc8", "f98", "f9c", "fa0", "fa4", "fa8", "fac", "fb0", "fe8", "ff0", "ff4", "ff8", "ffc", "f100", "f104", "f108", "f10c",
    )}
    f.update({
        "fec": int(model_present), "f10": users_object, "f18": companies_object,
        "f20": object_list(values=logs), "f50": modified_at, "f08": next_id,
        "f30": None, "f40": integer(update_stamp, "update stamp", low=COUNTER_SEED),
        "f38": None, "f44": integer(body_stamp, "body stamp", low=COUNTER_SEED),
        "f70": created_at, "f28": None, "fc4": component_count,
        "f7c": license_flags, "f48": updated_at, "f88": None, "bboxflag": 0,
        "fcc": -1, "fd0": -1, "fd4": -1, "f80": license_type,
    })
    return Obj("moHeader_c", f)


def biography():
    return Obj("moBiography_c", {"n": 0, "records": []})


def history(*, states, failure_severity, minimum_free_memory, license_origin, language_id, cjk_saved, cjk_warning):
    values = []
    for state in sequence(states, "version states"):
        state = fields(state, "version state", ("file_version", "date_codes", "stamp"))
        if integer(state["file_version"], "history file version") != FILE_VERSION:
            raise ValueError("fresh history construction supports only the recovered 19000 format")
        codes = []
        for value in sequence(state["date_codes"], "date-code provenance"):
            value = fields(value, "date-code provenance", ("build_code", "native_save"))
            code = integer(value["build_code"], "explicit originating build code", low=1, high=0xFFFFFF)
            native_save = boolean(value["native_save"], "native-save provenance")
            if native_save:
                raise ValueError("retaining a native-save history flag requires recovered provenance semantics; it must not be fabricated or cleared")
            codes.append({"st": {"f08": code}})
        if not codes:
            raise ValueError("history requires explicit build provenance; zero is not a proven neutral code")
        values.append({"st": {"f08": semantic_stamp(state["stamp"]), "f30": FILE_VERSION,
                               "f38": Obj("moDateCodeHistory_c", {"n": len(codes), "states": codes})}})
    if not values:
        raise ValueError("version history cannot be empty")
    license_origin = integer(license_origin, "license-origin provenance", high=50)
    if license_origin not in LICENSE_ORIGINS:
        raise ValueError("license-origin provenance is outside the recovered categories")
    language_id = integer(language_id, "language id", high=0xFFFF)
    cjk_saved = boolean(cjk_saved, "CJK saved state")
    cjk_warning = boolean(cjk_warning, "CJK warning state")
    if (language_id & 0x3FF) in (4, 17, 18) and not cjk_saved:
        raise ValueError("Chinese/Japanese/Korean save language requires the recovered CJK saved flag")
    return Obj("moVersionHistory_c", {
        "n": len(values), "states": values,
        "f28": integer(failure_severity, "failure severity", high=0x7FFFFFFF),
        "f2c": integer(minimum_free_memory, "minimum free-memory provenance"),
        "f30": license_origin, "f38": language_id, "f3c": int(cjk_saved), "f40": int(cjk_warning),
    })


def keywords(*, name, timestamp, configurations, features):
    root = Element("Keywords", {"id": str(integer(timestamp, "keyword timestamp")), "Name": text(name, "document name")})
    config_ids = set()
    for value in sequence(configurations, "configurations"):
        value = fields(value, "configuration", ("id", "name", "material"))
        key = integer(value["id"], "configuration id", high=0x7FFFFFFF)
        if key in config_ids:
            raise ValueError("configuration ids must be unique")
        config_ids.add(key)
        SubElement(root, "Configuration", {"id": str(key), "Name": text(value["name"], "configuration name"), "Type": "ConfigurationManager", "Material": text(value["material"], "configuration material")})
    if not config_ids:
        raise ValueError("keyword metadata requires a configuration")
    feature_ids = set()
    pending = []
    for value in sequence(features, "features"):
        value = fields(value, "feature", ("id", "name", "kind"), ("tag", "dimensions", "children", "dissectable", "root"))
        key = integer(value["id"], "feature id", low=1, high=0x7FFFFFFF)
        if key in feature_ids:
            raise ValueError("keyword feature ids must be unique")
        feature_ids.add(key)
        tag = text(value.get("tag", "Feature"), "feature tag")
        if tag not in KEYWORD_TAGS:
            raise ValueError(f"unsupported keyword feature tag {tag!r}")
        attrs = {"id": str(key), "Name": text(value["name"], "feature name"), "Type": text(value["kind"], "feature kind")}
        if "dissectable" in value:
            attrs["Dissectable"] = str(boolean(value["dissectable"], "dissectable state")).lower()
        if "root" in value:
            attrs["DissectableRoot"] = str(boolean(value["root"], "dissectable root state")).lower()
        children = tuple(integer(c, "child feature id", low=1, high=0x7FFFFFFF) for c in sequence(value.get("children", ()), "child features"))
        if len(children) > 1:
            raise ValueError("keyword encoding for multiple dissectable children is not recovered")
        if children:
            attrs["DissectableChildren"] = ",".join(map(str, children))
        pending.extend(children)
        node = SubElement(root, tag, attrs)
        names = set()
        for dimension in sequence(value.get("dimensions", ()), "feature dimensions"):
            dimension = fields(dimension, "dimension", ("name", "value"))
            dimension_name = text(dimension["name"], "dimension name")
            if dimension_name in names:
                raise ValueError("dimension names must be unique within their feature")
            names.add(dimension_name)
            number = dimension["value"]
            try:
                valid = type(number) in (int, float) and math.isfinite(number)
            except OverflowError:
                valid = False
            if not valid:
                raise ValueError("keyword dimensions must be finite authored numbers in presentation units")
            SubElement(node, "Dimension", {"Name": dimension_name}).text = str(number) if type(number) is int else format(number, ".17g")
    if not feature_ids or any(key not in feature_ids for key in pending):
        raise ValueError("keyword metadata must contain its feature nodes and every referenced child")
    return b"\x86<?xml version=\"1.0\" encoding=\"UTF-8\"?>\r\n" + tostring(root, encoding="utf-8", short_empty_elements=True) + b"\r\n"


def streams(*, registry, header2, model_headers, biography_record, history_record, keywords_data):
    if not isinstance(model_headers, Mapping) or not model_headers:
        raise ValueError("metadata streams require a model header for each generated configuration")
    records = {"Header2": (header2, "moHeader_c"),
               "_MO_VERSION_19000/Biography": (biography_record, "moBiography_c"),
               "_MO_VERSION_19000/History": (history_record, "moVersionHistory_c")}
    for key, value in model_headers.items():
        key = integer(key, "configuration id", high=0x7FFFFFFF)
        records[f"Contents/Config-{key}-ModelHeader"] = (value, "moHeader_c")
    if not isinstance(keywords_data, bytes) or not keywords_data.startswith(b"\x86<?xml"):
        raise ValueError("keyword data must come from the keyword constructor")
    keyword_root = fromstring(keywords_data[1:])
    if keyword_root.tag != "Keywords" or {int(node.attrib["id"]) for node in keyword_root.findall("Configuration")} != set(model_headers):
        raise ValueError("keyword configurations must match the generated model-header stream ids")
    out = {}
    for name, (record, cls) in records.items():
        if not isinstance(record, Obj) or record.cls != cls:
            raise ValueError(f"{name} requires a constructed {cls}")
        doc = StreamDoc(name, {"base": 1}, [record])
        out[name] = store_rooted(doc, registry, FILE_VERSION)
    for key, field in (("f0c", "f10"), ("f10", "f18")):
        reference_names = [e["s"] for e in header2.f[field].f["items"]]
        for state in history_record.f["states"]:
            index = state["st"]["f08"][key]
            if not 0 <= index < len(reference_names):
                raise ValueError("history stamp index lies outside the header's authored name table")
            for record in model_headers.values():
                names = [e["s"] for e in record.f[field].f["items"]]
                if index >= len(names) or names[index] != reference_names[index]:
                    raise ValueError("history provenance resolves to different users or companies across headers")
    out["swXmlContents/KeyWords"] = keywords_data
    return out
