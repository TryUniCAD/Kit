from __future__ import annotations

from hashlib import sha256

import DrawingSavePropertiesGateDbgEng as restoration


engine = restoration.engine
BASE_TRACE = restoration.preview.PreviewGateTrace.__base__
SDK_HEADER_SHA256 = restoration.SDK_HEADER_SHA256
PROPERTY_CALL_RVA = 0x1DF56
AFTER_PROPERTIES_RVA = 0x1DF5B
PROPERTIES_STOPS = (
    {"module": "doccplu.dll", "instruction_rva": PROPERTY_CALL_RVA, "sample": "entry"},
    {"module": "doccplu.dll", "instruction_rva": AFTER_PROPERTIES_RVA, "sample": "entry"},
)
ALLOWED_RVAS = frozenset((engine.STOP_RVA, PROPERTY_CALL_RVA, AFTER_PROPERTIES_RVA))


class PropertiesEntryTrace(restoration.PropertiesGateTrace):
    def arm_breakpoint(self, control, state, offset):
        engine.require(self._module_base is not None, "owned module base is unbound")
        rva = offset - self._module_base
        engine.require(rva in ALLOWED_RVAS, "software breakpoint RVA is outside this fixed entry trial")
        handle = self._process_handle
        self.verify_owned_module(handle)
        original = restoration.original_image_byte(self._module_path, rva)
        before = restoration.owned_process_byte(handle, offset)
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
        identifier = BASE_TRACE.arm_breakpoint(self, control, state, offset)
        record["armed"] = True
        return identifier

    def read_document_return(self, interfaces, handle, state, *, base, save_thread, save_stack):
        path = {}
        self.result["properties_entry_path"] = path
        stack = self.observe_stage(
            interfaces, handle, state, base=base, save_thread=save_thread, save_stack=save_stack,
            path=path, name="document_properties_call", rva=PROPERTY_CALL_RVA,
            storage_stack=None, read_eax=False,
        )
        if stack is not None:
            self.observe_stage(
                interfaces, handle, state, base=base, save_thread=save_thread, save_stack=save_stack,
                path=path, name="after_document_properties", rva=AFTER_PROPERTIES_RVA,
                storage_stack=stack, read_eax=False,
            )
