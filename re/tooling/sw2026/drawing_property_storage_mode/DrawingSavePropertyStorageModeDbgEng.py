from __future__ import annotations

import ctypes
from hashlib import sha256
from pathlib import Path
from struct import unpack_from

import DrawingSavePropertiesGateDbgEng as restoration


engine = restoration.engine
BASE_TRACE = restoration.preview.PreviewGateTrace.__base__
SDK_HEADER_SHA256 = restoration.SDK_HEADER_SHA256
MODULE_SHA256 = {
    "doccplu.dll": engine.DOCCPLU_SHA256,
    "sldappu.dll": "50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf",
}
STORAGE_MODE_RVA = 0x4F763B
FALLBACK_HRESULT_RVA = 0x4F769B
PROPERTY_CALL_RVA = 0x4F76AF
PROPERTY_RETURN_RVA = 0x4F76B5
ALLOWED_RVAS = {
    "doccplu.dll": frozenset((engine.STOP_RVA,)),
    "sldappu.dll": frozenset((STORAGE_MODE_RVA, FALLBACK_HRESULT_RVA, PROPERTY_CALL_RVA, PROPERTY_RETURN_RVA)),
}
STOPS = (
    {"module": "sldappu.dll", "instruction_rva": STORAGE_MODE_RVA, "sample": "storage_mode_and_nullness"},
    {"module": "sldappu.dll", "instruction_rva": FALLBACK_HRESULT_RVA, "sample": "signed_hresult", "conditional": True},
    {"module": "sldappu.dll", "instruction_rva": PROPERTY_CALL_RVA, "sample": "typed_argument_nullness"},
    {"module": "sldappu.dll", "instruction_rva": PROPERTY_RETURN_RVA, "sample": "signed_eax"},
)


def original_byte(path, module, rva):
    engine.require(module in MODULE_SHA256 and rva in ALLOWED_RVAS[module], "instruction is outside the fixed whitelist")
    data = path.read_bytes()
    engine.require(sha256(data).hexdigest() == MODULE_SHA256[module], "original module digest differs")
    pe = unpack_from("<I", data, 0x3C)[0]
    table = pe + 24 + unpack_from("<H", data, pe + 20)[0]
    for index in range(unpack_from("<H", data, pe + 6)[0]):
        _, address, raw_size, raw_offset = unpack_from("<IIII", data, table + 40 * index + 8)
        if address <= rva < address + raw_size:
            return data[raw_offset + rva - address:raw_offset + rva - address + 1]
    raise ValueError("fixed instruction has no original file byte")


def register64(registers, name):
    index = engine.U32()
    registers.call(5, f"locate AMD64 {name}", (engine.CSTR, engine.P32), name.encode("ascii"), ctypes.byref(index))
    value = engine.DebugValue()
    registers.call(6, f"read AMD64 {name}", (engine.U32, engine.PTR), index.value, ctypes.byref(value))
    engine.require(value.type == engine.DEBUG_VALUE_INT64, f"AMD64 {name} lacks a typed 64-bit register")
    return value.integer


def pointer64(data, address):
    engine.require(address != 0, "cannot read a member of a null owner")
    value, count = engine.U64(), engine.U32()
    data.call(6, "read the typed eight-byte owner member", (engine.U64, engine.PTR, engine.U32, engine.P32),
              address, ctypes.byref(value), ctypes.sizeof(value), ctypes.byref(count))
    engine.require(count.value == ctypes.sizeof(value), "typed owner-member read is incomplete")
    return value.value


def eax_sample(registers):
    bits = register64(registers, "rax") & 0xFFFFFFFF
    return {"eax_signed": ctypes.c_int32(bits).value, "eax_hex": f"0x{bits:08x}"}


class PropertyStorageModeTrace(restoration.PropertiesGateTrace):
    def __init__(self, sw, debugger_engine, identity):
        super().__init__(sw, debugger_engine, identity)
        self._modules = {}

    def doccplu_base(self, symbols, handle):
        base = super().doccplu_base(symbols, handle)
        self._modules["doccplu.dll"] = {"base": base, "path": self._module_path}
        return base

    def bind_module(self, symbols, handle, module):
        from win32process import GetModuleFileNameEx

        engine.require(module in MODULE_SHA256, "module is outside the fixed whitelist")
        self.confirm_owned(handle)
        index, base = engine.U32(), engine.U64()
        symbols.call(14, f"locate loaded {module}", (engine.CSTR, engine.U32, engine.P32, engine.P64),
                     module.removesuffix(".dll").encode("ascii"), 0, ctypes.byref(index), ctypes.byref(base))
        engine.require(base.value, "fixed module has no live base")
        path = Path(GetModuleFileNameEx(handle, base.value))
        engine.require(path.name.casefold() == module, "loaded module path belongs to another image")
        engine.check_amd64_image(path, MODULE_SHA256[module])
        previous = self._modules.get(module)
        engine.require(previous is None or previous == {"base": base.value, "path": path}, "loaded module identity changed")
        self._modules[module] = {"base": base.value, "path": path}
        return base.value

    def verify_owned_module(self, handle):
        from win32process import GetModuleFileNameEx

        self.confirm_owned(handle)
        engine.require(bool(self._modules), "owned modules are unbound")
        for name, row in self._modules.items():
            path = Path(GetModuleFileNameEx(handle, row["base"]))
            engine.require(path == row["path"] and path.name.casefold() == name, "owned module identity changed")
            engine.check_amd64_image(path, MODULE_SHA256[name])

    def arm_breakpoint(self, control, state, offset):
        matches = [(name, row, offset - row["base"]) for name, row in self._modules.items()
                   if offset - row["base"] in ALLOWED_RVAS[name]]
        engine.require(len(matches) == 1, "software breakpoint is outside the fixed module/address whitelist")
        name, row, rva = matches[0]
        self.verify_owned_module(self._process_handle)
        original = original_byte(row["path"], name, rva)
        before = restoration.owned_process_byte(self._process_handle, offset)
        engine.require(before == original, "owned instruction differs before breakpoint arming")
        site = {"module": name, "rva": rva, "bytes": 1, "original_sha256": sha256(original).hexdigest(),
                "before_arm_sha256": sha256(before).hexdigest(), "before_arm_matches_original": True,
                "armed": False, "remove_call_succeeded": False}
        self._sites.append(site)
        self._active_site = site
        identifier = BASE_TRACE.arm_breakpoint(self, control, state, offset)
        site["armed"] = True
        return identifier

    def verify_stop(self, interfaces, handle, *, break_id, base, rva):
        site = self._active_site
        engine.require(site is not None and site["rva"] == rva, "stop lacks its fixed active site")
        module = site["module"]
        engine.require(self.bind_module(interfaces["symbols"], handle, module) == base, "fixed module base changed")
        control = interfaces["control"]
        event, process, thread, seen, used = (engine.U32() for _ in range(5))
        control.call(94, "read the fixed software breakpoint event",
                     (engine.P32, engine.P32, engine.P32, engine.PTR, engine.U32, engine.P32, engine.PTR, engine.U32, engine.P32),
                     ctypes.byref(event), ctypes.byref(process), ctypes.byref(thread), ctypes.byref(seen),
                     ctypes.sizeof(seen), ctypes.byref(used), None, 0, None)
        engine.require((event.value, seen.value, used.value) == (engine.DEBUG_EVENT_BREAKPOINT, break_id, ctypes.sizeof(seen)),
                       "debug event differs from the fixed software breakpoint")
        engine.require(self.save_entered.is_set() and self.event7_seen.is_set() and not self.save_returned.is_set(),
                       "stop is outside the owned event-7 SaveAs interval")
        system = interfaces["system"]
        engine.require(system.value(27, "software-stop OS process id") == self.pid, "stop belongs to another process")
        self.confirm_owned(handle)
        effective = control.value(47, "effective processor at the fixed stop")
        executing = control.value(36, "executing processor at the fixed stop")
        engine.require(effective == executing == engine.AMD64, "fixed stop lacks executed AMD64 context")
        registers = interfaces["registers"]
        engine.require(registers.value(11, "AMD64 instruction offset", engine.U64) == base + rva,
                       "AMD64 RIP differs from the fixed instruction")
        stack = registers.value(12, "AMD64 stack offset", engine.U64)
        engine.require(stack != 0, "fixed stop has no AMD64 stack")
        identifier = system.value(7, "capture the owned engine process id")
        engine.require(self._engine_process_id in (None, identifier), "owned engine process identity changed")
        self._engine_process_id = identifier
        self.result["engine_process_id_captured"] = True
        return thread.value, stack, effective, executing

    def snapshot_sites(self, handle, phase):
        self.verify_owned_module(handle)
        for site in self._sites:
            row = self._modules[site["module"]]
            expected = original_byte(row["path"], site["module"], site["rva"])
            actual = restoration.owned_process_byte(handle, row["base"] + site["rva"])
            site[phase] = {"bytes_read": len(actual), "sha256": sha256(actual).hexdigest(), "matches_original": actual == expected}

    def observe_typed_stage(self, interfaces, handle, state, *, module_base, save_thread, save_stack,
                            path, name, rva, first_stack, sample_kind):
        stack = super().observe_stage(
            interfaces, handle, state, base=module_base, save_thread=save_thread, save_stack=save_stack,
            path=path, name=name, rva=rva, storage_stack=first_stack, read_eax=False,
        )
        path[name]["module"] = "sldappu.dll"
        if stack is None:
            return None
        sample = path[name]["sample"]
        registers, data = interfaces["registers"], interfaces["data"]
        if sample_kind in ("mode", "eax"):
            sample.update(eax_sample(registers))
        if sample_kind == "mode":
            sample["retained_istorage_null"] = register64(registers, "r14") == 0
            sample["storage_wrapper_null"] = register64(registers, "rbx") == 0
        if sample_kind == "arguments":
            owner = register64(registers, "rcx")
            sample.update(property_owner_null=owner == 0, storage_argument_null=register64(registers, "rdx") == 0,
                          custom_data_argument=register64(registers, "r8") & 0xFFFFFFFF,
                          property_option_argument=register64(registers, "r9") & 0xFFFFFFFF,
                          summary_owner_null=None if owner == 0 else pointer64(data, owner + 0x1D8) == 0)
        return stack

    def read_document_return(self, interfaces, handle, state, *, base, save_thread, save_stack):
        module_base = self.bind_module(interfaces["symbols"], handle, "sldappu.dll")
        path = {}
        self.result["property_storage_path"] = path
        common = {"interfaces": interfaces, "handle": handle, "state": state, "module_base": module_base,
                  "save_thread": save_thread, "save_stack": save_stack, "path": path}
        stack = self.observe_typed_stage(**common, name="storage_mode", rva=STORAGE_MODE_RVA,
                                         first_stack=None, sample_kind="mode")
        if stack is None:
            return
        sample = path["storage_mode"]["sample"]
        if sample["eax_signed"] == 0 and sample["retained_istorage_null"]:
            reached = self.observe_typed_stage(**common, name="fallback_storage_hresult", rva=FALLBACK_HRESULT_RVA,
                                              first_stack=stack, sample_kind="eax")
            if reached is None or path["fallback_storage_hresult"]["sample"]["eax_signed"] < 0:
                return
        reached = self.observe_typed_stage(**common, name="property_store_call", rva=PROPERTY_CALL_RVA,
                                          first_stack=stack, sample_kind="arguments")
        if reached is not None:
            self.observe_typed_stage(**common, name="property_store_return", rva=PROPERTY_RETURN_RVA,
                                     first_stack=stack, sample_kind="eax")
