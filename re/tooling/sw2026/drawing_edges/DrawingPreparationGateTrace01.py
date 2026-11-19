from __future__ import annotations

import ctypes
from hashlib import sha256
from pathlib import Path
from struct import unpack_from

import DrawingSaveAggregateDbgEng as engine
import DrawingSavePropertiesGateDbgEng as restoration
from DrawingEdgeCacheTrace01 import EdgeCacheTrace, register64

MODULE_SHA256 = "61c8481374431866f97416ce5109329f9c38e7e85b56a9f95d41bdf3122cdc47"
GATE_RVA = 0x347BCE


def original_byte(path):
    data = path.read_bytes()
    engine.require(
        sha256(data).hexdigest() == MODULE_SHA256, "original drawing module differs"
    )
    pe = unpack_from("<I", data, 0x3C)[0]
    table = pe + 24 + unpack_from("<H", data, pe + 20)[0]
    for index in range(unpack_from("<H", data, pe + 6)[0]):
        _, rva, size, raw = unpack_from("<IIII", data, table + 40 * index + 8)
        if rva <= GATE_RVA < rva + size:
            return data[raw + GATE_RVA - rva : raw + GATE_RVA - rva + 1]
    raise ValueError("the fixed preparation instruction has no original bytes")


def read_i32(handle, address):
    raw = b"".join(
        restoration.owned_process_byte(handle, address + offset) for offset in range(4)
    )
    return unpack_from("<i", raw)[0]


class PreparationGateTrace(EdgeCacheTrace):
    def __init__(self, sw, debugger_engine, identity, *, expected_view_id):
        super().__init__(sw, debugger_engine, identity)
        engine.require(
            type(expected_view_id) is int and expected_view_id > 0,
            "an exact disclosed view owner is required",
        )
        self.expected_view_id = expected_view_id
        self.result["trace_scope"] = (
            "actual disclosed model-view preparation decision before detailing bucket routing; no cache or edge-ID observation"
        )
        self.result["preparation_gate"] = {
            "rva": GATE_RVA,
            "state": "unobserved",
            "sample": None,
            "other_view_ids": [],
        }

    def ui_base(self, symbols, handle):
        from win32process import GetModuleFileNameEx

        index, base = engine.U32(), engine.U64()
        symbols.call(
            14,
            "locate the pinned drawing module",
            (engine.CSTR, engine.U32, engine.P32, engine.P64),
            b"slddrwu",
            0,
            ctypes.byref(index),
            ctypes.byref(base),
        )
        engine.require(base.value != 0, "owned drawing module is not loaded")
        path = Path(GetModuleFileNameEx(handle, base.value))
        engine.require(
            path.name.casefold() == "slddrwu.dll", "loaded drawing module name differs"
        )
        engine.check_amd64_image(path, MODULE_SHA256)
        engine.require(
            self._module_base in (None, base.value), "owned drawing module base changed"
        )
        self._module_base, self._module_path, self._process_handle = (
            base.value,
            path,
            handle,
        )
        return base.value

    def verify_owned_module(self, handle):
        from win32process import GetModuleFileNameEx

        self.confirm_owned(handle)
        engine.require(
            self._module_base is not None and self._module_path is not None,
            "owned drawing module is unbound",
        )
        path = Path(GetModuleFileNameEx(handle, self._module_base))
        engine.require(
            path == self._module_path and path.name.casefold() == "slddrwu.dll",
            "owned drawing module identity changed",
        )
        engine.check_amd64_image(path, MODULE_SHA256)

    def arm_breakpoint(self, control, state, offset):
        engine.require(
            self._module_base is not None and offset == self._module_base + GATE_RVA,
            "only the fixed preparation decision is allowed",
        )
        self.verify_owned_module(self._process_handle)
        original = original_byte(self._module_path)
        before = restoration.owned_process_byte(self._process_handle, offset)
        engine.require(before == original, "owned instruction differs before arming")
        row = {
            "rva": GATE_RVA,
            "bytes": 1,
            "original_sha256": sha256(original).hexdigest(),
            "before_arm_sha256": sha256(before).hexdigest(),
            "before_arm_matches_original": True,
            "armed": False,
            "remove_call_succeeded": False,
        }
        self._sites.append(row)
        self._active_site = row
        identifier = engine.SaveAggregateTrace.arm_breakpoint(
            self, control, state, offset
        )
        row["armed"] = True
        return identifier

    def snapshot_sites(self, handle, phase):
        self.verify_owned_module(handle)
        for row in self._sites:
            expected = original_byte(self._module_path)
            actual = restoration.owned_process_byte(
                handle, self._module_base + row["rva"]
            )
            row[phase] = {
                "bytes_read": len(actual),
                "sha256": sha256(actual).hexdigest(),
                "matches_original": actual == expected,
            }

    def _capture(self, client, interfaces, handle, state):
        control, system = interfaces["control"], interfaces["system"]
        deadline = engine.monotonic() + engine.SETUP_SECONDS
        self.result["stage"] = "verify_initial_break_engine_option"
        current = control.value(53, "read engine initial-break options")
        self.result["initial_break_already_enabled"] = bool(
            current & engine.DEBUG_ENGOPT_INITIAL_BREAK
        )
        if not current & engine.DEBUG_ENGOPT_INITIAL_BREAK:
            control.call(
                54,
                "enable the owned initial stop",
                (engine.U32,),
                engine.DEBUG_ENGOPT_INITIAL_BREAK,
            )
        engine.require(
            control.value(53, "verify engine initial-break options")
            & engine.DEBUG_ENGOPT_INITIAL_BREAK,
            "initial stop option not retained",
        )
        self.result["initial_break_option_verified"] = True
        self.result["stage"] = "request_owned_attach"
        engine.require(
            not self.cancel.is_set(),
            "owned preparation trace canceled before attachment",
        )
        self.confirm_owned(handle)
        engine.require(
            not engine.debugger_present(handle), "owned process already has a debugger"
        )
        client.call(
            12,
            "attach only the exact COM-owned process",
            (engine.U64, engine.U32, engine.U32),
            0,
            self.pid,
            engine.DEBUG_ATTACH_DEFAULT,
        )
        state["attach_requested"] = self.result["attach_requested"] = True
        self.result["cleanup_confirmed"] = False
        self.result["stage"] = "wait_initial_stop"
        engine.require(
            self.wait_event(control, deadline), "owned initial stop was not delivered"
        )
        engine.require(
            system.value(27, "verify initial owned OS PID") == self.pid,
            "initial stop is not owned",
        )
        self.confirm_owned(handle)
        self.result["initial_stop_verified"] = True
        self._engine_process_id = system.value(
            7, "capture exact initial engine process id"
        )
        client.call(
            16,
            "set owned target detach-on-exit",
            (engine.U32,),
            engine.DEBUG_PROCESS_DETACH_ON_EXIT,
        )
        client.call(
            16,
            "restrict debugging to the owned process",
            (engine.U32,),
            engine.DEBUG_PROCESS_ONLY_THIS_PROCESS,
        )
        options = client.value(15, "verify owned target process options")
        wanted = (
            engine.DEBUG_PROCESS_DETACH_ON_EXIT | engine.DEBUG_PROCESS_ONLY_THIS_PROCESS
        )
        engine.require(
            options & wanted == wanted and engine.debugger_present(handle),
            "owned process options were not retained",
        )
        self.result["process_options"] = options
        self.result["process_options_verified"] = True
        control.call(
            6,
            "set bounded owned cleanup interrupt",
            (engine.U32,),
            engine.CLEANUP_INTERRUPT_SECONDS,
        )
        engine.require(
            control.value(5, "verify cleanup interrupt timeout")
            == engine.CLEANUP_INTERRUPT_SECONDS,
            "cleanup timeout not retained",
        )
        base = self.ui_base(interfaces["symbols"], handle)
        if control.value(47, "initial effective CPU") != engine.AMD64:
            control.call(
                48, "select AMD64 for the owned session", (engine.U32,), engine.AMD64
            )
        engine.require(
            control.value(47, "verify selected AMD64 CPU") == engine.AMD64,
            "AMD64 context unavailable",
        )
        engine.require(
            not self.cancel.is_set(), "owned preparation trace canceled before arming"
        )
        row = self.result["preparation_gate"]
        self.result["stage"] = "arm_preparation_gate"
        identifier = self.arm_breakpoint(control, state, base + GATE_RVA)
        self.result["armed"] = True
        for ordinal in range(32):
            row["resume_requested_offset_ns"] = self.event_offset()
            control.call(
                50,
                "continue to the fixed preparation decision",
                (engine.U32,),
                engine.DEBUG_STATUS_GO,
            )
            self.result["stage"] = "wait_preparation_gate"
            stopped = self.wait_for_save_stop(control, row, signal_ready=ordinal == 0)
            row["save_wait_ended_offset_ns"] = self.event_offset()
            if not stopped:
                row["state"] = (
                    "unobserved_after_completed_save"
                    if row.get("wait_exit_reason") == "save_returned"
                    else "unqualified"
                )
                self.result["route"] = "preparation_gate_unobserved"
                return
            self.verify_stop(
                interfaces, handle, break_id=identifier, base=base, rva=GATE_RVA
            )
            registers = interfaces["registers"]
            view = register64(registers, "rdi")
            frame = register64(registers, "rbp")
            engine.require(view and frame, "preparation view or stack owner is null")
            view_id = read_i32(handle, view + 8)
            if view_id != self.expected_view_id:
                row["other_view_ids"].append(view_id)
                continue
            values = {
                name: register64(registers, name) & 0xFFFFFFFF
                for name in ("rbx", "r14", "r15", "r13")
            }
            argument = read_i32(handle, frame + 0x2E8)
            engine.require(
                values["r14"] in (0, 1) and values["r15"] in (0, 0x40),
                "typed preparation decision registers differ from source",
            )
            row["sample"] = {
                "view_feature_id_i32": view_id,
                "save_model_data_i32": ctypes.c_int32(values["rbx"]).value,
                "eligible_view_i32": values["r14"],
                "view_f614_mask40_u32": values["r15"],
                "detail_f224_i32": ctypes.c_int32(values["r13"]).value,
                "native_argument6_i32": argument,
                "next_detailing_branch_allowed": bool(values["r14"] and argument),
                "event7_seen": False,
            }
            row["sample_offset_ns"] = self.event_offset()
            row["state"] = "observed"
            self.result["route"] = "preparation_gate_observed"
            self.result["stage"] = "preparation_gate_observed"
            return
        raise ValueError(
            "the exact disclosed model view was not selected within the bounded preparation stops"
        )


def qualified(trace):
    cleanup = trace.get("breakpoint_cleanup") or {}
    clean = bool(
        trace.get("armed")
        and trace.get("failure") is None
        and trace.get("initial_stop_verified")
        and trace.get("initial_break_option_verified")
        and trace.get("process_options_verified")
        and trace.get("cleanup_confirmed")
        and cleanup.get("qualified")
        and cleanup.get("all_sites_original_after_detach")
        and trace.get("owned_process_debugger_present_after_cleanup") is False
    )
    row = trace.get("preparation_gate") or {}
    clock = [
        trace.get("save_entered_offset_ns"),
        row.get("sample_offset_ns"),
        trace.get("event7_offset_ns"),
        trace.get("save_returned_offset_ns"),
    ]
    ordered = None not in clock and clock == sorted(clock)
    observed = bool(clean and ordered and row.get("state") == "observed")
    return {
        "observer_completed_cleanly": clean,
        "preparation_gate_observed": observed,
        "pre_event7_clock_order_verified": ordered,
        "route": trace.get("route", "unqualified"),
        "selected_edge_cache_lookup_observed": False,
        "fallback_asserted": False,
        "native_acceptance": False,
    }
