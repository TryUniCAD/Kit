from __future__ import annotations

import ctypes
from hashlib import sha256
import os
from pathlib import Path
from struct import unpack_from
from threading import Event, Thread
from time import monotonic, monotonic_ns
from uuid import UUID


AMD64 = 0x8664
STOP_RVA = 0x15966
DOCUMENT_RETURN_RVA = 0x16421
DEBUG_VALUE_INT64 = 4
AGGREGATE_STACK_OFFSET = 0x1B0
SAMPLE_BYTES = 4
DOCCPLU_SHA256 = "ad0c266a966381defe9a68c11b76dc318acc6a9f6ac428d5aa253049df87ddd8"
SETUP_SECONDS = 20
SAVE_SECONDS = 20
JOIN_SECONDS = 7
CLEANUP_STOP_SECONDS = 4
CLEANUP_INTERRUPT_SECONDS = 3
WAIT_SLICE_MS = 250

DEBUG_ATTACH_DEFAULT = 0
DEBUG_ENGOPT_INITIAL_BREAK = 0x20
DEBUG_PROCESS_DETACH_ON_EXIT = 1
DEBUG_PROCESS_ONLY_THIS_PROCESS = 2
DEBUG_END_ACTIVE_DETACH = 2
DEBUG_STATUS_GO = 1
DEBUG_STATUS_BREAK = 6
DEBUG_INTERRUPT_ACTIVE = 0
DEBUG_BREAKPOINT_CODE = 0
DEBUG_BREAKPOINT_ENABLED = 4
DEBUG_EVENT_BREAKPOINT = 1
DEBUG_ANY_ID = 0xFFFFFFFF

PTR = ctypes.c_void_p
U32 = ctypes.c_uint32
U64 = ctypes.c_uint64
P32 = ctypes.POINTER(U32)
P64 = ctypes.POINTER(U64)
PPTR = ctypes.POINTER(PTR)
HRESULT = ctypes.c_int32
CSTR = ctypes.c_char_p

IIDS = {
    "client": "27fe5639-8407-4f47-8364-ee118fb08ac8",
    "control": "5182e668-105e-416e-ad92-24ef800424ba",
    "data": "88f7dfab-3ea7-4c3a-aefb-c4e8106173aa",
    "registers": "ce289126-9e84-45a7-937e-67bb18691493",
    "symbols": "8c31e98c-983a-48a5-9016-6fe5d667a950",
    "system": "6b86fe2c-2c4f-4f0c-9da2-174311acc327",
}



class DebugValue(ctypes.Structure):
    _fields_ = (("integer", U64), ("remaining", U64 * 2), ("tail", U32), ("type", U32))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def check(hr, label):
    if hr != 0:
        raise RuntimeError(f"{label} returned HRESULT 0x{hr & 0xFFFFFFFF:08x}")


def pe_machine(data):
    require(len(data) >= 64 and data[:2] == b"MZ", "expected a PE image")
    pe = unpack_from("<I", data, 60)[0]
    require(pe + 6 <= len(data) and data[pe:pe + 4] == b"PE\0\0", "invalid PE header")
    return unpack_from("<H", data, pe + 4)[0]


def check_amd64_image(path, expected_sha):
    data = path.read_bytes()
    require(pe_machine(data) == AMD64 and sha256(data).hexdigest() == expected_sha, f"{path.name} differs from the pinned AMD64 image")


def debugger_present(handle):
    state = ctypes.c_int32()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    query = kernel.CheckRemoteDebuggerPresent
    query.argtypes = (PTR, ctypes.POINTER(ctypes.c_int32))
    query.restype = ctypes.c_int32
    if not query(int(handle), ctypes.byref(state)):
        raise ctypes.WinError(ctypes.get_last_error())
    return bool(state.value)


def guid(name):
    return (ctypes.c_ubyte * 16).from_buffer_copy(UUID(IIDS[name]).bytes_le)


class Interface:
    def __init__(self, pointer):
        require(pointer.value, "DbgEng returned a null interface")
        self.pointer = pointer

    def invoke(self, slot, types=(), *args, result_type=HRESULT):
        table = ctypes.cast(self.pointer, ctypes.POINTER(ctypes.POINTER(PTR))).contents
        function = ctypes.WINFUNCTYPE(result_type, PTR, *types)(table[slot])
        return function(self.pointer, *args)

    def call(self, slot, label, types=(), *args):
        check(self.invoke(slot, types, *args), label)

    def value(self, slot, label, number_type=U32):
        result = number_type()
        self.call(slot, label, (ctypes.POINTER(number_type),), ctypes.byref(result))
        return result.value

    def query(self, name):
        pointer = PTR()
        ident = guid(name)
        self.call(0, f"QueryInterface({name})", (PTR, PPTR), ctypes.byref(ident), ctypes.byref(pointer))
        return Interface(pointer)

    def release(self):
        self.invoke(2, result_type=U32)


class SaveAggregateTrace:
    def __init__(self, sw, engine, identity):
        self.sw = sw
        self.engine = engine
        self.identity = identity
        self.pid = identity["process_id"]
        self.ready = Event()
        self.cancel = Event()
        self.started_ns = monotonic_ns()
        self.save_entered = Event()
        self.save_returned = Event()
        self.event7_seen = Event()
        self.thread = Thread(target=self._run, name="BlankDrawingSaveAggregate", daemon=True)
        self.result = {
            "armed": False, "cleanup_confirmed": True, "sample": None, "failure": None,
            "stage": "open_owned_process", "failure_stage": None, "attach_requested": False,
            "initial_stop_verified": False, "process_options_verified": False,
            "detach_method": None, "owned_process_debugger_present_after_cleanup": None,
            "breakpoint_kind": "dbgeng_managed_software",
        }

    def wait_event(self, control, deadline, *, honor_cancel=True):
        while not honor_cancel or not self.cancel.is_set():
            left_ms = int((deadline - monotonic()) * 1000)
            if left_ms <= 0:
                return False
            status = control.invoke(93, (U32, U32), 0, min(left_ms, WAIT_SLICE_MS))
            if status == 1:
                continue
            check(status, "WaitForEvent")
            return True
        return False

    def confirm_owned(self, handle):
        from OracleIdentity import process_creation_time

        require(self.sw.owned_process_ids() == {self.pid}, "the pinned process is outside this COM-owned session")
        require(self.sw.WaitForSingleObject(handle, 0) == self.sw.WAIT_TIMEOUT, "the COM-owned process is no longer live")
        require(process_creation_time(handle) == self.identity["process_creation_filetime"], "the COM-owned process identity changed")

    def event_offset(self):
        return monotonic_ns() - self.started_ns

    def call_owned_save(self, original, args):
        require(not self.save_entered.is_set(), "the owned SaveAs already entered")
        self.result["save_entered_offset_ns"] = self.event_offset()
        self.save_entered.set()
        try:
            return original(*args)
        finally:
            self.result["save_returned_offset_ns"] = self.event_offset()
            self.save_returned.set()

    def wait_for_save_stop(self, control, record, *, signal_ready=False):
        deadline = monotonic() + SAVE_SECONDS
        record["save_wait_started_offset_ns"] = self.event_offset()
        record["wait_calls"] = 0
        record["timed_out_wait_calls"] = 0
        if signal_ready:
            self.ready.set()
        while True:
            if self.save_returned.is_set():
                record["wait_exit_reason"] = "save_returned"
                return False
            if self.cancel.is_set():
                record["wait_exit_reason"] = "cancelled"
                return False
            left_ms = int((deadline - monotonic()) * 1000)
            if left_ms <= 0:
                record["wait_exit_reason"] = "deadline"
                return False
            record["wait_calls"] += 1
            status = control.invoke(93, (U32, U32), 0, min(left_ms, WAIT_SLICE_MS))
            if status == 1:
                record["timed_out_wait_calls"] += 1
                continue
            if status != 0:
                record["wait_exit_reason"] = "engine_error"
                record["wait_hresult"] = f"0x{status & 0xFFFFFFFF:08x}"
                check(status, "WaitForEvent")
            record["wait_exit_reason"] = "debug_event"
            return True

    def doccplu_base(self, symbols, handle):
        from win32process import GetModuleFileNameEx

        module_index, base = U32(), U64()
        symbols.call(14, "locate loaded doccplu", (CSTR, U32, P32, P64),
                     b"doccplu", 0, ctypes.byref(module_index), ctypes.byref(base))
        require(base.value, "doccplu has no live module base")
        module = Path(GetModuleFileNameEx(handle, base.value))
        require(module.name.casefold() == "doccplu.dll", "debugger module base belongs to another image")
        check_amd64_image(module, DOCCPLU_SHA256)
        return base.value

    def arm_breakpoint(self, control, state, offset):
        raw_breakpoint = PTR()
        control.call(72, "create DbgEng software breakpoint", (U32, U32, PPTR),
                     DEBUG_BREAKPOINT_CODE, DEBUG_ANY_ID, ctypes.byref(raw_breakpoint))
        breakpoint = Interface(raw_breakpoint)
        state["breakpoint"] = breakpoint
        breakpoint.call(11, "set pinned software breakpoint offset", (U64,), offset)
        kind, processor = U32(), U32()
        breakpoint.call(4, "read software breakpoint type", (P32, P32), ctypes.byref(kind), ctypes.byref(processor))
        require((kind.value, processor.value) == (DEBUG_BREAKPOINT_CODE, AMD64), "DbgEng did not retain the AMD64 software breakpoint")
        require(breakpoint.value(10, "read software breakpoint offset", U64) == offset, "software breakpoint offset changed")
        break_id = breakpoint.value(3, "read software breakpoint id")
        breakpoint.call(7, "enable software breakpoint", (U32,), DEBUG_BREAKPOINT_ENABLED)
        require(breakpoint.value(6, "read software breakpoint flags") & DEBUG_BREAKPOINT_ENABLED,
                "DbgEng did not retain the software breakpoint enable bit")
        return break_id

    def verify_stop(self, interfaces, handle, *, break_id, base, rva):
        control = interfaces["control"]
        event, engine_pid, engine_tid, seen_id, used = U32(), U32(), U32(), U32(), U32()
        control.call(94, "read the software breakpoint event",
                     (P32, P32, P32, PTR, U32, P32, PTR, U32, P32),
                     ctypes.byref(event), ctypes.byref(engine_pid), ctypes.byref(engine_tid),
                     ctypes.byref(seen_id), ctypes.sizeof(seen_id), ctypes.byref(used), None, 0, None)
        require((event.value, seen_id.value, used.value) == (DEBUG_EVENT_BREAKPOINT, break_id, ctypes.sizeof(seen_id)),
                "the debug stop differs from the expected software breakpoint")
        require(self.save_entered.is_set() and self.event7_seen.is_set() and not self.save_returned.is_set(),
                "software stop was outside the event 7 SaveAs interval")
        require(interfaces["system"].value(27, "software stop OS process id") == self.pid,
                "software stop belongs to another process")
        self.confirm_owned(handle)
        effective = control.value(47, "effective processor at software stop")
        executing = control.value(36, "executing processor at software stop")
        require(effective == executing == AMD64, "the software stop does not expose executed AMD64 context")
        registers = interfaces["registers"]
        rip = registers.value(11, "AMD64 instruction offset", U64)
        require(rip == base + rva, "AMD64 RIP differs from the pinned doccplu instruction")
        require(self.doccplu_base(interfaces["symbols"], handle) == base, "loaded doccplu base changed after arming")
        rsp = registers.value(12, "AMD64 stack offset", U64)
        require(rsp, "the software stop has no AMD64 stack")
        return engine_tid.value, rsp, effective, executing

    def read_document_return(self, interfaces, handle, state, *, base, save_thread, save_stack):
        control = interfaces["control"]
        result = {"rva": DOCUMENT_RETURN_RVA, "armed": False, "sample": None}
        self.result["document_return"] = result
        self.result["stage"] = "remove_aggregate_breakpoint"
        self.remove_software_breakpoint(interfaces, state["breakpoint"], handle)
        state["breakpoint"] = None
        self.result["aggregate_breakpoint_removed"] = True

        self.result["stage"] = "arm_document_return_breakpoint"
        break_id = self.arm_breakpoint(control, state, base + DOCUMENT_RETURN_RVA)
        control.call(50, "continue to document save return", (U32,), DEBUG_STATUS_GO)
        result["armed"] = True
        result["resume_requested_offset_ns"] = self.event_offset()
        self.result["stage"] = "wait_document_return_breakpoint"
        try:
            stopped = self.wait_for_save_stop(control, result)
        finally:
            result["save_wait_ended_offset_ns"] = self.event_offset()
        if not stopped:
            self.result["stage"] = "document_return_unobserved"
            return

        self.result["stage"] = "verify_document_return_stop"
        thread, stack, effective, executing = self.verify_stop(
            interfaces, handle, break_id=break_id, base=base, rva=DOCUMENT_RETURN_RVA,
        )
        require((thread, stack) == (save_thread, save_stack), "document result belongs to a different save frame")
        registers = interfaces["registers"]
        register_index = U32()
        registers.call(5, "locate AMD64 RAX", (CSTR, P32), b"rax", ctypes.byref(register_index))
        value = DebugValue()
        registers.call(6, "read AMD64 RAX at the result test", (U32, PTR), register_index.value, ctypes.byref(value))
        require(value.type == DEBUG_VALUE_INT64, "AMD64 RAX did not provide a typed 64-bit register")
        result["sample"] = {
            "eax": value.integer & 0xFFFFFFFF,
            "same_save_thread_and_stack": True,
            "effective_processor": hex(effective),
            "executing_processor": hex(executing),
        }
        self.result["stage"] = "document_return_observed"

    def _capture(self, client, interfaces, handle, state):
        control = interfaces["control"]
        system = interfaces["system"]
        symbols = interfaces["symbols"]
        data = interfaces["data"]
        deadline = monotonic() + SETUP_SECONDS
        self.result["stage"] = "verify_initial_break_engine_option"
        current = control.value(53, "engine options before the attach request")
        self.result["initial_break_already_enabled"] = bool(current & DEBUG_ENGOPT_INITIAL_BREAK)
        if not current & DEBUG_ENGOPT_INITIAL_BREAK:
            self.result["stage"] = "enable_initial_break_engine_option"
            control.call(54, "enable initial debugger break", (U32,), DEBUG_ENGOPT_INITIAL_BREAK)
        options = control.value(53, "read back engine options before the attach request")
        require(options & DEBUG_ENGOPT_INITIAL_BREAK, "DbgEng did not retain the initial break engine option")
        self.result["initial_break_option_verified"] = True
        self.result["stage"] = "request_owned_attach"
        require(not self.cancel.is_set(), "debugger setup canceled before attachment")
        self.confirm_owned(handle)
        require(not debugger_present(handle), "the owned COM process already has a debugger")
        client.call(12, "attach to owned COM process", (U64, U32, U32), 0, self.pid, DEBUG_ATTACH_DEFAULT)
        state["attach_requested"] = True
        self.result["attach_requested"] = True
        self.result["cleanup_confirmed"] = False

        self.result["stage"] = "wait_initial_stop"
        require(self.wait_event(control, deadline), "no initial debugger stop for the COM-owned process")
        self.result["stage"] = "verify_initial_target"
        require(system.value(27, "initial OS process id") == self.pid, "initial debug stop belongs to a different process")
        self.confirm_owned(handle)
        self.result["initial_stop_verified"] = True

        self.result["stage"] = "set_detach_on_exit"
        client.call(16, "set detach-on-exit on the owned live target", (U32,), DEBUG_PROCESS_DETACH_ON_EXIT)
        self.result["stage"] = "restrict_to_owned_process"
        client.call(16, "restrict debugging to the COM-owned process", (U32,), DEBUG_PROCESS_ONLY_THIS_PROCESS)
        self.result["stage"] = "verify_process_options"
        options = client.value(15, "process options")
        wanted_options = DEBUG_PROCESS_DETACH_ON_EXIT | DEBUG_PROCESS_ONLY_THIS_PROCESS
        require(options & wanted_options == wanted_options, "DbgEng did not retain the required session options")
        require(debugger_present(handle), "Windows did not confirm the debugger for the owned process")
        self.result["process_options"] = options
        self.result["process_options_verified"] = True

        self.result["stage"] = "configure_cleanup_interrupt"
        control.call(6, "set the bounded cleanup interrupt timeout", (U32,), CLEANUP_INTERRUPT_SECONDS)
        require(control.value(5, "read the cleanup interrupt timeout") == CLEANUP_INTERRUPT_SECONDS,
                "DbgEng did not retain the cleanup interrupt timeout")

        self.result["stage"] = "verify_loaded_doccplu"
        base = self.doccplu_base(symbols, handle)

        self.result["stage"] = "select_amd64_context"
        if control.value(47, "initial effective processor") != AMD64:
            control.call(48, "select effective AMD64 processor", (U32,), AMD64)
        require(control.value(47, "effective processor before breakpoint") == AMD64, "debugger cannot select AMD64")
        require(not self.cancel.is_set(), "debugger setup canceled before software breakpoint")
        self.result["stage"] = "arm_software_breakpoint"
        break_id = self.arm_breakpoint(control, state, base + STOP_RVA)
        control.call(50, "continue owned COM process", (U32,), DEBUG_STATUS_GO)
        self.result["armed"] = True
        self.result["resume_requested_offset_ns"] = self.event_offset()
        self.result["stage"] = "wait_saveas_breakpoint"
        try:
            stopped = self.wait_for_save_stop(control, self.result, signal_ready=True)
        finally:
            self.result["save_wait_ended_offset_ns"] = self.event_offset()
        require(stopped, f"software breakpoint wait ended with {self.result['wait_exit_reason']}")
        self.result["stage"] = "verify_software_stop"
        thread, rsp, effective, executing = self.verify_stop(
            interfaces, handle, break_id=break_id, base=base, rva=STOP_RVA,
        )
        self.result["stage"] = "read_listener_aggregate"
        aggregate, count = U32(), U32()
        data.call(6, "read four-byte listener aggregate", (U64, PTR, U32, P32),
                  rsp + AGGREGATE_STACK_OFFSET, ctypes.byref(aggregate), SAMPLE_BYTES, ctypes.byref(count))
        require(count.value == SAMPLE_BYTES, "DbgEng did not return the full four-byte aggregate")
        self.result["sample"] = {
            "aggregate": aggregate.value,
            "rva": STOP_RVA,
            "effective_processor": hex(effective),
            "executing_processor": hex(executing),
            "bytes_read": count.value,
            "event7_seen": True,
        }
        self.result["stage"] = "aggregate_observed"
        self.read_document_return(interfaces, handle, state, base=base, save_thread=thread, save_stack=rsp)

    def remove_software_breakpoint(self, interfaces, breakpoint, handle):
        control = interfaces["control"]
        system = interfaces["system"]
        self.confirm_owned(handle)
        require(debugger_present(handle), "Windows reports no debugger before removing the software breakpoint")
        status = control.value(49, "execution status before software breakpoint removal")
        if status != DEBUG_STATUS_BREAK:
            control.call(4, "request a cleanup stop on the owned process", (U32,), DEBUG_INTERRUPT_ACTIVE)
            self.result["cleanup_interrupt_requested"] = True
            require(self.wait_event(control, monotonic() + CLEANUP_STOP_SECONDS, honor_cancel=False),
                    "software breakpoint cleanup stop timed out")
        require(system.value(27, "cleanup stop OS process id") == self.pid, "cleanup stop belongs to another process")
        self.confirm_owned(handle)
        require(control.value(49, "execution status at software breakpoint removal") == DEBUG_STATUS_BREAK,
                "owned process has not stopped for software breakpoint removal")
        control.call(73, "remove software breakpoint", (PTR,), breakpoint.pointer)

    def _cleanup(self, client, interfaces, state, handle):
        errors = []
        breakpoint = state["breakpoint"]
        if breakpoint is not None:
            try:
                self.remove_software_breakpoint(interfaces, breakpoint, handle)
                self.result["breakpoint_removed"] = True
            except Exception as error:
                errors.append(str(error))
                self.result["breakpoint_removed"] = False
        if state["attach_requested"]:
            try:
                client.call(25, "detach from the owned COM process")
                self.result["detach_method"] = "DetachProcesses"
            except Exception as error:
                errors.append(str(error))
                try:
                    client.call(26, "end session and detach", (U32,), DEBUG_END_ACTIVE_DETACH)
                    self.result["detach_method"] = "EndSession"
                except Exception as fallback_error:
                    errors.append(str(fallback_error))
        for interface in (*reversed(tuple(interfaces.values())), client):
            try:
                interface.release()
            except Exception as error:
                errors.append(str(error))
        if state["attach_requested"]:
            try:
                status = self.sw.WaitForSingleObject(handle, 0)
                if status == self.sw.WAIT_OBJECT_0:
                    self.result["owned_process_exited_after_cleanup"] = True
                    self.result["cleanup_confirmed"] = True
                else:
                    require(status == self.sw.WAIT_TIMEOUT, "could not verify the owned process after detach")
                    present = debugger_present(handle)
                    self.result["owned_process_debugger_present_after_cleanup"] = present
                    self.result["cleanup_confirmed"] = not present
                    if present:
                        errors.append("Windows still reports a debugger on the owned COM process")
            except Exception as error:
                errors.append(str(error))
        if errors:
            self.result["cleanup_diagnostics"] = errors

    def _run(self):
        handle = None
        initialized = False
        try:
            from win32api import OpenProcess
            from win32process import GetModuleFileNameEx

            self.sw.pythoncom.CoInitialize()
            initialized = True
            handle = OpenProcess(0x00100410, False, self.pid)
            self.confirm_owned(handle)
            executable = Path(GetModuleFileNameEx(handle, None))
            require(executable.name.casefold() == "sldworks.exe", "owned COM process executable is not sldworks.exe")
            check_amd64_image(executable, self.identity["sha256"])

            self.result["stage"] = "load_dbgeng"
            with os.add_dll_directory(str(self.engine.parent)):
                library = ctypes.WinDLL(str(self.engine), winmode=0xD00, use_last_error=True)
                pointer = PTR()
                create = library.DebugCreate
                create.argtypes = (PTR, PPTR)
                create.restype = HRESULT
                ident = guid("client")
                check(create(ctypes.byref(ident), ctypes.byref(pointer)), "DebugCreate")
                client = Interface(pointer)
                interfaces = {}
                state = {"attach_requested": False, "breakpoint": None}
                try:
                    self.result["stage"] = "query_dbgeng_interfaces"
                    for name in ("control", "data", "registers", "symbols", "system"):
                        interfaces[name] = client.query(name)
                    self._capture(client, interfaces, handle, state)
                finally:
                    self._cleanup(client, interfaces, state, handle)
        except Exception as error:
            self.result["failure_stage"] = self.result["stage"]
            self.result["failure"] = str(error)
        finally:
            try:
                if handle is not None:
                    handle.Close()
                if initialized:
                    self.sw.pythoncom.CoUninitialize()
            finally:
                self.ready.set()

    def finish(self):
        self.cancel.set()
        self.thread.join(JOIN_SECONDS)
        if self.thread.is_alive():
            return {**self.result, "cleanup_confirmed": False, "sample": None,
                    "failure_stage": self.result["stage"],
                    "failure": "debugger worker did not finish within its cleanup deadline"}
        return dict(self.result)
