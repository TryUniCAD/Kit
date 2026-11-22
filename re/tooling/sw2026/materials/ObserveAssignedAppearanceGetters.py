from argparse import ArgumentParser
from contextlib import redirect_stderr, redirect_stdout
from hashlib import sha256
from math import isclose, isfinite
import json
import os
from pathlib import Path, PureWindowsPath
import struct
import sys
import time
import traceback


BASE = "a84a6578041643558e38c12910d405f24150babd"
SDK_TREE = "30dab695fbd7704c3ac227e925a77baf81deec83"
ARCHIVE_RECEIPT = "280e6648f0dd6a90eb25dd257dc0419f2be00b0e6c220bc1bfcfdf36f023db88"
NATIVE_JOB = "3289913b17116604a52279a8dca2aba788ec173a2a9f89472605ba699960c477"
NATIVE_RESULT = "cb044d2a615d819e8ac642f3eea4bf5f313b8b61c5bd70570e7e3c90895a26f1"
SHARED = PureWindowsPath(r"\\Mac\Home\Documents\UniCAD\Oracle121Takeover\SdkNamedMaterial01")
SOURCE_NAME = "NativeSourcePacket03"
PACKET_NAME = "AppearanceGetterPacket01"
RAW_ROOT = PureWindowsPath(r"C:\KitAssignedAppearanceGetter01")
INSTALL = PureWindowsPath(r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS")
BUILD = "34.5.2.0604"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
MODULES = {
    "SLDWORKS.exe": ORACLE,
    "sldapiu.dll": "97bc3d859637c8b420108a1a3ebd4262580fa45d05c761874df7658fad49b6c2",
    "sldmatu.dll": "8a07d6b5d8d7d4f9f064b28e1d60f853fd754caa6d507db28b06031f287e051e",
    "sldvisualstateu.dll": "fb85d7921c52393e8bb847258b72d8cd006b37c118138c8260c6efe7dcc22c2c",
}
LIBRARIES = {
    "sldworks": "{83A33D31-27C5-11CE-BFD4-00400513BB57}",
    "swconst": "{4687F359-55D0-4CD3-B6CF-2EB42C11F989}",
}
MEMBERS = {
    "IModelDoc2": {("IsOpenedReadOnly", 1, 0)},
    "IBody2": {("MaterialPropertyValues2", 2, 0)},
    "IPartDoc": {("MaterialPropertyValues", 2, 0), ("GetBodies2", 1, 2)},
    "IConfiguration": {("GetDisplayStates", 1, 0), ("GetDisplayStatesCount", 1, 0)},
    "IModelDocExtension": {("GetRenderMaterials2", 1, 2)},
    "IRenderMaterial": {("GetEntities", 1, 0), ("GetMaterialIds", 1, 2),
                        ("PrimaryColor", 2, 0), ("Roughness", 2, 0), ("FileName", 2, 0)},
}
CASES = {
    "D01Author": ("D01Corner/Author", "Original.SLDPRT",
                  "6f3683065b2e401812a52c03e8c9913d8ea76ff82444dd975a174977f3b5740f"),
    "D02Swap": ("D02Center/Swap", "Swapped.SLDPRT",
                "e1c79ba4b22508f465ee624a6fe2b41f04f5efdf60012c0ef909cbed1195ec23"),
}
PHASES = ("ControlBefore", *CASES, "ControlAfter")
CONTROL_SHA = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
PACKET_TOOLS = ("AuthorCurves.py", "AuthorRectangleAnchors.py", "MaterialSourceFacts.py",
                "OracleIdentity.py", "Swapp.py")
SCRIPT = "ObserveAssignedAppearanceGetters.py"
ALL_TOOLS = {*PACKET_TOOLS, SCRIPT, "ObserveAssemblyLoad.py"}
SCHEMA = "kit.sw2026.assigned-appearance-getters.v1"
SLOTS = ("red", "green", "blue", "ambient", "diffuse", "specular", "shininess",
         "transparency", "emission")


class EvidenceFailure(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise EvidenceFailure(message)


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def checked(path, expected, size=None):
    require(path.is_file() and path.resolve(strict=True) == path and not path.is_symlink(),
            f"expected an unredirected regular input: {path.name}")
    require((size is None or path.stat().st_size == size) and digest(path) == expected,
            f"custody differs for {path.name}")
    return path


def native_authority(source):
    job = json.loads(checked(source / "Job.json", NATIVE_JOB).read_bytes())
    result = json.loads(checked(source / "Inspection" / "Result.json", NATIVE_RESULT).read_bytes())
    require(result["packet_sha256"] == NATIVE_JOB and result["cohort_role"] == "discovery"
            and result["passed"] and result["source_lifecycle_qualified"] and result["controls_healthy"]
            and result["distinct_native_processes"] == 10 and result["heldout_credit"] == 0
            and job["oracle_sha256"] == ORACLE and job["control_sha256"] == CONTROL_SHA,
            "the measured disclosed source batch does not match")
    return job, result


def verify(packet, job_pin, source):
    job = json.loads(checked(packet / "Job.json", job_pin).read_bytes())
    require(set(p.name for p in packet.iterdir()) == {"Job.json", "Tools"}
            and set(p.name for p in (packet / "Tools").iterdir()) == ALL_TOOLS,
            "frozen packet inventory differs")
    require(job["schema"] == SCHEMA and job["archive_revision"] == BASE and job["sdk_tree"] == SDK_TREE
            and job["archive_receipt_sha256"] == ARCHIVE_RECEIPT
            and job["native_source_job_sha256"] == NATIVE_JOB
            and job["native_source_result_sha256"] == NATIVE_RESULT
            and job["phases"] == list(PHASES) and set(job["cases"]) == set(CASES)
            and set(job["tools_sha256"]) == ALL_TOOLS and job["control"]["sha256"] == CONTROL_SHA,
            "wrong exact source or research packet")
    native_job, authority = native_authority(source)
    for name, wanted in job["tools_sha256"].items():
        if name in PACKET_TOOLS:
            require(wanted == native_job["tools_sha256"][name], "measured source tool changed")
        checked(packet / "Tools" / name, wanted)
    for name, (role, basename, expected) in CASES.items():
        entry = job["cases"][name]
        measured = authority["phases"][role]
        require(measured["passed"] and measured["file"]["sha256"] == entry["sha256"] == expected
                and measured["file"]["bytes"] == entry["bytes"]
                and measured["identity"]["sha256"] == ORACLE
                and entry["relative"] == f"Inspection/{role}/{basename}",
                "candidate differs from the measured disclosure")
        checked(source / entry["relative"], expected, entry["bytes"])
    checked(source / "Control.SLDPRT", CONTROL_SHA, job["control"]["bytes"])
    for role in ("ControlBefore", "ControlAfter"):
        control = authority["phases"][role]
        require(control["passed"] and control["oracle_identity"]["sha256"] == ORACLE
                and job["control"]["prior_record_sha256"][role] == control["record_sha256"],
                "previous control did not qualify")
    return job


def installed_api():
    import pythoncom
    from win32api import GetFileVersionInfo

    install = Path(INSTALL)
    for name, wanted in MODULES.items():
        file = checked(install / name, wanted)
        info = GetFileVersionInfo(str(file), "\\")
        high, low = info["FileVersionMS"], info["FileVersionLS"]
        require((high >> 16, high & 65535, low >> 16, low & 65535) == (34, 5, 2, 604),
                f"incorrect installed build for {name}")
    rows, selector = {}, None
    pythoncom.CoInitialize()
    try:
        for name, guid in LIBRARIES.items():
            library = pythoncom.LoadRegTypeLib(guid, 34, 0, 0)
            attributes = library.GetLibAttr()
            require(str(attributes[0]).casefold() == guid.casefold() and tuple(attributes[3:5]) == (34, 0),
                    "incorrect registered 2026 type library")
            for index in range(library.GetTypeInfoCount()):
                info = library.GetTypeInfo(index)
                owner = info.GetDocumentation(-1)[0]
                layout = info.GetTypeAttr()
                if name == "sldworks" and owner in MEMBERS:
                    observed = {}
                    for ordinal in range(layout.cFuncs):
                        entry = info.GetFuncDesc(ordinal)
                        names = info.GetNames(entry.memid)
                        if not names:
                            continue
                        spelling = (names[0], entry.invkind,
                                    len(names) - 1 if entry.invkind == 1 else len(entry.args))
                        if spelling in MEMBERS[owner]:
                            observed[spelling] = {
                                "name": names[0], "id": entry.memid, "kind": entry.invkind,
                                "params": list(names[1:]), "args": repr(entry.args), "result": repr(entry.rettype),
                            }
                    require(set(observed) == MEMBERS[owner], f"incomplete installed getter layout for {owner}")
                    rows[owner] = {"iid": str(layout[0]), "members": [observed[key] for key in sorted(observed)]}
                if name == "swconst" and owner == "swDisplayStateOpts_e":
                    for ordinal in range(layout.cVars):
                        entry = info.GetVarDesc(ordinal)
                        if info.GetNames(entry.memid)[0] == "swSpecifyDisplayState":
                            selector = entry.value
    finally:
        pythoncom.CoUninitialize()
    require(set(rows) == set(MEMBERS) and type(selector) is int and selector == 3,
            "incomplete documented 2026 getter contract")
    return {"build": BUILD, "modules": MODULES, "interfaces": rows, "selected_state": selector}


def array_value(author, owner, member):
    try:
        value = author.get(owner, member)
    except Exception as error:
        return {"shape": "getter_error", "error": repr(error)}
    if value is None:
        return {"shape": "null"}
    if not isinstance(value, (tuple, list)) or len(value) != len(SLOTS):
        return {"shape": "unexpected", "python_type": type(value).__name__}
    if all(type(x) in (float, int) and x == -1 for x in value):
        return {"shape": "all_minus_one", "values": list(value)}
    if not all(type(x) in (float, int) and isfinite(x) and 0 <= x <= 1 for x in value):
        return {"shape": "unexpected", "values": list(value)}
    return {"shape": "nine_values", "values": dict(zip(SLOTS, value, strict=True))}


def same_owner(sw, left, right):
    iid = sw.pythoncom.IID_IUnknown
    return left._oleobj_.QueryInterface(iid) == right._oleobj_.QueryInterface(iid)


def matches_color(rgb, archive):
    expected = {
        "model": [v / 255 for v in archive["model_rgb"]],
        "classic": [v / 255 for v in archive["classic_rgb"]],
        "pbr": archive["pbr_albedo_f10"],
    }
    return {branch: all(isclose(a, b, rel_tol=0, abs_tol=1e-6)
                        for a, b in zip(rgb, values, strict=True))
            for branch, values in expected.items()}


def scalar_close(actual, expected):
    return isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-12)


def appearance_match(legacy, appearance):
    if legacy["shape"] != "nine_values":
        return {"shape": legacy["shape"]}
    values = legacy["values"]
    return {"shape": "nine_values", "rgb": matches_color([values[k] for k in SLOTS[:3]], appearance),
            "transparency": scalar_close(values["transparency"], appearance["legacy_transparency_f58"])}


def render_rows(author, extension, model, part, body, selector, display, archive):
    sw = author.sw
    names = sw.VARIANT(sw.pythoncom.VT_ARRAY | sw.pythoncom.VT_BSTR, [display])
    native = author.get(extension, "GetRenderMaterials2", selector, names)
    require(native is None or isinstance(native, (tuple, list)),
            "selected-state renderer did not return a documented material array")
    rows = []
    for candidate in native or ():
        material = author.typed(candidate, "RenderMaterial")
        entities = author.get(material, "GetEntities")
        require(entities is None or isinstance(entities, (tuple, list)),
                "renderer did not return a documented owner array")
        owners = []
        for entity in entities or ():
            if entity is not None and (same_owner(sw, entity, model) or same_owner(sw, entity, part)):
                owners.append("part_self")
            elif entity is not None and same_owner(sw, entity, body):
                owners.append("sole_solid")
            else:
                owners.append("unresolved")
        first, second = sw.byref_long(), sw.byref_long()
        first.value = second.value = -1
        status = author.get(material, "GetMaterialIds", first, second)
        ids = [int(first.value), int(second.value)]
        require(ids != [-1, -1] and (status is None or type(status) in (int, bool)),
                "renderer did not expose the documented ID return")
        packed = author.get(material, "PrimaryColor")
        roughness = author.get(material, "Roughness")
        filename = author.get(material, "FileName")
        require(type(packed) is int and -(2 ** 31) <= packed < 2 ** 32 and type(roughness) in (float, int)
                and isfinite(roughness) and (filename is None or type(filename) is str),
                "unexpected renderer getter values")
        rgb = [(packed >> (8 * index)) & 255 for index in range(3)] if 0 <= packed <= 0xFFFFFF else None
        comparisons = {
            scope: {
                "rgb": None if rgb is None else matches_color([v / 255 for v in rgb], visual),
                "id": ids == visual["render_id_words"],
                "classic_roughness": scalar_close(roughness, visual["classic_roughness_f74"]),
                "pbr_roughness": scalar_close(roughness, visual["pbr_roughness_f2c"]),
                "exact_filename": (filename is not None
                                   and sha256(encode(filename)).hexdigest() == visual["classic_locator_sha256"]),
            }
            for scope, visual in archive.items()
        }
        rows.append({"owners": owners, "ids": ids, "get_ids_result": status, "colorref": packed,
                     "rgb": rgb, "roughness": roughness, "filename": filename, "comparison": comparisons})
    return rows


def part_sample(author, model, entry, selector, raw):
    from MaterialSourceFacts import material_identity, selected_mass

    sw = author.sw
    part = author.typed(model, "PartDoc")
    extension = author.typed(author.get(model, "Extension"), "ModelDocExtension")
    configuration = author.typed(author.get(author.get(model, "ConfigurationManager"),
                                            "ActiveConfiguration"), "Configuration")
    config_name = author.get(configuration, "Name")
    states = tuple(author.get(configuration, "GetDisplayStates") or ())
    raw.update(configuration=config_name, selected_states=list(states))
    require(config_name == entry["config"] and author.get(model, "GetConfigurationCount") == 1
            and author.get(configuration, "GetDisplayStatesCount") == len(states) == 1
            and states[0] == entry["display"], "the actual active configuration or selected display differs")
    raw["active_display"] = states[0]
    total = author.get(part, "GetBodies2", 0, False) or ()
    visible = author.get(part, "GetBodies2", 0, True) or ()
    require(len(total) == len(visible) == 1, "expected precisely one visible and total native solid")
    body = author.typed(total[0], "Body2")
    require(same_owner(sw, part, model) and same_owner(sw, body, visible[0])
            and author.get(body, "GetType") == 0 and author.get(body, "Name") == entry["body"],
            "actual part or sole visible solid ownership differs")
    raw["bound_part_and_solid"] = True
    document = array_value(author, part, "MaterialPropertyValues")
    solid = array_value(author, body, "MaterialPropertyValues2")
    raw["legacy"] = {"document": document, "body": solid}
    raw["legacy_comparison"] = {
        key: {scope: appearance_match(value, archived)
              for scope, archived in entry["archive"].items()}
        for key, value in raw["legacy"].items()
    }
    physical = raw["physical"] = {
        "part": material_identity(author, part, "GetMaterialPropertyName2", config_name),
        "body": material_identity(author, body, "GetMaterialPropertyName", config_name),
        "body_name": author.get(body, "Name"),
        "body_id_name": author.get(body, "GetMaterialIdName2"),
        "body_user_name": author.get(body, "GetMaterialUserName2"),
        "mass": selected_mass(author, body),
    }
    expected = entry["physical"]
    require(all(physical[k] == expected[k] for k in ("part", "body", "body_id_name", "body_user_name"))
            and all(scalar_close(physical["mass"][k], expected["mass"][k])
                    for k in ("density", "volume", "mass", "mass_over_volume_density")),
            "assigned physical material, body owner or selected-body SI mass differs")
    raw["physical_matches"] = True
    raw["renderer"] = render_rows(author, extension, model, part, body, selector, states[0], entry["archive"])
    active_after = author.get(author.get(model, "ConfigurationManager"), "ActiveConfiguration")
    require(same_owner(sw, configuration, active_after)
            and tuple(author.get(configuration, "GetDisplayStates") or ()) == states,
            "active configuration or display changed during observation")
    require(document["shape"] in {"nine_values", "all_minus_one", "null"}
            and solid["shape"] in {"nine_values", "all_minus_one", "null"},
            "legacy property getter did not yield a documented observable shape")


def control_sample(sw, model, expected, raw):
    raw.update(bodies=sw.bodies(model), whats_wrong=sw.rebuild_errors(model),
               mass=sw.mass(model), features=sw.features(model))
    features = raw["features"]
    require(raw["bodies"] == 1 and raw["whats_wrong"] == 0 and raw["mass"] is not None
            and [dict(name=row["name"], type=row["type"]) for row in features] == expected["features"]
            and all(row.get("error") == 0 and row.get("warning") is False and not row.get("error_query_error")
                    for row in features)
            and all(scalar_close(raw["mass"][k], expected["mass"][k]) for k in ("volume", "area", "mass"))
            and all(scalar_close(x, y) for x, y in zip(raw["mass"]["com"], expected["mass"]["com"], strict=True)),
            "licensed readonly control lost its native feature or geometry health")


def public_phase(raw, record_hash, expected):
    renderer = raw.get("renderer")
    return {
        "passed": raw["passed"], "record_sha256": record_hash, "save_calls": 0,
        "source_sha256": expected, "before_sha256": raw.get("before_sha256"),
        "after_sha256": raw.get("after_sha256"),
        "exact_open": raw.get("open_errors") == raw.get("open_warnings") == 0 and raw.get("same_file", False),
        "readonly": raw.get("read_only", False) and raw.get("read_only_after", False),
        "immutable": raw.get("before_sha256") == raw.get("after_sha256") == expected,
        "dialogs": len(raw.get("dialogs", ())),
        "cleanup_diagnostics": len(raw.get("controller_diagnostics", ())) + len(raw.get("cleanup_errors", ())),
        "active_scope_bound": "active_display" in raw,
        "part_and_solid_bound": raw.get("bound_part_and_solid", False),
        "physical_matches": raw.get("physical_matches", False),
        "legacy_comparison": raw.get("legacy_comparison"),
        "renderer": None if renderer is None else
        [{"owners": row["owners"], "has_filename": bool(row["filename"]), "comparison": row["comparison"]}
         for row in renderer],
        "failure_stage": raw.get("failure_stage"),
    }


def phase(role, source, job, job_pin, installed, output):
    import Swapp
    from AuthorCurves import CurveAuthor, Recorder
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    directory = output / role
    directory.mkdir()
    rec = Recorder(directory / "Record.json", {"phase": role, "job_sha256": job_pin})
    candidate = role in CASES
    entry = job["cases"][role] if candidate else job["control"]
    file = source / (entry["relative"] if candidate else "Control.SLDPRT")
    raw = {"passed": False, "save_calls": 0, "cleanup_errors": []}
    controller, model, observed = None, None, False
    stage = "custody"
    with AssemblyLoadMonitor() as monitor:
        try:
            checked(file, entry["sha256"], entry["bytes"])
            raw["before_sha256"] = digest(file)
            stage = "oracle"
            rec.call("require idle owned oracle", Swapp.sweep)
            controller = rec.call("start exact versioned oracle", Swapp.Sw)
            identity = raw["identity"] = rec.call("check actual process", application_identity, controller.app)
            require(identity["version_matches"] and identity["sha256"] == ORACLE
                    and identity["file_version"] == BUILD and identity["pe_machine"] == "0x8664"
                    and controller.revision == "34.5.2" and Swapp.PROGID == "SldWorks.Application.34",
                    "wrong exact current-user oracle")
            author = CurveAuthor(controller.app, rec, Swapp)
            require(author.get(controller.app, "GetDocumentCount") == 0, "oracle opened with a prior document")
            stage = "open"
            model, errors, warnings = rec.call("open native file read-only", controller.open, file, read_only=True)
            raw.update(open_errors=errors, open_warnings=warnings)
            require(model is not None and errors == warnings == 0, "unhealthy native open")
            raw["same_file"] = Path(author.get(model, "GetPathName")).samefile(file)
            raw["read_only"] = bool(author.get(model, "IsOpenedReadOnly"))
            require(raw["same_file"] and raw["read_only"] and author.get(model, "GetType") == 1,
                    "read-only native part identity differs")
            raw["dirty_before"] = bool(author.get(model, "GetSaveFlag"))
            stage = "candidate_getters" if candidate else "control_health"
            if candidate:
                author.model = model
                part_sample(author, model, entry, installed["selected_state"], raw)
            else:
                control_sample(Swapp, model, entry, raw)
            raw["read_only_after"] = bool(author.get(model, "IsOpenedReadOnly"))
            raw["dirty_after"] = bool(author.get(model, "GetSaveFlag"))
            require(raw["read_only_after"], "native read-only state changed")
            observed = True
        except Exception as error:
            raw["failure_stage"] = stage
            rec.failure(error)
        finally:
            if controller is not None:
                if model is not None:
                    try:
                        rec.call("discard-close readonly document", controller.close_doc, model)
                        require(Swapp.cv(controller.app, "GetDocumentCount") == 0, "native document remained open")
                    except Exception as error:
                        raw["cleanup_errors"].append(repr(error))
                try:
                    rec.call("retire fresh owned oracle", controller.close)
                except Exception as error:
                    raw["cleanup_errors"].append(repr(error))
                raw["controller_diagnostics"] = controller.diagnostics
    raw.update(dialogs=monitor.log, progress_windows=monitor.progress)
    try:
        raw["after_sha256"] = digest(file)
        require(raw.get("before_sha256") == raw["after_sha256"] == entry["sha256"]
                and file.stat().st_size == entry["bytes"], "native observation changed original custody")
        require(not Swapp.application_pids(), "oracle is still running after observation")
    except Exception as error:
        raw.setdefault("failure_stage", "retire_or_custody")
        raw["cleanup_errors"].append(repr(error))
    raw["passed"] = bool(observed and not raw["dialogs"] and not raw["cleanup_errors"]
                         and not raw.get("controller_diagnostics"))
    if not raw["passed"]:
        raw.setdefault("failure_stage", "retire_or_custody")
    rec.data.update(result=raw, passed=raw["passed"], finished_at=time.time())
    rec.flush()
    identity = raw.get("identity")
    lifetime = (identity["process_id"], identity["process_creation_filetime"]) if identity else None
    return public_phase(raw, digest(rec.path), entry["sha256"]), lifetime


def native_run(packet, job_pin):
    require(os.name == "nt" and sys.version_info[:2] == (3, 12) and struct.calcsize("P") == 8
            and sys.flags.ignore_environment and not sys.flags.isolated and sys.dont_write_bytecode,
            "run from the verified current-user Windows Python 3.12 using -E -B")
    require(packet == Path(SHARED / PACKET_NAME), "native side requires the exact shared packet locator")
    source = Path(SHARED / SOURCE_NAME)
    output = Path(RAW_ROOT)
    output.mkdir()
    require(output.resolve(strict=True) == output, "Windows-local raw output redirected")
    summary = {"schema": SCHEMA, "job_sha256": job_pin, "exact_build": BUILD, "passed": False,
               "installed_api_sha256": None, "controls_healthy": False, "distinct_native_processes": 0,
               "save_calls": 0, "heldout_credit": 0, "source_lifecycle_or_writer_credit": 0, "phases": {}}
    lifetimes = []
    with (output / "Observer.log").open("x", encoding="utf-8") as log, redirect_stdout(log), redirect_stderr(log):
        stage = "packet_verification"
        try:
            job = verify(packet, job_pin, source)
            stage = "installed_metadata"
            installed = installed_api()
            installed_path = output / "InstalledApi.json"
            installed_path.write_bytes(encode(installed))
            summary["installed_api_sha256"] = digest(installed_path)
            for role in PHASES:
                if role in CASES and not summary["phases"]["ControlBefore"]["passed"]:
                    continue
                stage = role
                summary["phases"][role], lifetime = phase(role, source, job, job_pin, installed, output)
                if lifetime is not None:
                    lifetimes.append(lifetime)
            stage = "final_custody"
            verify(packet, job_pin, source)
            summary["final_custody_verified"] = True
        except Exception:
            summary["failure_stage"] = stage
            traceback.print_exc()
    rows = summary["phases"]
    summary["distinct_native_processes"] = len(set(lifetimes))
    summary["controls_healthy"] = all(rows.get(role, {}).get("passed") is True
                                      for role in ("ControlBefore", "ControlAfter"))
    summary["passed"] = (summary.get("final_custody_verified") is True and set(rows) == set(PHASES)
                         and all(row["passed"] for row in rows.values())
                         and len(set(lifetimes)) == len(PHASES)
                         and sorted({lifetime[1] for lifetime in lifetimes}) == [lifetime[1] for lifetime in lifetimes])
    (output / "Result.json").write_bytes(encode(summary))
    print(encode(summary).decode(), end="")
    return 0 if summary["passed"] else 3


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("verify", "run"))
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    packet = Path(__file__).resolve(strict=True).parent.parent
    if args.mode == "run":
        if args.source is not None:
            parser.error("the native source locator is frozen")
        try:
            return native_run(packet, args.job_sha256)
        except Exception:
            print('{"passed":false,"failure_stage":"entry_or_packet_verification"}')
            return 3
    require(os.name != "nt" and args.source is not None, "host verification requires the disclosed source path only")
    verify(packet, args.job_sha256, args.source.resolve(strict=True))
    print(encode({"passed": True, "job_sha256": args.job_sha256, "disclosed_cases": len(CASES),
                  "native_processes_started": 0, "heldout_credit": 0}).decode(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
