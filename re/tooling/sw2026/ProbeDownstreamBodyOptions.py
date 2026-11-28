from argparse import ArgumentParser
from ctypes import POINTER, WinDLL, byref, c_size_t, c_uint32, c_void_p, get_last_error, sizeof, WinError
from ctypes.wintypes import BOOL, DWORD, HANDLE, HMODULE
from hashlib import sha256
from json import dumps
from pathlib import Path

from win32api import OpenProcess
from win32process import GetModuleFileNameEx

from OracleIdentity import application_identity
import Swapp


MODEL_SHA256 = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
APPLICATION_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
OPTION_RVA = 0x2a1681c


def read_options(process_id):
    enumerate_modules = WinDLL("psapi", use_last_error=True).EnumProcessModulesEx
    enumerate_modules.argtypes = [HANDLE, POINTER(HMODULE), DWORD, POINTER(DWORD), DWORD]
    enumerate_modules.restype = BOOL
    read = WinDLL("kernel32", use_last_error=True).ReadProcessMemory
    read.argtypes = [HANDLE, c_void_p, c_void_p, c_size_t, POINTER(c_size_t)]
    read.restype = BOOL

    handle = OpenProcess(0x410, False, process_id)
    try:
        modules = (HMODULE * 4096)()
        size = DWORD()
        if not enumerate_modules(int(handle), modules, sizeof(modules), byref(size), 3):
            raise WinError(get_last_error())
        if size.value > sizeof(modules) or size.value % sizeof(HMODULE):
            raise ValueError("module inventory exceeded its buffer")
        for module in modules[:size.value // sizeof(HMODULE)]:
            original = Path(GetModuleFileNameEx(handle, module))
            if original.name.casefold() != "sldmodu.dll":
                continue
            digest = sha256(original.read_bytes()).hexdigest()
            if digest != MODEL_SHA256:
                raise ValueError("loaded model module differs from the pinned build")
            out = c_uint32()
            captured = c_size_t()
            if not read(int(handle), module + OPTION_RVA, byref(out), sizeof(out), byref(captured)):
                raise WinError(get_last_error())
            if captured.value != sizeof(out):
                raise ValueError("incomplete four-byte option sample")
            return {"loaded": True, "model_sha256": digest, "option_rva": OPTION_RVA,
                    "option_word": out.value, "forces_vertices": bool(out.value & 1),
                    "uses_body_representative": bool(out.value & 0x10)}
        return {"loaded": False}
    finally:
        handle.Close()


def main():
    parser = ArgumentParser()
    parser.add_argument("control", type=Path)
    parser.add_argument("control_sha256")
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    contents = args.control.read_bytes()
    if sha256(contents).hexdigest() != args.control_sha256:
        raise ValueError("known native control hash differs")
    result = {"schema": "kit.sw2026.downstream-body-options-live.v1", "control_sha256": args.control_sha256,
              "sampled": {}, "passed": False, "license_service_changes": 0}
    sample_stages = {"open_return", "rebuild_return", "close_start"}

    def checkpoint():
        args.receipt.write_text(dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    def progress(stage, facts):
        result["stage"] = stage
        if stage in sample_stages:
            result["sampled"][stage] = read_options(controller.process_id)
        checkpoint()

    with args.receipt.open("x", encoding="utf-8"):
        pass
    controller = None
    try:
        result["stage"] = "activate_registered_application"
        checkpoint()
        controller = Swapp.Sw()
        identity = application_identity(controller.app)
        result["oracle"] = identity
        if not identity["version_matches"] or identity["sha256"] != APPLICATION_SHA256:
            raise ValueError("oracle executable identity differs")
        result["sampled"]["startup"] = read_options(controller.process_id)
        control = Swapp.measure(controller, args.control, progress=progress, read_only=True)
        result["control"] = {
            key: control.get(key) for key in ("opened", "open_errors", "open_warnings", "rebuilt", "bodies", "mass",
                                               "features", "whats_wrong", "session_diagnostics")
        }
        result["passed"] = bool(
            control["opened"] and control["rebuilt"] and control["bodies"] == 1 and control["mass"]["volume"] > 0
            and control["open_errors"] == control["open_warnings"] == control["whats_wrong"] == 0
            and control["features"]
            and all(feature["error"] == 0 and feature["warning"] is False for feature in control["features"])
            and all(result["sampled"][stage]["loaded"] for stage in sample_stages)
        )
    except Exception as error:
        result["error"] = repr(error)
    finally:
        if controller is not None:
            controller.close()
            result["controller_diagnostics"] = controller.diagnostics
            if controller.diagnostics:
                result["passed"] = False
        checkpoint()
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
