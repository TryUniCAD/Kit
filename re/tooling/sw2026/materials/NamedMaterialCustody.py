from hashlib import sha256
from json import loads


LIFECYCLE_SHA = "cb044d2a615d819e8ac642f3eea4bf5f313b8b61c5bd70570e7e3c90895a26f1"
DIAGNOSTIC_SHA = "a23e44a29967ad84e2716f66363c2898025460bd5a9dddf266e575bdac3a88d2"
CONTROL_SHA = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"
SAVES = {"Author": "Original.SLDPRT", "Swap": "Swapped.SLDPRT", "Depth": "DepthEdit.SLDPRT"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def checked(root, relative, expected):
    path = root / relative
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root),
            "named material asset escaped the disclosed packet")
    data = path.read_bytes()
    require(digest(data) == expected, f"source hash changed at {relative}")
    return data


def disclosed_sources(root):
    require(root.name == "SdkNamedMaterial01" and root.is_dir() and not root.is_symlink(),
            "expected the exact prior disclosed material packet")
    root = root.resolve()
    source_path = "NativeSourcePacket03/Inspection"
    discovery_path = "NativeDensityProbe01/Native"
    source = loads(checked(root, source_path + "/Result.json", LIFECYCLE_SHA))
    diagnostic = loads(checked(root, discovery_path + "/Result.json", DIAGNOSTIC_SHA))
    require(source["passed"] and source["controls_healthy"] and source["distinct_native_processes"] == 10
            and diagnostic["complete_observations"] and diagnostic["controls_healthy"],
            "prior licensed material or control observations changed")
    for design in ("D01Corner", "D02Center"):
        for phase, basename in SAVES.items():
            role = f"{design}/{phase}"
            item = source["phases"][role]
            require(item["passed"] and item["file"]["diagnostics"] == [True, 0, 0],
                    "disclosed source did not save cleanly")
            state = item["states"]["after_save"]
            physical = state["mass"]
            require(physical["use_system_units"], "part density was not measured in SI")
            data = checked(root, f"{source_path}/{role}/{basename}", item["file"]["sha256"])
            require(len(data) == item["file"]["bytes"], "native save size changed")
            yield role, data, state["part_material"] | {
                "density_kg_m3": physical["density"], "configuration_name": state["configuration"],
            }
    item = diagnostic["rows"]["Author"]
    state = item["states"]["saved"]
    physical = state["selected_mass_property2"]
    require(item["file"]["diagnostics"] == [True, 0, 0] and physical["use_system_units"],
            "prior disclosed diagnostic lost physical custody")
    data = checked(root, discovery_path + "/AssignedDensityProbe.SLDPRT", item["file"]["sha256"])
    require(len(data) == item["file"]["bytes"], "native diagnostic save size changed")
    yield "Diagnostic", data, state["part_material"] | {
        "density_kg_m3": physical["density"], "configuration_name": "Default",
    }
    yield "Control", checked(root, "NativeSourcePacket03/Control.SLDPRT", CONTROL_SHA), None
