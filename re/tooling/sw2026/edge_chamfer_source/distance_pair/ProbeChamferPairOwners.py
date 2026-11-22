from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output, run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(HERE.parent.parent), str(HERE.parent.parent.parent / "materials")]

from AuditTypedChamfer import NAMES, digest, expected_inputs, guard_runtime, inspect, registry, require
from MaterialPe import PeImage

IMAGE_SHA = "aa3fa88eeb5349c8ac2161ce9b3f18ab4e23417598c6b57719c88d5d6c178da9"
REA_IDENTITY = "ev_0abc627ded68a778913137169a7778a9c5d8a4de5eadea4cd58a3cc4d440aa32"
REA_SERIALIZER = "ev_7cb8c3657c99eaaa67c46ce501bcee9ddfeedbdd86c1cd9af82b26979601a7e7"
SLOTS = ("f810", "f818", "f820", "f828", "f830", "f838")
DISPLAY = "moDisplayDistanceDim_c"
SLOT_SHAPES = {
    1: (DISPLAY, "moDisplayAngularDim_c", None, None, None, None),
    2: (DISPLAY, None, DISPLAY, None, None, None),
    0x12: (DISPLAY, None, None, None, None, None),
}
RANGES = {
    "edge_constructor": (0x18023E400, 0x18023E69F),
    "mode_getter": (0x180244E00, 0x180244E0A),
    "equality_getter": (0x180248890, 0x18024889D),
    "mode_setter": (0x18024D210, 0x18024D222),
    "equality_setter": (0x18024D370, 0x18024D38F),
    "second_display_exposure": (0x180244E10, 0x180244ED0),
    "width_getter": (0x180245D40, 0x180245D61),
    "other_distance_getter": (0x180244F30, 0x180244F51),
    "cleanup": (0x1802400F0, 0x180240243),
    "current_mode_load": (0x18023F0C4, 0x18023F104),
}


def class_name(node):
    return None if node is None else node.ClassValue.NameValue


def display_slots(feature):
    fields = feature.FieldsValue
    require(feature.ClassValue.NameValue == "Chamfer_c" and feature.ClassValue.SchemaValue == 1
            and fields["f8a0"] == 10 and type(fields["f8c0"]) is int and fields["f8c0"] in SLOT_SHAPES,
            "chamfer is outside the exact ordinary edge archive mode boundary")
    actual = tuple(class_name(fields[key]) for key in SLOTS)
    require(actual == SLOT_SHAPES[fields["f8c0"]],
            "runtime mode and typed display slots do not describe the same ordinary edge chamfer")
    owned = [fields[key] for key in SLOTS if fields[key] is not None]
    require(len({id(row) for row in owned}) == len(owned), "chamfer display roots repeat an actual owner")
    return dict(zip(SLOTS, actual, strict=True))


def selected_export(exports, prefix, address):
    rows = [row for row in exports if row["name"].startswith(prefix)]
    require(len(rows) == 1 and rows[0]["forwarder"] is None and int(rows[0]["address"], 16) == address,
            "installed chamfer export or entry address differs")
    return {"name": prefix, "address": hex(address)}


def binary_proof(path, objdump):
    path = path.resolve(strict=True)
    require(not path.is_relative_to(ROOT) and path.name.casefold() == "sldmopartu.dll",
            "use the exact installed module outside the checkout")
    image = PeImage(path)
    require(image.sha256 == IMAGE_SHA and len(image.data) == 6836824 and image.u16(image.pe + 4) == 0x8664,
            "the installed SP05.2 module identity changed")
    exports = image.exports()
    observed = [selected_export(exports, prefix, RANGES[name][0]) for name, prefix in (
        ("edge_constructor", "??0Chamfer_c@@QEAA@PEAVmoModel_c@@NNHHH"),
        ("mode_getter", "?getChamferType@Chamfer_c@@"),
        ("equality_getter", "?isEqualDist@Chamfer_c@@"),
        ("mode_setter", "?setChamferType@Chamfer_c@@"),
        ("equality_setter", "?setEqualDist@Chamfer_c@@"),
        ("width_getter", "?getWidth@Chamfer_c@@"),
        ("other_distance_getter", "?getDist@Chamfer_c@@"),
        ("cleanup", "?cleanupDims@Chamfer_c@@"),
    )]
    imports = image.imports()
    bindings = {hex(key): imports[key] for key in (0x1803E7EF0, 0x1803E7F10, 0x1803E4B70, 0x1803E4B88, 0x1803EC690)}
    require("moDisplayDistanceDim_c" in bindings["0x1803e7ef0"]["name"]
            and "ParallelPlaneDistanceDim_c" in bindings["0x1803e7f10"]["name"]
            and "AngleDim_c" in bindings["0x1803e4b70"]["name"]
            and "moDisplayAngularDim_c" in bindings["0x1803e4b88"]["name"]
            and "su_CArchive" in bindings["0x1803ec690"]["name"], "installed display imports differ")
    owners = []
    observed_text = {}
    for name, (start, end) in RANGES.items():
        text = check_output((objdump, "-d", "--no-show-raw-insn", "--x86-asm-syntax=intel",
                             f"--start-address={hex(start)}", f"--stop-address={hex(end)}", str(path)), text=True)
        observed_text[name] = {line.split(":", 1)[0]: " ".join(line.split(":", 1)[1].split())
                               for line in text.splitlines() if line.startswith("180") and ":" in line}
        owners.append(image.pin(name, start, end))

    def check(role, anchors):
        instructions = observed_text[role]
        for address, instruction in anchors.items():
            require(instructions.get(address, "").startswith(instruction), "installed chamfer operation differs")

    check("mode_getter", {"180244e00": "mov eax, dword ptr [rcx + 0x8c0]", "180244e06": "and eax, 0xf"})
    check("equality_getter", {"180248890": "mov eax, dword ptr [rcx + 0x8c0]",
                              "180248896": "shr eax, 0x4", "180248899": "and eax, 0x1"})
    check("edge_constructor", {"18023e48b": "mov dword ptr [rsp + 0x28], 0x1",
           "18023e4af": "mov qword ptr [rbx + 0x810], rax", "18023e4cb": "mov dword ptr [rbx + 0x8c0], eax",
           "18023e4d9": "cmp eax, 0x1", "18023e504": "mov dword ptr [rsp + 0x28], 0x2",
           "18023e528": "mov qword ptr [rbx + 0x818], rax", "18023e539": "cmp eax, 0x2",
           "18023e541": "call 0x180248890", "18023e548": "jne 0x18023e59b",
           "18023e570": "mov dword ptr [rsp + 0x28], 0x3", "18023e594": "mov qword ptr [rbx + 0x820], rax",
           "18023e5e9": "mov dword ptr [rbx + 0x8a0], 0xa"})
    check("width_getter", {"180245d40": "mov rcx, qword ptr [rcx + 0x810]"})
    check("other_distance_getter", {"180244f30": "mov rcx, qword ptr [rcx + 0x820]"})
    check("second_display_exposure", {"180244e4d": "cmp eax, 0x2", "180244e55": "call 0x180248890",
           "180244e5c": "jne 0x180244e67", "180244e5e": "mov rdx, qword ptr [rbx + 0x820]",
           "180244eb0": "mov rdx, qword ptr [rbx + 0x810]"})
    check("cleanup", {"180240182": "cmp eax, 0x2", "1802401a1": "mov qword ptr [rbx + 0x818], rdi",
           "1802401a8": "call 0x180248890", "1802401af": "je 0x1802401de",
           "1802401d7": "mov qword ptr [rbx + 0x820], rdi"})
    check("current_mode_load", {"18023f0ce": "cmp eax, 0x2c7",
           "18023f0e9": "mov dword ptr [rdi + 0x8c0], eax"})
    return {"image_sha256": image.sha256, "image_bytes": len(image.data), "machine": "x64",
            "rea_resource_identity": REA_IDENTITY, "rea_known_serializer": REA_SERIALIZER,
            "exports": observed, "imports": bindings, "original_ranges": owners,
            "native_mode_mask": 15, "equal_distance_bit": 16, "ordinary_flags_byte": 10,
            "expected_type_2_rows": {"equal": [18, ["f810"]], "independent": [2, ["f810", "f820"]]},
            "constructor_ordinals": {"f810": 1, "f818": 2, "f820": 3}}


def disclosed_worker(folder, name, edited):
    from AuditTypedChamfer import ReadChmfOwn, ReadNativeLink, SldprtArchive

    data, case, branch, phase = expected_inputs(folder, name, edited)
    schemas = registry()
    banned = guard_runtime()
    proof = inspect(data, case, branch, edited, phase, schemas)
    link = ReadNativeLink(SldprtArchive.from_bytes(data), 0, ReadChamfers=True)
    feature = ReadChmfOwn(link).FeatureValue
    slots = display_slots(feature)
    require(feature.FieldsValue["f8c0"] == 1 and proof["exact_linked_replay"] and not banned,
            "disclosed contrast lost the existing linked angle-distance ownership")
    return {"case": name, "edited": edited, "source_sha256": digest(data), "mode_word": 1,
            "flags_byte": feature.FieldsValue["f8a0"], "display_slots": slots,
            "actual_driver_names": [row["name"] for row in proof["drivers"]],
            "exact_linked_replay": True, "external_accesses": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", required=True, type=Path)
    parser.add_argument("--image", type=Path)
    parser.add_argument("--objdump", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--case", choices=NAMES)
    parser.add_argument("--edited", action="store_true")
    args = parser.parse_args()
    if args.case:
        print(json.dumps(disclosed_worker(args.disclosed, args.case, args.edited), sort_keys=True))
        return
    require(args.image and args.objdump and args.report and not args.report.exists(), "incomplete evidence request")
    static = binary_proof(args.image, args.objdump)
    sources = []
    for name in NAMES:
        for edited in (False, True):
            command = [sys.executable, "-I", "-B", str(HERE), "--disclosed", str(args.disclosed), "--case", name]
            if edited:
                command.append("--edited")
            process = run(command, capture_output=True, timeout=90, check=False)
            require(process.returncode == 0 and not process.stderr, process.stderr.decode())
            sources.append(json.loads(process.stdout))
    receipt = {"schema": "kit.sw2026.distance-pair-chamfer-boundary.v1", "build": "34.5.2.0604",
               "installed": static, "disclosed_angle_distance": sources, "observed_distance_pair_files": 0,
               "native_processes": 0, "guarded_source_processes": len(sources)}
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main()
