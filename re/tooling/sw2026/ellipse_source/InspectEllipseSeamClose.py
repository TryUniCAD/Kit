import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "materials"))
from MaterialPe import PeImage

IMAGES = {
    "sldappu.dll": "50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf",
    "sldapiu.dll": "97bc3d859637c8b420108a1a3ebd4262580fa45d05c761874df7658fad49b6c2",
    "slduiu.dll": "025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7",
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
}
NATIVE = {
    "sketch": "6e519f5c06d15c56ee3bde95fdb0485bc5dd1170853d25fa9328d9983be0d52f",
    "boss": "ea68a19f9ad39c55a8115c88a4a77ab3058481481b7b59c8b3dd6a13be50f084",
}
DISPOSITION = "325ff7dd99419673d5dfe4d02291de6189c69cbc0121a0d176dc77a3011780d4"
SOURCE = "d454ea02c374f7bd4aec8f14ca9bc151128516533db0161b60bcbcf5b479abc5"
IID = "9ce9dace-e595-4d8f-b893-5ae4899517de"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def pinned_bytes(path, digest):
    data = path.read_bytes()
    require(sha256(data).hexdigest() == digest, f"identity mismatch for {path.name}")
    return data


def observe(root, capture):
    disposition_path = root / "re/solidworks/measurements/2026/EllipseSeamNativeDisposition01.json"
    disposition = json.loads(pinned_bytes(disposition_path, DISPOSITION))
    pinned_bytes(Path(__file__).with_name("EllipseSeamAuthor.py"), SOURCE)
    cases = {}
    for role, pin in NATIVE.items():
        record = json.loads(pinned_bytes(capture / f"author-{role}" / "Record.json", pin))
        require(record["passed"] is True and record["writer_output_count"] == 0, "source-only phase did not pass")
        args = [row["arguments"]["values"] for row in record["api_calls"] if row["method"] == "InsertSketch"]
        require(len(args) == 2 and all(len(row) == 1 and row[0] is True for row in args),
                "both disclosed sketch edit toggles must pass True")
        stages = disposition["cases"][role]["author"]
        first, second = stages[:2]
        require([first["stage"], second["stage"]] == ["draw_open", "sketch_closed"] and
                first["live_point_id"] == second["live_point_id"] == [1, 1] and
                first["matches_saved"] is False and second["matches_saved"] is True,
                "disclosed seam phase or identity changed")
        saved = disposition["cases"][role]["saved"]
        require(saved["seam_id"] == [0, 1], "the archive role or handle changed")
        cases[role] = {
            "author_record_sha256": pin,
            "open_and_close_update_edit_rebuild": [row[0] for row in args],
            "live_point_id": first["live_point_id"],
            "wire_point_id": saved["seam_id"],
            "open_phase_degrees": first["phase_degrees"],
            "closed_phase_degrees": second["phase_degrees"],
        }
    return {
        "author_source_sha256": SOURCE,
        "disposition_sha256": DISPOSITION,
        "prior_fresh_native_processes": disposition["fresh_native_processes"],
        "cases": cases,
    }


def read_at(image, address, size):
    start = image.offset(address)
    require(image.offset(address + size - 1) == start + size - 1, "noncontiguous original mapping")
    return image.data[start:start + size]


def locators(app, api, model):
    for image, address in ((app, 0x45FC7CF0), (api, 0x432C6098)):
        require(str(uuid.UUID(bytes_le=read_at(image, address, 16))) == IID, "different ISketchManager IID")
    for image, address, expected in (
        (api, 0x432A7C58, 0x432C6098),
        (api, 0x432A7C60, 0x70),
        (api, 0x432A7CE8, 0x43314FF0),
        (api, 0x432A7CF0 + 0x108, 0x42EBA200),
        (model, 0x4D0E8E80 - 8, 0x4D34EB28),
        (model, 0x4D0E8E80 + 0x138, 0x4C0E6670),
        (model, 0x4D1252D8 - 8, 0x4D352FC0),
        (model, 0x4D1252D8 + 0x138, 0x4C1D2940),
    ):
        require(image.u64(image.offset(address)) == expected, f"owner cell differs at {address:#x}")
    for image, rtti, class_name in (
        (api, 0x43314FF0, ".?AVXDispatch@auSketchManager_c@@"),
        (model, 0x4D34EB28, ".?AVmoProfileFeature_c@@"),
        (model, 0x4D352FC0, ".?AVmoPart_c@@"),
    ):
        location = image.offset(rtti)
        require(image.u32(location) == 1 and image.u32(location + 20) == rtti - image.base and
                image.string(image.base + image.u32(location + 12) + 16) == class_name,
                f"RTTI owner changed at {rtti:#x}")
    return {
        "interface_iid": IID,
        "interface_map_entry_va": "0x432a7c58",
        "interface_subobject_offset": "0x70",
        "interface_vtable_va": "0x432a7cf0",
        "slot_offset": "0x108",
        "target_va": "0x42eba200",
        "profile_update_vtable_va": "0x4d0e8e80",
        "part_update_vtable_va": "0x4d1252d8",
    }


def check_import(image, address, module, symbol):
    imported = image.imports()[address]
    require(imported["module"].casefold() == module and imported["name"].startswith(symbol),
            f"import ownership changed at {address:#x}")


def check_sites(image, objdump, name, address, sites, leaf_bytes=None):
    bounds = image.range(address)
    if bounds is None:
        require(leaf_bytes is not None, f"no unwind record for {name}")
        bounds = address, address + leaf_bytes
    require(bounds[0] == address and bounds[1] > address, f"invalid procedure bounds for {name}")
    disassembly = subprocess.check_output([
        objdump, "-d", "--no-show-raw-insn", "--x86-asm-syntax=intel",
        f"--start-address={bounds[0]:#x}", f"--stop-address={bounds[1]:#x}", str(image.path),
    ], text=True)
    rows = {int(match[1], 16): " ".join(match[2].split())
            for line in disassembly.splitlines() if (match := re.fullmatch(r"([0-9a-f]+):\s+(.*)", line))}
    for _, site, instruction in sites:
        require(instruction in rows.get(site, ""), f"dispatch assertion differs at {site:#x}")
    return {
        "module": image.path.name,
        **image.pin(name, *bounds),
        "verified_sites": {meaning: hex(site) for meaning, site, _ in sites},
    }


def prove(binary_dir, objdump):
    images = {name: PeImage(binary_dir / name) for name in IMAGES}
    for name, image in images.items():
        require(image.sha256 == IMAGES[name] and image.u16(image.pe + 4) == 0x8664, f"wrong x64 image {name}")
    app, api, ui, model = images.values()
    interface = locators(app, api, model)
    check_import(api, 0x43036760, "slduiu.dll", "?OnInsertSketch2@uiModelDoc_c@@")
    check_import(ui, 0x4A44BB18, "sldmodu.dll", "?cleanOutUnusedSketchMidPoints@sgSketch@@")
    claims = (
        (app, "ISketchManager QueryInterface", 0x456DF320, (
            ("query interface result", 0x456DF3B8, "lea r8, [rbx + 0x50]"),
            ("query interface iid", 0x456DF3BC, "0x45fc7cf0"),
            ("query interface", 0x456DF3C6, "call qword ptr [rax]"),
        )),
        (app, "ISketchManager InsertSketch wrapper", 0x456E3E00, (
            ("ordinary forwarded branch", 0x456E3E95, "je 0x456e3e9d"),
            ("inner interface", 0x456E3E9D, "mov rcx, qword ptr [rbx + 0x50]"),
            ("variant bool", 0x456E3EA4, "movzx edx, di"),
            ("dispatch", 0x456E3EA7, "call qword ptr [rax + 0x108]"),
        )),
        (api, "auSketchManager constructor", 0x42EAF190, (
            ("document context", 0x42EAF1B6, "mov qword ptr [rdi + 0x68], rbx"),
            ("typed vtable", 0x42EAF1BA, "0x432a7cf0"),
            ("install interface", 0x42EAF1C1, "mov qword ptr [rdi + 0x70], rax"),
        )),
        (api, "auSketchManager XDispatch slot 33", 0x42EBA200, (
            ("interface to object", 0x42EBA217, "lea rsi, [rcx - 0x70]"),
            ("normalize variant bool", 0x42EBA293, "setne dl"),
            ("native adapter", 0x42EBA299, "call 0x42ec24a0"),
        )),
        (api, "auSketchManager native close adapter", 0x42EC24A0, (
            ("native document", 0x42EC24AF, "mov rbx, qword ptr [rcx + 0x68]"),
            ("pass update boolean", 0x42EC250D, "mov edx, esi"),
            ("pass api origin", 0x42EC250F, "mov r8d, edi"),
            ("OnInsertSketch2", 0x42EC2515, "0x43036760"),
        )),
        (ui, "uiModelDoc OnInsertSketch2", 0x49CC03D0, (
            ("forward update boolean", 0x49CC0431, "mov r9d, esi"),
            ("forward api origin", 0x49CC042D, "mov dword ptr [rsp + 0x20], edi"),
            ("shared insertSketch", 0x49CC043C, "call 0x49cc7c30"),
        )),
        (ui, "uiModelDoc active sketch close", 0x49CC7C30, (
            ("retain update boolean", 0x49CC7C60, "mov dword ptr [rsp + 0x6c], r9d"),
            ("get actual sketch", 0x49CC7EFB, "call 0x4a1aa430"),
            ("get actual profile", 0x49CC7F33, "call 0x4a1a9fc0"),
            ("cleanup 2d midpoints", 0x49CC803D, "0x4a44bb18"),
            ("check update boolean", 0x49CC80D3, "cmp dword ptr [rsp + 0x6c], 0x0"),
            ("no update branch", 0x49CC80D8, "je 0x49cc8664"),
            ("updated close helper", 0x49CC8282, "call 0x49cc63c0"),
            ("no update clear sketch", 0x49CC8830, "call 0x497bbaf0"),
        )),
        (ui, "active sketch close with update", 0x49CC63C0, (
            ("profile needs update", 0x49CC64D4, "0x4a45ed90"),
            ("profile update slot", 0x49CC65D4, "call qword ptr [rax + 0x138]"),
            ("model update slot", 0x49CC6767, "call qword ptr [rax + 0x138]"),
            ("updated clear sketch", 0x49CC6918, "call 0x497bbaf0"),
        )),
        (model, "moProfileFeature update slot", 0x4C0E6670, (
            ("local profile update alternative", 0x4C0E6711, "jmp 0x4c0dc6b0"),
        )),
        (model, "moProfileFeature local update", 0x4C0DC6B0, (
            ("typed sketch update", 0x4C0DCCDA, "call 0x4c549ab0"),
        )),
    )
    procedures = [check_sites(image, objdump, name, address, sites) for image, name, address, sites in claims]
    procedures.append(check_sites(app, objdump, "AddToDB environment setter", 0x456FBA00, (
        ("environment flag write", 0x456FBA00, "mov dword ptr [rcx + 0x2d8], edx"),
        ("return", 0x456FBA06, "ret"),
    ), leaf_bytes=7))
    return {
        "images": {name: {"sha256": image.sha256, "bytes": len(image.data), "base": hex(image.base)}
                   for name, image in images.items()},
        "interface": interface,
        "procedures": procedures,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bin", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--objdump", default="llvm-objdump")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[4]
    result = {
        "schema": 1,
        "build": "34.5.2.0604",
        "native_observation": observe(root, args.capture),
        "static_observation": prove(args.bin, args.objdump),
        "conclusion": "api_close_branch_bound_exact_seam_write_unresolved",
        "new_native_processes": 0,
        "writer_outputs": 0,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
