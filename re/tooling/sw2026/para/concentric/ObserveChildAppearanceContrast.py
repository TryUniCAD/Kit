from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parent), str(HERE.parents[2])]

from ConcentricApiMetadata import LIBRARIES
from ConcentricNativeContract import ORACLE, checked, digest, require, signature, write_json

SCHEMA = "kit.sw2026.concentric-child-appearance-contrast.v1"
BUILD = "34.5.2.0604"
MODULES = {
    "sldworks.exe": ORACLE,
    "sldapiu.dll": "97bc3d859637c8b420108a1a3ebd4262580fa45d05c761874df7658fad49b6c2",
    "sldappu.dll": "50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf",
    "sldmfcu.dll": "af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735",
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    "sldvisualstateu.dll": "fb85d7921c52393e8bb847258b72d8cd006b37c118138c8260c6efe7dcc22c2c",
}
PHASES = ("ControlBefore", "AuthorA", "ReopenA", "AuthorB", "ReopenB", "ControlAfter")
MEMBERS = {
    "IModelDocExtension": {
        ("CreateRenderMaterial", 1, 1), ("AddDisplayStateSpecificRenderMaterial", 1, 5),
        ("GetRenderMaterials2", 1, 2),
    },
    "IRenderMaterial": {
        ("PrimaryColor", 2, 0), ("PrimaryColor", 4, 1), ("Roughness", 2, 0), ("Roughness", 4, 1),
        ("AddEntity", 1, 1), ("GetEntities", 1, 0), ("GetMaterialIds", 1, 2), ("FileName", 2, 0),
    },
    "IConfiguration": {("GetDisplayStates", 1, 0), ("GetDisplayStatesCount", 1, 0)},
    "IModelDoc2": {("Save3", 1, 3), ("IsOpenedReadOnly", 1, 0)},
}
RGB = (53, 137, 211)
ROUGHNESS = {"A": 0.3125, "B": 0.6875}
COLOR = sum(channel << (8 * index) for index, channel in enumerate(RGB))
PUBLISHED_STOCK_COLOR = 0xE5E5E5
AUTHORING_PROTOCOL = "set-primary-color-on-published-row-once"
PART_NAME = "DisclosedRadialSceneProbe.SLDPRT"


def metadata(executable):
    require(os.name == "nt", "the installed metadata phase belongs to the licensed Windows guest")
    import pythoncom
    from win32api import GetFileVersionInfo

    executable = checked(executable.resolve(strict=True), ORACLE)
    require(executable.name.casefold() == "sldworks.exe", "expected the actual installed SOLIDWORKS executable")
    install = executable.parent
    versions = GetFileVersionInfo(str(executable), "\\")
    high, low = versions["FileVersionMS"], versions["FileVersionLS"]
    require((high >> 16, high & 65535, low >> 16, low & 65535) == (34, 5, 2, 604), "wrong installed build")
    modules = {name: digest(checked(install / name, expected)) for name, expected in MODULES.items()}
    data_root = install / "data"
    asset = (data_root / "graphics/materials/color.p2m").resolve(strict=True)
    require(asset.is_file() and asset.is_relative_to(data_root.resolve(strict=True))
            and 0 < asset.stat().st_size <= 32 * 1024 * 1024, "unexpected installed asset locator or size")
    interfaces, libraries, selector = {}, {}, None
    pythoncom.CoInitialize()
    try:
        for family, guid in LIBRARIES.items():
            lib = pythoncom.LoadRegTypeLib(guid, 34, 0, 0)
            attributes = lib.GetLibAttr()
            require(tuple(attributes[3:5]) == (34, 0), "expected registered 2026 metadata")
            libraries[family] = str(attributes[0])
            for index in range(lib.GetTypeInfoCount()):
                info = lib.GetTypeInfo(index)
                name = info.GetDocumentation(-1)[0]
                attrs = info.GetTypeAttr()
                if family == "sldworks" and name in MEMBERS:
                    seen = []
                    for number in range(attrs.cFuncs):
                        entry = info.GetFuncDesc(number)
                        names = list(info.GetNames(entry.memid))
                        if names and any(row[0].casefold() == names[0].casefold() for row in MEMBERS[name]):
                            seen.append({"name": names[0], "kind": entry.invkind,
                                         "count": len(names) - 1 if entry.invkind == 1 else len(entry.args),
                                         "names": names, "id": entry.memid, "args": repr(entry.args), "result": repr(entry.rettype)})
                    interfaces[name] = {"iid": str(attrs[0]), "members": seen}
                if family == "swconst" and name == "swDisplayStateOpts_e":
                    for ordinal in range(attrs.cVars):
                        entry = info.GetVarDesc(ordinal)
                        if info.GetNames(entry.memid)[0] == "swSpecifyDisplayState":
                            selector = entry.value
    finally:
        pythoncom.CoUninitialize()
    require(set(interfaces) == set(MEMBERS) and type(selector) is int and selector == 3,
            "required registered API family or documented specific-state selector is missing")
    for name, wanted in MEMBERS.items():
        actual = {(row["name"].casefold(), row["kind"], row["count"]) for row in interfaces[name]["members"]}
        require({(member.casefold(), kind, count) for member, kind, count in wanted} <= actual,
                f"registered invocation differs for {name}: {sorted(actual)}")
    return {"schema": SCHEMA, "build": BUILD, "oracle": str(executable), "modules": modules,
            "asset": {"path": str(asset), "sha256": digest(asset), "bytes": asset.stat().st_size, "data_root": str(data_root)},
            "interfaces": interfaces, "libraries": libraries, "specified_state_selector": selector,
            "runtime": {"executable": sys.executable, "version": ".".join(map(str, sys.version_info[:3])),
                        "pointer_bits": struct.calcsize("P") * 8}, "native_processes_started": 0}


def verify(packet, expected):
    require(os.name == "nt", "native phase belongs exclusively to the Windows operator")
    packet = checked(packet, expected).resolve(strict=True)
    root = packet.parent
    job = json.loads(packet.read_bytes())
    require(job["schema"] == SCHEMA and job["phases"] == list(PHASES)
            and packet.name == "Trial.json" and root == Path(job["guest_root"])
            and HERE == root / "Tools" / HERE.name
            and job["part_name"] == PART_NAME
            and job["authoring_protocol"] == AUTHORING_PROTOCOL
            and job["rgb"] == list(RGB) and job["roughness"] == ROUGHNESS and job["heldout_inputs_read"] is False,
            "wrong disclosed appearance packet")
    for relative, wanted in job["files_sha256"].items():
        path = root / relative
        require(path.resolve(strict=True) == path and path.is_relative_to(root), "frozen input escaped its packet")
        checked(path, wanted)
    data = job["installed"]
    runtime = data["runtime"]
    require(Path(sys.executable).samefile(runtime["executable"])
            and tuple(sys.version_info[:3]) == tuple(map(int, runtime["version"].split(".")))
            and struct.calcsize("P") * 8 == runtime["pointer_bits"] == 64, "wrong pinned guest runtime")
    for name, wanted in MODULES.items():
        checked(Path(data["oracle"]).parent / name, wanted)
    asset = checked(Path(data["asset"]["path"]), data["asset"]["sha256"])
    require(asset.stat().st_size == data["asset"]["bytes"], "installed asset size changed")
    for row in job["controls"].values():
        checked(Path(row["guest_path"]), row["sha256"])
    working_dir = root / "Working"
    require(working_dir.resolve(strict=True) == working_dir and working_dir.is_dir()
            and not working_dir.is_symlink() and not working_dir.is_junction(), "working directory redirected")
    working = working_dir / PART_NAME
    require(working.resolve(strict=True) == working and working.is_file() and not working.is_symlink(), "working part redirected")
    return root, job, asset, working


def phase_record(root, expected, role):
    path = root / "Inspection" / role / "Record.json"
    if not path.is_file():
        return None
    row = json.loads(path.read_bytes())
    require(row["job"] == {"trial_sha256": expected, "phase": role}, "phase receipt belongs to another trial")
    return row["result"]


def predecessor(root, expected, role):
    row = phase_record(root, expected, role)
    require(row is not None and row["passed"], f"{role} did not pass")
    return row


def material_ids(author, material):
    first, second = (author.sw.byref_long() for _ in range(2))
    first.value = second.value = -1
    status = author.get(material, "GetMaterialIds", first, second)
    ids = (int(first.value), int(second.value))
    require(ids != (-1, -1), "material did not return its allocated ID pair")
    return ids, None if status is None else bool(status)


def same_identity(author, first, second):
    iid = author.sw.pythoncom.IID_IUnknown
    return first._oleobj_.QueryInterface(iid) == second._oleobj_.QueryInterface(iid)


def render_values(author, material):
    return {"primary_color": int(author.get(material, "PrimaryColor")), "roughness": float(author.get(material, "Roughness"))}


def observed_material(author, material, model, asset, data_root):
    values = render_values(author, material)
    entities = tuple(author.get(material, "GetEntities") or ())
    require(len(entities) == 1, "render material does not have precisely one self owner")
    owner = author.typed(entities[0], "ModelDoc2")
    require(same_identity(author, owner, model)
            and int(author.get(owner, "GetType")) == 1
            and Path(author.get(owner, "GetPathName")).samefile(author.get(model, "GetPathName")),
            "render material selected a different COM document, component or body")
    filename = str(author.get(material, "FileName"))
    prefix = "<SystemTexture>"
    actual = Path(data_root) / filename[len(prefix):].lstrip("\\/") if filename.startswith(prefix) else Path(filename)
    require(actual.samefile(asset), "render material does not resolve to the pinned installed asset")
    ids, status = material_ids(author, material)
    return {"ids": list(ids), "get_ids_result": status, "same_model_iunknown": True, "entity_count": 1,
            "filename": filename, "asset_sha256": digest(asset)} | values


def acquire_material(author, extension, model, selector, names, asset, data_root):
    rows = tuple(author.get(extension, "GetRenderMaterials2", selector, names) or ())
    require(len(rows) == 1, "bounded probe requires one actual current-state render material")
    material = author.typed(rows[0], "RenderMaterial")
    return material, observed_material(author, material, model, asset, data_root)


def require_intent(evidence, color, roughness, stage):
    require((evidence["primary_color"], evidence["roughness"]) == (color, roughness),
            f"{stage} did not retain the bound colour and roughness: {evidence['primary_color']}, {evidence['roughness']}")


def appearance(author, model, asset, job, roughness, editing, checkpoints, stage):
    sw = author.sw
    extension = author.typed(author.get(model, "Extension"), "ModelDocExtension")
    manager = author.typed(author.get(model, "ConfigurationManager"), "ConfigurationManager")
    config = author.typed(author.get(manager, "ActiveConfiguration"), "Configuration")
    display, = tuple(author.get(config, "GetDisplayStates") or ())
    require(int(author.get(config, "GetDisplayStatesCount")) == 1 and display, "expected one actual active display state")
    selector = job["installed"]["specified_state_selector"]
    names = sw.VARIANT(sw.pythoncom.VT_ARRAY | sw.pythoncom.VT_BSTR, [display])
    data_root = job["installed"]["asset"]["data_root"]
    selected = {"configuration": str(author.get(config, "Name")), "display_state": str(display)}
    if editing:
        creator = author.typed(author.get(extension, "CreateRenderMaterial", str(asset)), "RenderMaterial")
        author.set(creator, "PrimaryColor", COLOR)
        author.set(creator, "Roughness", roughness)
        checkpoints["creator_requested"] = render_values(author, creator)
        require(author.get(creator, "AddEntity", model) is True, "the native render API refused its part-scope entity")
        checkpoints["creator_after_attach"] = render_values(author, creator)
        first, second = (sw.byref_long() for _ in range(2))
        first.value = second.value = -1
        require(author.get(extension, "AddDisplayStateSpecificRenderMaterial", creator, selector, names, first, second) is True,
                "the native render API did not publish its selected state material")
        published = [int(first.value), int(second.value)]
        require(published != [-1, -1], "published material lacks its explicit ID pair")
        checkpoints["creator_after_publication"] = render_values(author, creator) | {"published_ids": published}
        target, prior = acquire_material(author, extension, model, selector, names, asset, data_root)
        checkpoints["published_before_set"] = prior | selected | {"same_creator_iunknown": same_identity(author, target, creator)}
        require(prior["ids"] == published, "actual selected-state material does not own the published IDs")
        require_intent(prior, PUBLISHED_STOCK_COLOR, roughness, "published pre-set contrast")
        author.rec.call("set published PrimaryColor once", setattr, target, "PrimaryColor", COLOR, parameters={"value": COLOR})
        direct = observed_material(author, target, model, asset, data_root) | selected
        checkpoints["published_set_direct"] = direct
        successor, observed = acquire_material(author, extension, model, selector, names, asset, data_root)
        checkpoints[stage] = observed | selected | {"same_published_iunknown": same_identity(author, successor, target)}
        require(direct["ids"] == published, "direct setter readback changed its actual material ID pair")
        require_intent(direct, COLOR, roughness, "direct published setter")
    else:
        published = None
        _, observed = acquire_material(author, extension, model, selector, names, asset, data_root)
        checkpoints[stage] = observed | selected
    require(published is None or published == observed["ids"], "the published material and selected state returned different IDs")
    require_intent(observed, COLOR, roughness, stage)
    return observed | selected | {"published_ids": published}


def appearance_signature(row):
    return {key: row[key] for key in ('ids', 'same_model_iunknown', 'entity_count', 'asset_sha256',
                                     'primary_color', 'roughness', 'configuration', 'display_state')}


def phase(packet, expected, role):
    root, job, asset, working = verify(packet, expected)
    control = role.startswith("Control")
    editing = role.startswith("Author")
    lane = role[-1]
    if control:
        target = Path(job["controls"]["parent"]["guest_path"])
    else:
        predecessor(root, expected, "ControlBefore")
        if lane == "B":
            predecessor(root, expected, "ReopenA")
            reset = check_reset(root, expected)
            require(reset["before"] == predecessor(root, expected, "AuthorA")["saved_sha256"]
                    and reset["after"] == job["baseline_sha256"], "second arm selector disagrees with the exact original")
        expected_source = job["baseline_sha256"] if editing else predecessor(root, expected, "Author" + lane)["saved_sha256"]
        target = checked(working, expected_source)
    import InspectCircleSketch as circle
    import ObserveRadialScene as radial
    import Swapp
    from AuthorCurves import CurveAuthor, Recorder
    from InspectGeneratedConcentric import capture, same_file
    from ObserveAssemblyLoad import AssemblyLoadMonitor
    from OracleIdentity import application_identity

    directory = root / "Inspection" / role
    directory.mkdir(exist_ok=False)
    rec = Recorder(directory / "Record.json", {"trial_sha256": expected, "phase": role})
    result = {"role": role, "passed": False, "save_count": 0}
    controller = None
    with AssemblyLoadMonitor() as monitor:
        try:
            rec.call("require idle owned oracle", Swapp.sweep)
            controller = rec.call("start clean exact oracle", Swapp.Sw)
            identity = rec.call("read actual oracle build", application_identity, controller.app)
            require(identity["file_version"] == BUILD and identity["version_matches"] and identity["sha256"] == ORACLE,
                    "unexpected CAD process")
            result["oracle_identity"] = identity
            author = CurveAuthor(controller.app, rec, Swapp)
            require(int(author.get(controller.app, "GetDocumentCount")) == 0, "cold oracle already has a document")
            if control:
                require(bool(author.get(controller.app, "GetUserPreferenceToggle", 18)), "control has unexpected ordinary link policy")
            model, errors, warnings = rec.call("open exact custody-bound input", controller.open, target, read_only=not editing)
            result.update(open_errors=errors, open_warnings=warnings)
            require(model is not None and errors == warnings == 0 and same_file(author.get(model, "GetPathName"), target),
                    "native open failed, warned or selected another file")
            require(bool(author.get(model, "IsOpenedReadOnly")) is not editing, "document write mode differs from its custody role")
            if control:
                assembly = author.typed(model, "AssemblyDoc")
                child = Path(job["controls"]["child"]["guest_path"])
                result["initial"], _ = capture(author, model, assembly, child, job["prediction_control"], False)
                require(bool(author.get(model, "ForceRebuild3", False)), "control rebuild failed")
                result["rebuilt"], _ = capture(author, model, assembly, child, job["prediction_control"], False)
                require(signature(result["initial"]) == signature(result["rebuilt"]), "control tree or ownership changed")
            else:
                author.model = model
                result["initial"] = circle.initial_state(author, job["radial"]["case"])
                require(result["initial"]["passed"], "initial part lacks its body and requested feature owners")
                if editing:
                    result["geometry"] = radial.capture(author, job["radial"], 1.0)
                checkpoints = result["appearance_checkpoints"] = {}
                initial_stage = "reacquired_after_set" if editing else "cold_reopen"
                result["appearance"] = appearance(author, model, asset, job, ROUGHNESS[lane], editing, checkpoints, initial_stage)
                result["rebuild_geometry"] = radial.capture(author, job["radial"], 1.0)
                refreshed = appearance(author, model, asset, job, ROUGHNESS[lane], False, checkpoints, "rebuilt_reacquired")
                result["rebuilt_appearance"] = refreshed
                require(appearance_signature(refreshed) == appearance_signature(result["appearance"]),
                        "appearance changed on rebuild")
                if editing:
                    require(result["rebuild_geometry"]["tree"] == result["geometry"]["tree"], "appearance changed the actual feature tree")
                    err, warn = (Swapp.byref_long() for _ in range(2))
                    status = author.get(model, "Save3", Swapp.SAVE_SILENT, err, warn)
                    result["save_status"] = [bool(status), int(err.value), int(warn.value)]
                    require(result["save_status"] == [True, 0, 0], "owned native save failed or warned")
                    result["save_count"] = 1
                else:
                    prior = predecessor(root, expected, "Author" + lane)
                    require(prior["rebuild_geometry"]["tree"] == result["rebuild_geometry"]["tree"]
                            and appearance_signature(prior["rebuilt_appearance"]) == appearance_signature(result["appearance"]),
                            "fresh reopen did not retain the authored source intent")
            result["passed"] = True
        except Exception as error:
            rec.failure(error)
        finally:
            if controller is not None:
                try:
                    controller.close()
                    result["controller_diagnostics"] = controller.diagnostics
                except Exception as error:
                    rec.failure(error, cleanup=True)
    try:
        verify(packet, expected)
        if not control:
            actual = digest(working)
            result["working_sha256"] = actual
            if editing and result["save_count"] == 1:
                require(actual != job["baseline_sha256"], "native save did not change the owned derivative")
                snapshot = directory / working.name
                with snapshot.open("xb") as stream:
                    stream.write(working.read_bytes())
                require(digest(snapshot) == actual, "immutable saved snapshot does not match the owned derivative")
                result["saved_sha256"] = actual
            else:
                require(actual == expected_source, "phase without a clean native save changed its exact input")
    except Exception as error:
        rec.failure(error, cleanup=True)
    result.update(dialogs=monitor.log, numeric_checks=len(rec.data["checks"]), first_failure=rec.data["first_failure"])
    result["passed"] = bool(result["passed"] and not result["dialogs"] and not result["first_failure"]
                            and not result.get("controller_diagnostics"))
    rec.data.update(result=result, passed=result["passed"])
    rec.flush()
    return result["passed"]


def check_reset(root, expected):
    reset = json.loads((root / "ResetB.json").read_bytes())
    require(reset["trial_sha256"] == expected and reset["after"] != reset["before"], "same-locator selector evidence differs")
    return reset


def reset_b(packet, expected):
    root, job, _, working = verify(packet, expected)
    prior = predecessor(root, expected, "AuthorA")
    predecessor(root, expected, "ReopenA")
    record = root / "ResetB.json"
    require(not record.exists() and not (root / "Inspection" / "AuthorB").exists(), "second arm already started")
    import Swapp

    Swapp.sweep()
    before = checked(working, prior["saved_sha256"])
    checked(root / "Inspection" / "AuthorA" / working.name, prior["saved_sha256"])
    source = checked(root / "Frozen" / working.name, job["baseline_sha256"])
    temporary = root / "Working" / (working.name + ".reset")
    with temporary.open("xb") as stream:
        stream.write(source.read_bytes())
    checked(temporary, job["baseline_sha256"])
    os.replace(temporary, before)
    checked(working, job["baseline_sha256"])
    write_json(record, {"trial_sha256": expected, "before": prior["saved_sha256"],
                        "after": job["baseline_sha256"], "native_processes_started": 0})


def summary(packet, expected):
    root, job, _, _ = verify(packet, expected)
    rows = {role: phase_record(root, expected, role) for role in PHASES}
    controls = rows[PHASES[0]], rows[PHASES[-1]]
    healthy = all(row and row["passed"] for row in controls)
    if healthy:
        healthy = signature(controls[0]["rebuilt"]) == signature(controls[1]["rebuilt"])
    births = [row["oracle_identity"]["process_creation_filetime"] for row in rows.values()
              if row and "oracle_identity" in row]
    passed = (healthy and all(row and row["passed"] for row in rows.values()) and len(births) == len(PHASES)
              and all(first < second for first, second in zip(births, births[1:])))
    if passed:
        reset = check_reset(root, expected)
        require(reset["before"] == rows["AuthorA"]["saved_sha256"] and reset["after"] == job["baseline_sha256"],
                "same-locator trial did not restore the identical source")
    write_json(root / "Result.json", {"schema": SCHEMA, "trial_sha256": expected, "passed": passed,
                                       "controls_healthy": healthy, "native_processes": len(set(births)),
                                       "source_evidence_only": True, "heldout_credit": 0, "phases": rows})
    return passed


def main():
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    probe = commands.add_parser("metadata")
    probe.add_argument("installed_executable", type=Path)
    probe.add_argument("output", type=Path)
    for name in ("verify", "phase", "reset-b", "summary"):
        mode = commands.add_parser(name)
        mode.add_argument("packet", type=Path)
        mode.add_argument("sha256")
        if name == "phase":
            mode.add_argument("role", choices=PHASES)
    args = parser.parse_args()
    if args.command == "metadata":
        value = metadata(args.installed_executable)
        require(not args.output.exists(), "reuse of a metadata receipt is forbidden")
        write_json(args.output, value)
        print(json.dumps({"metadata_sha256": digest(args.output), "asset": value["asset"], "native_processes_started": 0}))
        return 0
    if args.command == "verify":
        _, job, asset, _ = verify(args.packet, args.sha256)
        require(metadata(Path(job["installed"]["oracle"])) == job["installed"], "registered API or asset changed after freeze")
        return 0
    if args.command == "reset-b":
        reset_b(args.packet, args.sha256)
        return 0
    if args.command == "phase":
        return int(not phase(args.packet, args.sha256, args.role))
    return int(not summary(args.packet, args.sha256))


if __name__ == "__main__":
    raise SystemExit(main())
