from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from struct import unpack_from
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from NativeNamePe import NativeNamePe, require


IDENTITIES = {
    "sldmodu.dll": "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e",
    "sldresu.dll": "531cf5d1c913f60f707652f0ecae600313d0970f7e649dcadec64983c484e111",
    "mfresu.dll": "a5cba60ca4df309845febfc39b7881a3025b53e5a4879bc66898d884a7830384",
    "slddialogresu.dll": "bd8d2e40405059d270917e7d2907934c023a245d990b219ee41dee944c0d8b31",
    "sldworks.exe": "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe",
    "mfc140u.dll": "88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1",
}


def x64_target(image, entry):
    address = entry + 9
    offset = image.offset(address - image.base, 5)
    require(image.data[offset] == 0xE9, "the selected hybrid export is not its traced x64 relative-jump stub")
    return address + 5 + unpack_from("<i", image.data, offset + 1)[0]


def arm_branch(image, address, link=False):
    word = unpack_from("<I", image.data, image.offset(address - image.base, 4))[0]
    require(word & 0xFC000000 == (0x94000000 if link else 0x14000000),
            "the traced ARM64EC branch instruction differs")
    delta = word & 0x3FFFFFF
    if delta & (1 << 25):
        delta -= 1 << 26
    return address + delta * 4


def arm_load_slot(image, address):
    offset = image.offset(address - image.base, 8)
    page_word, load_word = unpack_from("<II", image.data, offset)
    require(page_word & 0x9F000000 == 0x90000000 and load_word & 0xFFC00000 == 0xF9400000,
            "the traced ARM64EC import thunk no longer contains ADRP and LDR")
    register = page_word & 31
    require((load_word & 31) == ((load_word >> 5) & 31) == register,
            "ARM64EC import thunk register ownership differs")
    delta = ((page_word >> 5) & 0x7FFFF) << 2 | ((page_word >> 29) & 3)
    if delta & (1 << 20):
        delta -= 1 << 21
    page = (address & ~0xFFF) + (delta << 12)
    return page + ((load_word >> 10) & 0xFFF) * 8


def arm_iat(image, address):
    offset = image.offset(address - image.base, 12)
    page_word, _, branch_word = unpack_from("<III", image.data, offset)
    require(branch_word == 0xD61F0000 | ((page_word & 31) << 5), "ARM64EC import thunk has no matching indirect branch")
    return arm_load_slot(image, address)


def window(original, view, low, high):
    offset = view.offset(low - view.base, high - low)
    raw = view.data[offset:offset + high - low]
    initial = original.data[offset:offset + high - low]
    return {"start": hex(low), "end": hex(high), "bytes": len(raw),
            "sha256": sha256(raw).hexdigest(), "original_sha256": sha256(initial).hexdigest(),
            "code_unchanged_from_original": raw == initial}


def inspect(root):
    images, inventory = {}, []
    for name, identity in IDENTITIES.items():
        path = root / name
        require(path.is_file() and not path.is_symlink(), "use original regular images outside all checkouts")
        image = NativeNamePe(path.read_bytes())
        require(image.sha256 == identity, "a source image differs from the pinned original")
        images[name] = image
        inventory.append({"name": name, "sha256": image.sha256, "bytes": len(image.data),
                          "machine": hex(image.machine), "resource_id": "0x2e56", "matches": image.resource(0x2E56)})
    matches = [(row["name"], item) for row in inventory for item in row["matches"]]
    require(len(matches) == 1 and matches[0][0] == "sldresu.dll"
            and matches[0][1]["language_id"] == 1033 and matches[0][1]["value"] == "Thickness",
            "the explicit English resource inventory changed")
    original = images["mfc140u.dll"]
    view, metadata = original.hybrid()
    model_imports, mfc_imports = images["sldmodu.dll"].imports(), view.imports()
    slots = {"load_string": 0x4CD34E70, "compare": 0x4CD34E80}
    ordinals = {name: model_imports[slot]["ordinal"] for name, slot in slots.items()}
    require(ordinals == {"load_string": 8161, "compare": 2909}
            and all(model_imports[slot]["module"].casefold() == "mfc140u.dll" for slot in slots.values()),
            "the native model no longer imports the declared MFC operations")
    entries = {name: view.ordinal(number) for name, number in ordinals.items()}
    bodies = {name: x64_target(view, int(value["address"], 16)) for name, value in entries.items()}
    require(bodies == {"load_string": 0x18034A4F0, "compare": 0x18037F2A0},
            "the correct hybrid ordinal thunks changed")
    load_config = view.offset(unpack_from("<I", view.data, view.optional + 112 + 10 * 8)[0])
    chpe = unpack_from("<Q", view.data, load_config + 0xC8)[0] - view.base
    chpe_offset = view.offset(chpe)
    version, code_map, map_count = unpack_from("<III", view.data, chpe_offset)
    require(version == 2, "the declared CHPE metadata version differs")
    aux_iat = unpack_from("<I", view.data, chpe_offset + 0x2C)[0]
    normal_iat = unpack_from("<I", view.data, view.optional + 112 + 12 * 8)[0]
    code_ranges = []
    for index in range(map_count):
        start, length = unpack_from("<II", view.data, view.offset(code_map) + index * 8)
        code_ranges.append({"start_rva": start & ~3, "end_rva": (start & ~3) + length, "type": start & 3})

    def imported(address):
        auxiliary = arm_iat(view, address)
        normal = auxiliary - aux_iat + normal_iat
        exit_target = unpack_from("<Q", view.data, view.offset(auxiliary - view.base, 8))[0]
        require(arm_load_slot(view, exit_target) == normal,
                "the auxiliary exit thunk does not load the corresponding ordinary import slot")
        require(normal in mfc_imports, "the ARM64EC auxiliary IAT has no corresponding original import")
        return {"thunk": hex(address), "auxiliary_slot": hex(auxiliary), "normal_slot": hex(normal),
                "exit_thunk": hex(exit_target), "exit_window": window(original, view, exit_target, exit_target + 20),
                "import": mfc_imports[normal]}

    compare_target = arm_branch(view, 0x18037F2A8)
    compare = imported(compare_target)
    require(compare["import"]["name"] == "_wcsicmp", "the native special-name comparison is not case-insensitive wide text")
    resource_handle = arm_branch(view, 0x18034A514, True)
    explicit_load = arm_branch(view, 0x18034A534, True)
    require(resource_handle == 0x180660450 and explicit_load == 0x18034A400,
            "the native MFC resource lookup ownership differs")
    lookup = arm_branch(view, 0x18034A420, True)
    require(lookup == 0x18034A340, "the MFC explicit loader does not use the traced string-block lookup")
    kernel = {name: imported(address) for name, address in {
        "find": 0x180337D68, "load": 0x180337D5C, "lock": 0x180337D50, "size": 0x180337D44,
    }.items()}
    require({name: value["import"]["name"] for name, value in kernel.items()}
            == {"find": "FindResourceW", "load": "LoadResource", "lock": "LockResource", "size": "SizeofResource"},
            "the traced native block loader imports differ")
    ranges = {
        "x64_load_string_stub": (0x1806AE170, 0x1806AE17E),
        "x64_compare_stub": (0x180699F80, 0x180699F8E),
        "arm64ec_load_string": (0x18034A4F0, 0x18034A548),
        "arm64ec_compare_leaf": (0x18037F2A0, 0x18037F2B4),
        "arm64ec_compare_import_thunk": (0x180338538, 0x180338544),
        "arm64ec_string_block_lookup": (0x18034A340, 0x18034A3F8),
        "arm64ec_resource_handle_search": (0x180660450, 0x1806606EC),
        "arm64ec_explicit_string_load": (0x18034A400, 0x18034A4E4),
    }
    return {
        "schema": "kit.sw2026.cylinder-native-name-resource.v1", "passed": True,
        "original_images": inventory, "special_name_resource": matches[0][1],
        "mfc_hybrid_view": metadata, "chpe": {"version": version, "rva": hex(chpe),
                                               "auxiliary_iat_rva": hex(aux_iat), "normal_iat_rva": hex(normal_iat),
                                               "code_ranges": code_ranges},
        "model_imports": {name: {"slot": hex(slot), **model_imports[slot]} for name, slot in slots.items()},
        "raw_arm64_ordinals": {name: original.ordinal(number) for name, number in ordinals.items()},
        "hybrid_ordinals": entries, "hybrid_bodies": {name: hex(value) for name, value in bodies.items()},
        "wide_compare": compare, "kernel_resource_imports": kernel,
        "method_windows": {name: window(original, view, *extent) for name, extent in ranges.items()},
        "explicit_names": [{"name": name, "equals_english_special_name": name.casefold() == matches[0][1]["value"].casefold(),
                            "new_f2c_mask_from_this_branch": 0x1 if name.casefold() == matches[0][1]["value"].casefold() else 0,
                            "native_custom_name_lifecycle_qualified": False}
                           for name in ("Radius", "Height")],
        "scope": "original English resource and declared correct-view setter branch only",
        "live_selected_resource_handle_observed": False, "other_locales_qualified": False,
        "native_processes_started": 0, "heldout_inputs_read": 0, "generated_native_files": 0,
        "binary_written": False,
    }


def main():
    parser = ArgumentParser(description="Pin the original English parameter-name resource and the correct ARM64X MFC route")
    parser.add_argument("images", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = inspect(args.images)
    raw = (json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with args.output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"passed": True, "output_sha256": sha256(raw).hexdigest(),
                      "original_images": len(IDENTITIES), "native_processes_started": 0, "heldout_inputs_read": 0}))


if __name__ == "__main__":
    main()
