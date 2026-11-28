from __future__ import annotations

import ctypes

import DrawingSaveAggregateDbgEng as engine


DISPLAY_ONLY_RVA = 0x1DD1B
QUICK_VIEW_ONLY_RVA = 0x1DD2B
THIRD_PARTY_DISPATCH_RVA = 0x1DFB5
PREVIEW_STOPS = (
    {"module": "doccplu.dll", "instruction_rva": DISPLAY_ONLY_RVA, "sample": "signed_eax", "bytes": 4},
    {"module": "doccplu.dll", "instruction_rva": QUICK_VIEW_ONLY_RVA, "sample": "signed_eax", "bytes": 4},
    {"module": "doccplu.dll", "instruction_rva": THIRD_PARTY_DISPATCH_RVA, "sample": "entry"},
)


class PreviewGateTrace(engine.SaveAggregateTrace):
    def read_document_return(self, interfaces, handle, state, *, base, save_thread, save_stack):
        path = {}
        self.result["preview_path"] = path
        stack = self.observe_stage(
            interfaces, handle, state, base=base, save_thread=save_thread, save_stack=save_stack,
            path=path, name="display_list_only", rva=DISPLAY_ONLY_RVA, storage_stack=None, read_eax=True,
        )
        if stack is None or path["display_list_only"]["sample"]["eax_signed"]:
            return

        quick_stack = self.observe_stage(
            interfaces, handle, state, base=base, save_thread=save_thread, save_stack=save_stack,
            path=path, name="quick_view_only", rva=QUICK_VIEW_ONLY_RVA, storage_stack=stack, read_eax=True,
        )
        if quick_stack is None or path["quick_view_only"]["sample"]["eax_signed"]:
            return

        self.observe_stage(
            interfaces, handle, state, base=base, save_thread=save_thread, save_stack=save_stack,
            path=path, name="third_party_dispatch", rva=THIRD_PARTY_DISPATCH_RVA, storage_stack=stack, read_eax=False,
        )

    def observe_stage(self, interfaces, handle, state, *, base, save_thread, save_stack, path,
                      name, rva, storage_stack, read_eax):
        control = interfaces["control"]
        result = {"rva": rva, "prior_breakpoint_removed": False, "armed": False, "sample": None}
        path[name] = result
        self.result["stage"] = f"replace_breakpoint_for_{name}"
        self.remove_software_breakpoint(interfaces, state["breakpoint"], handle)
        state["breakpoint"] = None
        result["prior_breakpoint_removed"] = True
        break_id = self.arm_breakpoint(control, state, base + rva)
        result["armed"] = True
        result["resume_requested_offset_ns"] = self.event_offset()
        control.call(50, f"continue to {name}", (engine.U32,), engine.DEBUG_STATUS_GO)
        self.result["stage"] = f"wait_{name}"
        try:
            stopped = self.wait_for_save_stop(control, result)
        finally:
            result["save_wait_ended_offset_ns"] = self.event_offset()
        if not stopped:
            self.result["stage"] = f"{name}_unobserved"
            return None

        self.result["stage"] = f"verify_{name}"
        thread, stack, effective, executing = self.verify_stop(
            interfaces, handle, break_id=break_id, base=base, rva=rva,
        )
        engine.require(thread == save_thread and stack < save_stack,
                       f"{name} is outside the originating save thread or nested frame")
        if storage_stack is not None:
            engine.require(stack == storage_stack, f"{name} is outside the first getter's storage frame")
        sample = {
            "same_save_thread": True,
            "nested_save_frame": True,
            "storage_frame_relation": "established" if storage_stack is None else "same_as_first_getter",
            "effective_processor": hex(effective),
            "executing_processor": hex(executing),
        }
        if read_eax:
            registers = interfaces["registers"]
            register_index = engine.U32()
            registers.call(5, "locate AMD64 RAX", (engine.CSTR, engine.P32), b"rax", ctypes.byref(register_index))
            value = engine.DebugValue()
            registers.call(6, f"read AMD64 RAX at {name}", (engine.U32, engine.PTR),
                           register_index.value, ctypes.byref(value))
            engine.require(value.type == engine.DEBUG_VALUE_INT64, "AMD64 RAX lacks a typed 64-bit register")
            eax_bits = value.integer & 0xFFFFFFFF
            sample.update(eax_signed=ctypes.c_int32(eax_bits).value, eax_hex=f"0x{eax_bits:08x}")
        result["sample"] = sample
        self.result["stage"] = f"{name}_observed"
        return stack
