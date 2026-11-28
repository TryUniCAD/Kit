from __future__ import annotations

import ctypes
from hashlib import sha256
from pathlib import Path
from struct import unpack_from

import DrawingSaveAggregateDbgEng as engine
import DrawingSavePreviewGateDbgEng as preview


AFTER_PROPERTIES_RVA = 0x1DF5B
THIRD_PARTY_RVA = 0x1DFB5
PROPERTIES_STOPS = (
    {"module": "doccplu.dll", "instruction_rva": AFTER_PROPERTIES_RVA, "sample": "entry"},
    {"module": "doccplu.dll", "instruction_rva": THIRD_PARTY_RVA, "sample": "entry"},
)
ALLOWED_RVAS = frozenset((engine.STOP_RVA, AFTER_PROPERTIES_RVA, THIRD_PARTY_RVA))
SDK_HEADER_SHA256 = "88a62d326ecef94ee6b015b96bfa2b62254236b8638cf3ad9a807ba5e6dab632"


def original_image_byte(path, rva):
    data = path.read_bytes()
    engine.require(sha256(data).hexdigest() == engine.DOCCPLU_SHA256, "original module digest differs")
    pe = unpack_from("<I", data, 0x3C)[0]
    table = pe + 24 + unpack_from("<H", data, pe + 20)[0]
    for index in range(unpack_from("<H", data, pe + 6)[0]):
        _, address, raw_size, raw_offset = unpack_from("<IIII", data, table + 40 * index + 8)
        if address <= rva < address + raw_size:
            return data[raw_offset + rva - address:raw_offset + rva - address + 1]
    raise ValueError("pinned software breakpoint RVA lacks original file bytes")


def owned_process_byte(handle, address):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    read = kernel.ReadProcessMemory
    read.argtypes = (engine.PTR, engine.PTR, engine.PTR, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t))
    read.restype = ctypes.c_int32
    result = ctypes.c_ubyte()
    count = ctypes.c_size_t()
    success = read(engine.PTR(int(handle)), engine.PTR(address), ctypes.byref(result), 1, ctypes.byref(count))
    engine.require(success and count.value == 1,
                   f"owned instruction byte read failed with Windows error {ctypes.get_last_error()}")
    return bytes((result.value,))


class PropertiesGateTrace(preview.PreviewGateTrace):
    def __init__(self, sw, debugger_engine, identity):
        super().__init__(sw, debugger_engine, identity)
        self._module_base = None
        self._module_path = None
        self._process_handle = None
        self._engine_process_id = None
        self._active_site = None
        self._sites = []
        self.result["breakpoint_sites"] = self._sites
        self.result["cleanup_context_selections"] = []

    def doccplu_base(self, symbols, handle):
        from win32process import GetModuleFileNameEx

        base = super().doccplu_base(symbols, handle)
        engine.require(self._module_base in (None, base), "owned module base changed")
        self._module_base = base
        self._module_path = Path(GetModuleFileNameEx(handle, base))
        self._process_handle = handle
        return base

    def verify_stop(self, interfaces, handle, *, break_id, base, rva):
        result = super().verify_stop(interfaces, handle, break_id=break_id, base=base, rva=rva)
        identifier = interfaces["system"].value(7, "capture the owned engine process id")
        engine.require(self._engine_process_id in (None, identifier), "owned engine process identity changed")
        self._engine_process_id = identifier
        self.result["engine_process_id_captured"] = True
        return result

    def verify_owned_module(self, handle):
        from win32process import GetModuleFileNameEx

        self.confirm_owned(handle)
        engine.require(self._module_base is not None and self._module_path is not None, "owned module is unbound")
        module = Path(GetModuleFileNameEx(handle, self._module_base))
        engine.require(module == self._module_path and module.name.casefold() == "doccplu.dll",
                       "owned module identity changed")
        engine.check_amd64_image(module, engine.DOCCPLU_SHA256)

    def arm_breakpoint(self, control, state, offset):
        engine.require(self._module_base is not None, "owned module base is unbound")
        rva = offset - self._module_base
        engine.require(rva in ALLOWED_RVAS, "software breakpoint RVA is outside this fixed trial")
        handle = self._process_handle
        self.verify_owned_module(handle)
        original = original_image_byte(self._module_path, rva)
        before = owned_process_byte(handle, offset)
        engine.require(before == original, "owned breakpoint site differs from the original module before arming")
        record = {
            "rva": rva,
            "bytes": 1,
            "original_sha256": sha256(original).hexdigest(),
            "before_arm_sha256": sha256(before).hexdigest(),
            "before_arm_matches_original": True,
            "armed": False,
            "remove_call_succeeded": False,
        }
        self._sites.append(record)
        self._active_site = record
        identifier = super().arm_breakpoint(control, state, offset)
        record["armed"] = True
        return identifier

    def select_owned_context(self, system, handle, phase):
        entry = {"phase": phase, "selected": False, "owned_os_pid_verified": False}
        self.result["cleanup_context_selections"].append(entry)
        try:
            self.confirm_owned(handle)
            engine.require(self._engine_process_id is not None, "owned engine process id was not captured")
            system.call(8, "select the captured owned engine process", (engine.U32,), self._engine_process_id)
            entry["selected"] = True
            engine.require(system.value(27, "verify selected cleanup OS process id") == self.pid,
                           "selected cleanup process differs from the COM-owned process")
            self.confirm_owned(handle)
            entry["owned_os_pid_verified"] = True
        except Exception as error:
            entry["diagnostic"] = str(error)
            raise

    def remove_software_breakpoint(self, interfaces, breakpoint, handle):
        control = interfaces["control"]
        self.confirm_owned(handle)
        engine.require(engine.debugger_present(handle), "owned process has no debugger before explicit removal")
        self.select_owned_context(interfaces["system"], handle, "before_cleanup_status")
        status = control.value(49, "execution status before owned breakpoint removal")
        if status != engine.DEBUG_STATUS_BREAK:
            control.call(4, "request owned cleanup stop", (engine.U32,), engine.DEBUG_INTERRUPT_ACTIVE)
            self.result["cleanup_interrupt_requested"] = True
            engine.require(self.wait_event(control, engine.monotonic() + engine.CLEANUP_STOP_SECONDS, honor_cancel=False),
                           "owned cleanup stop timed out")
        self.select_owned_context(interfaces["system"], handle, "after_cleanup_stop")
        engine.require(control.value(49, "execution status after owned cleanup stop") == engine.DEBUG_STATUS_BREAK,
                       "owned process is not stopped for explicit breakpoint removal")
        self.verify_owned_module(handle)
        control.call(73, "remove owned software breakpoint", (engine.PTR,), breakpoint.pointer)
        if self._active_site is not None:
            self._active_site["remove_call_succeeded"] = True
            self._active_site = None

    def snapshot_sites(self, handle, phase):
        self.verify_owned_module(handle)
        for record in self._sites:
            expected = original_image_byte(self._module_path, record["rva"])
            actual = owned_process_byte(handle, self._module_base + record["rva"])
            record[phase] = {
                "bytes_read": len(actual),
                "sha256": sha256(actual).hexdigest(),
                "matches_original": actual == expected,
            }

    def _cleanup(self, client, interfaces, state, handle):
        audit = {"mode": "unverified", "before_detach_read_complete": False,
                 "after_detach_read_complete": False, "all_sites_original_after_detach": False,
                 "explicit_removal_complete": False, "detached_and_restored": False, "qualified": False}
        self.result["breakpoint_cleanup"] = audit
        if self._sites:
            try:
                self.snapshot_sites(handle, "before_detach")
                audit["before_detach_read_complete"] = True
            except Exception as error:
                audit["before_detach_diagnostic"] = str(error)
        super()._cleanup(client, interfaces, state, handle)
        if (self.result.get("detach_method") and self.result.get("cleanup_confirmed")
                and self.result.get("owned_process_debugger_present_after_cleanup") is False):
            try:
                self.snapshot_sites(handle, "after_detach")
                audit["after_detach_read_complete"] = True
            except Exception as error:
                audit["after_detach_diagnostic"] = str(error)
        armed = [row for row in self._sites if row["armed"]]
        audit["explicit_removal_complete"] = bool(
            armed and self.result.get("breakpoint_removed") and all(row["remove_call_succeeded"] for row in armed)
        )
        audit["all_sites_original_after_detach"] = bool(
            armed and all(row.get("after_detach", {}).get("matches_original") for row in armed)
        )
        audit["detached_and_restored"] = bool(
            audit["before_detach_read_complete"] and audit["after_detach_read_complete"]
            and audit["all_sites_original_after_detach"]
            and self.result.get("owned_process_debugger_present_after_cleanup") is False
        )
        audit["qualified"] = audit["detached_and_restored"]
        if audit["qualified"]:
            audit["mode"] = "explicit_removed" if audit["explicit_removal_complete"] else "detached_restored"

    def read_document_return(self, interfaces, handle, state, *, base, save_thread, save_stack):
        path = {}
        self.result["properties_path"] = path
        stack = self.observe_stage(
            interfaces, handle, state, base=base, save_thread=save_thread, save_stack=save_stack,
            path=path, name="after_document_properties", rva=AFTER_PROPERTIES_RVA,
            storage_stack=None, read_eax=False,
        )
        if stack is not None:
            self.observe_stage(
                interfaces, handle, state, base=base, save_thread=save_thread, save_stack=save_stack,
                path=path, name="third_party_dispatch", rva=THIRD_PARTY_RVA,
                storage_stack=stack, read_eax=False,
            )
