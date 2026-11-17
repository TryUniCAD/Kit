from __future__ import annotations

import ctypes

import DrawingSaveAggregateDbgEng as engine


SAVE_DOC_ENTRY_RVA = 0x1B810
ROOT_VALIDITY_RVA = 0x1DA03
STORAGE_STOPS = (
    {"module": "doccplu.dll", "instruction_rva": SAVE_DOC_ENTRY_RVA, "sample": "entry"},
    {"module": "doccplu.dll", "instruction_rva": ROOT_VALIDITY_RVA, "sample": "signed_eax", "bytes": 4},
)


class StorageGateTrace(engine.SaveAggregateTrace):
    def read_document_return(self, interfaces, handle, state, *, base, save_thread, save_stack):
        path = {}
        self.result["storage_path"] = path
        save_doc_stack = self.observe_stage(
            interfaces, handle, state, base=base, save_thread=save_thread, enclosing_stack=save_stack,
            path=path, name="save_doc_entry", rva=SAVE_DOC_ENTRY_RVA,
        )
        if save_doc_stack is not None:
            self.observe_stage(
                interfaces, handle, state, base=base, save_thread=save_thread, enclosing_stack=save_doc_stack,
                path=path, name="storage_root_validity", rva=ROOT_VALIDITY_RVA,
            )

    def observe_stage(self, interfaces, handle, state, *, base, save_thread, enclosing_stack, path, name, rva):
        control = interfaces["control"]
        stage = {"rva": rva, "prior_breakpoint_removed": False, "armed": False, "sample": None}
        path[name] = stage
        self.result["stage"] = f"replace_breakpoint_for_{name}"
        self.remove_software_breakpoint(interfaces, state["breakpoint"], handle)
        state["breakpoint"] = None
        stage["prior_breakpoint_removed"] = True
        break_id = self.arm_breakpoint(control, state, base + rva)
        stage["armed"] = True
        stage["resume_requested_offset_ns"] = self.event_offset()
        control.call(50, f"continue to {name}", (engine.U32,), engine.DEBUG_STATUS_GO)
        self.result["stage"] = f"wait_{name}"
        try:
            stopped = self.wait_for_save_stop(control, stage)
        finally:
            stage["save_wait_ended_offset_ns"] = self.event_offset()
        if not stopped:
            self.result["stage"] = f"{name}_unobserved"
            return None

        self.result["stage"] = f"verify_{name}"
        thread, stack, effective, executing = self.verify_stop(
            interfaces, handle, break_id=break_id, base=base, rva=rva,
        )
        engine.require(thread == save_thread and stack < enclosing_stack,
                       f"{name} did not occur on the same save thread in a nested frame")
        sample = {
            "same_save_thread": True,
            "nested_save_frame": True,
            "effective_processor": hex(effective),
            "executing_processor": hex(executing),
        }
        if rva == ROOT_VALIDITY_RVA:
            registers = interfaces["registers"]
            register_index = engine.U32()
            registers.call(5, "locate AMD64 RAX", (engine.CSTR, engine.P32), b"rax", ctypes.byref(register_index))
            value = engine.DebugValue()
            registers.call(6, "read AMD64 RAX at the root validity test", (engine.U32, engine.PTR),
                           register_index.value, ctypes.byref(value))
            engine.require(value.type == engine.DEBUG_VALUE_INT64, "AMD64 RAX lacks the typed 64-bit register")
            eax_bits = value.integer & 0xFFFFFFFF
            sample.update(eax_signed=ctypes.c_int32(eax_bits).value, eax_hex=f"0x{eax_bits:08x}")
        stage["sample"] = sample
        self.result["stage"] = f"{name}_observed"
        return stack
