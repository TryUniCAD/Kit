from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import ctypes
import ctypes.wintypes as wt
import hashlib
import json
import os
from pathlib import Path
import re
import struct

import InspectMfcFiles as files


MFC_SHA256 = "88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1"
MFC_VERSION = (14, 50, 35719, 0)
INVENTORY_SHA256 = "67d0e37be1e2cabdf2e233c66d2654b3caa2dc1692ef285df76190b6eb0b0a87"
HELPER_SHA256 = "195a0d90fe26169b31e87234910af29b2b1f5289b58d29a2e91cafca62602960"
ORDINALS = (12087, 14278)
PROCESS_MACHINE_TYPE_INFO = 9
COUNT_BODY_SPECS = {
    12087: {
        "thunk_rva": 0x6BCC70,
        "thunk_sha256": "fa55fff220c458e914d00249b5fb46b623778bdde557fe261afeb6883fee0469",
        "target_rva": 0x557B30,
        "bytes": 288,
        "body_sha256": "cd381ab524f765a17274de09b371c47ed028f0c3b2b31804eb3871fa71a5c0e4",
    },
    14278: {
        "thunk_rva": 0x6C5370,
        "thunk_sha256": "693ed1a1e4a317c9fed2fa8dc1dee237e7c670b2aae9ebb97c35c5031402e6dd",
        "target_rva": 0x557980,
        "bytes": 424,
        "body_sha256": "ad9500fd35f8e392d159dbebacd41f377ec1fdbf9f778a25c76c2834af7fda84",
    },
}
MAX_BLOCK = 2 * 1024 * 1024
MAX_CAPTURE = 4 * 1024 * 1024


class ModuleInfo(ctypes.Structure):
    _fields_ = [
        ("base", ctypes.c_void_p),
        ("image_size", wt.DWORD),
        ("entry_point", ctypes.c_void_p),
    ]


class ProcessMachineInfo(ctypes.Structure):
    _fields_ = [
        ("machine", wt.USHORT),
        ("reserved", wt.USHORT),
        ("attributes", wt.DWORD),
    ]


def kernel_api():
    kernel = ctypes.WinDLL("kernel32.dll", use_last_error=True, winmode=0x800)
    signatures = [
        ("GetCurrentProcess", [], wt.HANDLE),
        ("IsWow64Process2", [wt.HANDLE, ctypes.POINTER(wt.USHORT), ctypes.POINTER(wt.USHORT)], wt.BOOL),
        ("GetProcessInformation", [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD], wt.BOOL),
        ("GetSystemDirectoryW", [wt.LPWSTR, wt.UINT], wt.UINT),
        ("GetModuleHandleW", [wt.LPCWSTR], wt.HMODULE),
        ("LoadLibraryExW", [wt.LPCWSTR, wt.HANDLE, wt.DWORD], wt.HMODULE),
        ("GetModuleFileNameW", [wt.HMODULE, wt.LPWSTR, wt.DWORD], wt.DWORD),
        ("K32GetModuleInformation", [wt.HANDLE, wt.HMODULE, ctypes.POINTER(ModuleInfo), wt.DWORD], wt.BOOL),
        ("ReadProcessMemory", [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)], wt.BOOL),
        ("GetProcAddress", [wt.HMODULE, ctypes.c_void_p], ctypes.c_void_p),
        ("FreeLibrary", [wt.HMODULE], wt.BOOL),
    ]
    for name, arguments, result in signatures:
        function = getattr(kernel, name)
        function.argtypes, function.restype = arguments, result
    return kernel


class MappedPe(files.PeFile):
    def __init__(self, kernel, process, base, size):
        self.kernel, self.process, self.base = kernel, process, base
        super().__init__(None, size)

    def read(self, offset, length):
        if offset < 0 or length < 0 or length > MAX_BLOCK or offset + length > self.size:
            raise ValueError("mapped read exceeds the selected module or per-read bound")
        if length == 0:
            return b""
        buffer = ctypes.create_string_buffer(length)
        transferred = ctypes.c_size_t()
        if not self.kernel.ReadProcessMemory(self.process, self.base + offset, buffer, length, ctypes.byref(transferred)):
            raise ctypes.WinError(ctypes.get_last_error())
        if transferred.value != length:
            raise RuntimeError("short read from the owned process")
        return buffer.raw

    def locate(self, rva, length):
        if rva < 0 or length < 0 or rva + length > self.size:
            raise ValueError("mapped RVA exceeds module bounds")
        if rva < self.header_size and rva + length <= self.header_size:
            return rva, self.header_size - rva, None
        for section in self.sections:
            available = max(section["virtual_size"], section["raw_size"])
            delta = rva - section["rva"]
            if 0 <= delta < available and delta + length <= available:
                return rva, min(available - delta, self.size - rva), section
        raise ValueError("mapped RVA is outside an admitted section")

    def directory(self, index):
        pe = struct.unpack("<I", self.read(0x3C, 4))[0]
        optional_size = struct.unpack("<H", self.read(pe + 20, 2))[0]
        if self.magic != 0x20B or 112 + 8 * (index + 1) > optional_size:
            raise ValueError("unsupported mapped directory framing")
        count = struct.unpack("<I", self.read(pe + 24 + 108, 4))[0]
        return (0, 0) if count <= index else struct.unpack("<II", self.read(pe + 24 + 112 + 8 * index, 8))


def inspect_owned_executable(kernel, process, executable):
    module = kernel.GetModuleHandleW(None)
    if not module:
        raise ctypes.WinError(ctypes.get_last_error())
    buffer = ctypes.create_unicode_buffer(32768)
    length = kernel.GetModuleFileNameW(module, buffer, len(buffer))
    if not length or length >= len(buffer) or not Path(buffer.value).samefile(executable):
        raise RuntimeError("mapped own executable does not match the inspected Python file")
    information = ModuleInfo()
    if not kernel.K32GetModuleInformation(process, module, ctypes.byref(information), ctypes.sizeof(information)):
        raise ctypes.WinError(ctypes.get_last_error())
    if information.base != module or not information.image_size:
        raise RuntimeError("mapped own-executable bounds are ambiguous")
    image = MappedPe(kernel, process, information.base, information.image_size)
    if image.magic != 0x20B or not 0 < image.header_size <= 65536:
        raise RuntimeError("mapped own executable has unsupported header framing")
    pe = struct.unpack("<I", image.read(0x3C, 4))[0]
    declared_size = struct.unpack("<I", image.read(pe + 24 + 56, 4))[0]
    if declared_size != image.size:
        raise RuntimeError("own-executable header and OS module bounds disagree")
    return {"path": buffer.value, "base": hex(image.base), "image_size": image.size, "declared_image_size": declared_size, "machine": image.machine, "machine_hex": hex(image.machine), "optional_header_magic": hex(image.magic), "header_bytes": image.header_size, "header_sha256": hashlib.sha256(image.read(0, image.header_size)).hexdigest(), "module_reference_acquired": False}


def checkpoint(output, report, stage):
    report.update(stage=stage, updated_at=files.utc_now())
    files.write_json(output / "Inventory.json", report)


def identity_matches(value):
    versions = value.get("pe", {}).get("version_resources", {}).get("entries", [])
    return (
        value.get("sha256") == MFC_SHA256
        and value.get("bytes") == 12118600
        and value.get("pe", {}).get("machine") == 0xAA64
        and bool(versions)
        and all(tuple(item["fixed_info"]["file_version_words"]) == MFC_VERSION for item in versions)
    )


def save_range(output, report, image, name, rva, size, maximum, expected_raw=None):
    if size <= 0 or size > maximum or sum(item["bytes"] for item in report["private_ranges"]) + size > MAX_CAPTURE:
        raise ValueError("private capture exceeds its declared bounds")
    payload = image.read_rva(rva, size)
    path = output / f"{name}.private.bin"
    with path.open("xb") as stream:
        stream.write(payload)
    record = {"file": path.name, "rva": rva, "mapped_address": hex(image.base + rva), "bytes": size, "sha256": hashlib.sha256(payload).hexdigest(), "full_function_extent_claimed": False}
    report["private_ranges"].append(record)
    if expected_raw is not None:
        record["raw_sha256"] = hashlib.sha256(expected_raw).hexdigest()
        record["mapped_equals_pinned_raw"] = payload == expected_raw
        if not record["mapped_equals_pinned_raw"]:
            raise RuntimeError("mapped count body differs from the pinned raw body")
        record["full_function_extent_claimed"] = True
    return record


def capture_code(output, report, image, name, address):
    rva = address - image.base
    offset, available, section = image.locate(rva, 1)
    if section is None or not section["characteristics"] & 0x20000000:
        raise ValueError("resolved target is not in an executable section of the selected module")
    return save_range(output, report, image, name, rva, min(4096, available), 4096)


def capture_count_body(output, report, image, ordinal, address, runtime_path):
    specification = COUNT_BODY_SPECS[ordinal]
    if address != image.base + specification["thunk_rva"]:
        raise RuntimeError("selected count export has an unexpected thunk RVA")
    thunk = image.read_rva(specification["thunk_rva"], 14)
    thunk_hash = hashlib.sha256(thunk).hexdigest()
    if thunk_hash != specification["thunk_sha256"] or thunk[9] != 0xE9:
        raise RuntimeError("count export is not the exact pinned fast-forward sequence")
    target_rva = address + 14 + struct.unpack_from("<i", thunk, 10)[0] - image.base
    if target_rva != specification["target_rva"]:
        raise RuntimeError("count fast-forward target differs from the pinned body")
    offset, available, section = image.locate(target_rva, specification["bytes"])
    if section is None or not section["characteristics"] & 0x20000000:
        raise RuntimeError("count body span is not within the selected executable module")
    with runtime_path.open("rb") as stream:
        raw = files.PeFile(stream, os.fstat(stream.fileno()).st_size)
        raw_thunk = raw.read_rva(specification["thunk_rva"], 14)
        raw_body = raw.read_rva(target_rva, specification["bytes"])
    if raw_thunk != thunk or hashlib.sha256(raw_body).hexdigest() != specification["body_sha256"]:
        raise RuntimeError("raw count thunk or complete body differs from the pinned identity")
    body = save_range(output, report, image, f"Ordinal{ordinal}CountBody", target_rva, specification["bytes"], specification["bytes"], expected_raw=raw_body)
    report["count_bodies"].append({"ordinal": ordinal, "thunk_rva": specification["thunk_rva"], "thunk_bytes": 14, "thunk_sha256": thunk_hash, "target_rva": target_rva, "expected_body_sha256": specification["body_sha256"], "extent_evidence": "pinned original ARM64 pdata/xdata", "body": body})


def run(args, output, report):
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise RuntimeError("this probe requires an owned Windows x64 Python process")
    helper_hash = hashlib.sha256(Path(files.__file__).read_bytes()).hexdigest()
    report["helper_sha256"] = helper_hash
    if helper_hash != HELPER_SHA256:
        raise RuntimeError("file-inspection helper is not the reviewed revision")
    inventory_bytes = Path(args.inventory).read_bytes()
    if hashlib.sha256(inventory_bytes).hexdigest() != INVENTORY_SHA256:
        raise RuntimeError("discovery inventory identity differs from the retained run")
    inventory = json.loads(inventory_bytes)
    if inventory.get("state") != "completed" or not inventory.get("scan_complete") or inventory.get("errors"):
        raise RuntimeError("discovery inventory is incomplete")
    report["discovery"] = {"sha256": INVENTORY_SHA256, "source_revision": inventory["source_revision"]}
    kernel = kernel_api()
    process = kernel.GetCurrentProcess()
    process_machine, native_machine = wt.USHORT(), wt.USHORT()
    if not kernel.IsWow64Process2(process, ctypes.byref(process_machine), ctypes.byref(native_machine)):
        raise ctypes.WinError(ctypes.get_last_error())
    report["process_architecture"] = {"process_machine": hex(process_machine.value), "native_machine": hex(native_machine.value), "pointer_bytes": ctypes.sizeof(ctypes.c_void_p)}
    checkpoint(output, report, "query_actual_process_machine")
    machine_information = ProcessMachineInfo()
    if ctypes.sizeof(machine_information) != 8:
        raise RuntimeError("unexpected PROCESS_MACHINE_INFORMATION layout")
    if not kernel.GetProcessInformation(process, PROCESS_MACHINE_TYPE_INFO, ctypes.byref(machine_information), ctypes.sizeof(machine_information)):
        raise ctypes.WinError(ctypes.get_last_error())
    report["process_architecture"]["machine_type_information"] = {"information_class": PROCESS_MACHINE_TYPE_INFO, "structure_bytes": ctypes.sizeof(machine_information), "process_machine": hex(machine_information.machine), "machine_attributes": hex(machine_information.attributes)}
    report["python_file"] = files.inspect_file(Path(sys.executable), include_exports=False)
    checkpoint(output, report, "inspect_mapped_own_executable")
    report["python_mapped_image"] = inspect_owned_executable(kernel, process, Path(sys.executable))
    if machine_information.machine != 0x8664 or report["python_file"].get("pe", {}).get("machine") != 0x8664 or report["python_mapped_image"]["machine"] != 0x8664:
        raise RuntimeError("actual process, raw executable and mapped executable do not agree on AMD64")
    if native_machine.value != 0xAA64 or process_machine.value not in (0, 0x8664):
        raise RuntimeError("WOW64/native architecture observations conflict with the selected process")
    report["process_architecture_verified"] = True
    buffer = ctypes.create_unicode_buffer(32768)
    length = kernel.GetSystemDirectoryW(buffer, len(buffer))
    if not length or length >= len(buffer):
        raise RuntimeError("system directory query failed or was truncated")
    path = Path(buffer.value) / "mfc140u.dll"
    expected = [item for item in inventory["files"] if os.path.normcase(item["path"]) == os.path.normcase(str(path))]
    if len(expected) != 1 or not identity_matches(expected[0]):
        raise RuntimeError("system-directory runtime does not match the retained discovery identity")
    report["raw_file_before"] = files.inspect_file(path)
    if not identity_matches(report["raw_file_before"]):
        raise RuntimeError("raw system runtime hash, version, size or architecture differs")
    report["preexisting_module_handle"] = kernel.GetModuleHandleW("mfc140u.dll")
    if report["preexisting_module_handle"]:
        raise RuntimeError("the analysis process already contains this runtime")
    checkpoint(output, report, "before_load_exact_system_runtime")
    module = kernel.LoadLibraryExW(str(path), None, 0x900)
    if not module:
        raise ctypes.WinError(ctypes.get_last_error())
    report["module_loaded_by_probe"] = True
    try:
        checkpoint(output, report, "loaded_inspect_module_identity")
        length = kernel.GetModuleFileNameW(module, buffer, len(buffer))
        if not length or length >= len(buffer):
            raise RuntimeError("mapped module path query failed or was truncated")
        report["mapped_module_path"] = buffer.value
        if not Path(buffer.value).samefile(path):
            raise RuntimeError("OS loader selected a different runtime file")
        information = ModuleInfo()
        if not kernel.K32GetModuleInformation(process, module, ctypes.byref(information), ctypes.sizeof(information)):
            raise ctypes.WinError(ctypes.get_last_error())
        if information.base != module or not information.image_size:
            raise RuntimeError("mapped module bounds are ambiguous")
        image = MappedPe(kernel, process, information.base, information.image_size)
        if image.magic != 0x20B:
            raise RuntimeError("effective mapped image is not PE32+")
        pe = struct.unpack("<I", image.read(0x3C, 4))[0]
        optional = image.read(pe + 24, 64)
        declared_size = struct.unpack_from("<I", optional, 56)[0]
        report["mapped_pe"] = {"base": hex(image.base), "image_size": image.size, "declared_image_size": declared_size, "preferred_image_base": hex(struct.unpack_from("<Q", optional, 24)[0]), "machine": hex(image.machine), "optional_header_magic": hex(image.magic), "coff_timestamp_raw": image.timestamp, "header_size": image.header_size, "sections": image.sections}
        if declared_size != image.size:
            raise RuntimeError("effective header and OS module bounds disagree")
        if image.header_size > 65536:
            raise RuntimeError("mapped header exceeds the private capture limit")
        save_range(output, report, image, "MappedHeaders", 0, image.header_size, 65536)
        checkpoint(output, report, "inspect_effective_exports")
        exports = image.exports()
        for item in exports["ordinals"]:
            if "file_offset" in item:
                item["mapped_offset"] = item.pop("file_offset")
            if item.get("status") == "file_backed_export":
                item["status"] = "mapped_export"
        report["mapped_exports"] = exports
        ambiguous = [] if image.machine == 0x8664 else ["effective mapped PE machine is not AMD64"]
        if not exports.get("present") or exports.get("dll_name", "").casefold() != "mfc140u.dll":
            raise RuntimeError("effective export identity is absent or unexpected")
        save_range(output, report, image, "MappedExports", image.export_rva, image.export_size, 1024 * 1024)
        for index, name, maximum in [(3, "MappedExceptionDirectory", 2 * 1024 * 1024), (10, "MappedLoadConfig", 16384)]:
            rva, size = image.directory(index)
            report["mapped_directories"][name] = {"rva": rva, "bytes": size, "decoded": False}
            if rva or size:
                if not rva or not size:
                    raise RuntimeError("mapped directory has incomplete bounds")
                save_range(output, report, image, name, rva, size, maximum)
        for ordinal in ORDINALS:
            checkpoint(output, report, f"resolve_ordinal_{ordinal}")
            selected = [item for item in exports["ordinals"] if item["ordinal"] == ordinal]
            if len(selected) != 1 or selected[0].get("status") != "mapped_export" or not selected[0].get("section_executable"):
                raise RuntimeError(f"ordinal {ordinal} is missing, forwarded or not executable in the mapped view")
            address = kernel.GetProcAddress(module, ctypes.c_void_p(ordinal))
            if not address:
                raise ctypes.WinError(ctypes.get_last_error())
            expected_address = image.base + selected[0]["rva"]
            item = {"ordinal": ordinal, "mapped_eat_address": hex(expected_address), "get_proc_address": hex(address), "matches_mapped_eat": address == expected_address}
            report["resolved_ordinals"].append(item)
            item["eat_window"] = capture_code(output, report, image, f"Ordinal{ordinal}Eat", expected_address)
            if address != expected_address:
                ambiguous.append(f"ordinal {ordinal} resolver differs from the effective export table")
                item["resolved_window"] = capture_code(output, report, image, f"Ordinal{ordinal}Resolved", address)
            if args.capture_count_bodies and image.machine == 0x8664 and address == expected_address:
                checkpoint(output, report, f"capture_complete_count_body_{ordinal}")
                capture_count_body(output, report, image, ordinal, address, path)
        report["raw_file_after"] = files.inspect_file(path)
        if not identity_matches(report["raw_file_after"]) or any(report["raw_file_before"][key] != report["raw_file_after"][key] for key in ("file_identity", "mtime_ns", "bytes", "sha256")):
            raise RuntimeError("runtime file identity changed during inspection")
        report["ambiguities"] = ambiguous
        if ambiguous:
            raise RuntimeError("ambiguous effective runtime view: " + "; ".join(ambiguous))
        if args.capture_count_bodies and len(report["count_bodies"]) != len(ORDINALS):
            raise RuntimeError("requested count-body capture did not complete for both ordinals")
    finally:
        try:
            checkpoint(output, report, "release_owned_module_reference")
        finally:
            released = bool(kernel.FreeLibrary(module))
            report["owned_module_reference_released"] = released
            if not released:
                raise ctypes.WinError(ctypes.get_last_error())
    report["mapped_abi_view_verified"] = True
    report["count_body_bytes_verified"] = bool(args.capture_count_bodies)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--capture-count-bodies", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_revision):
        parser.error("--source-revision requires an exact lowercase Git object identity")
    output = Path(args.output).absolute()
    files.check_chain(output)
    if files.inside_checkout(output):
        parser.error("private mapped ranges must remain outside repository checkouts")
    output.mkdir(parents=False, exist_ok=False)
    report = {"schema": "kit.sw2026.mfc-runtime-view.v1", "state": "running", "started_at": files.utc_now(), "source_revision": args.source_revision, "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "argv": sys.argv, "python": sys.version, "python_executable": sys.executable, "process_id": os.getpid(), "process_architecture_verified": False, "mapped_abi_view_verified": False, "count_body_capture_requested": args.capture_count_bodies, "count_body_bytes_verified": False, "instruction_set_proven": False, "native_implementation_bound": False, "acceptance": False, "archive_methods_invoked": False, "private_ranges": [], "mapped_directories": {}, "resolved_ordinals": [], "count_bodies": []}
    checkpoint(output, report, "preflight")
    status = 1
    try:
        run(args, output, report)
        report["state"], status = "completed", 0
    except Exception as error:
        report.update(state="failed", error={"type": type(error).__name__, "message": str(error)})
    finally:
        report["finished_at"] = files.utc_now()
        checkpoint(output, report, "finished")
    print(json.dumps({"output": str(output), "state": report["state"], "mapped_abi_view_verified": report["mapped_abi_view_verified"], "native_implementation_bound": False}))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
