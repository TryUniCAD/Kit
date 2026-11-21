from hashlib import sha256
from pathlib import Path

from OwnedMessengerMemory import OwnedProcess, require


UI_SHA = "3948ce26833d053f9d4d0a8b4f8b1b9ed90662f4324aca2f4d002c7f3166edbf"
CORE_SHA = "eb0a385b396cd0abc03fd92afae26b9df8cab588a737a3b10c806cfe46282249"
PREDICATE_RVA = 0x1727D0
PREDICATE_SHA = "9d52413d08f660c9ff98255aa9958a2324e509449f5eddaf8774548ab6bfbad4"


class OwnedQueueProcess(OwnedProcess):
    def snapshot(self):
        result = super().snapshot()
        target = result["target_owner"]
        table_owner = result["vtable_owner"]
        require(target["module"]["name"].casefold() == "sldgraphicsuiu.dll"
                and target["module"]["sha256"] == UI_SHA and target["rva"] == "0xd1e40"
                and table_owner["module"]["sha256"] == UI_SHA and table_owner["rva"] == "0x166c40",
                "registered graphics messenger owner differs from the measured source")
        ui_base = int(target["module"]["base"], 0)
        require(int(result["messenger"], 0) == ui_base + 0x1EBE38,
                "active messenger is not the source-bound installed object")
        modules = self.modules()
        core = [row for row in modules if Path(row["path"]).name.casefold() == "sldgfxu.dll"]
        require(len(core) == 1, "actual graphics queue module is absent or duplicated")
        info, _, _, _ = self.identity_for(core[0])
        require(info["sha256"] == CORE_SHA and info.get("version") == [34, 5, 2, 604]
                and info["file_bytes"] == 2736728, "wrong exact graphics queue image")
        live = self.read(core[0]["base"] + PREDICATE_RVA, 9)
        require(sha256(live).hexdigest() == PREDICATE_SHA,
                "loaded clear-all predicate differs from the pinned complete leaf")
        messenger = int(result["messenger"], 0)
        global_address = int(result["global_address"], 0)
        expected_table = int(result["vtable"], 0)
        queue = {"handler_offset": "0x8", "pending_offset": "0x28",
                 "predicate_module": info, "predicate_rva": hex(PREDICATE_RVA),
                 "predicate_live_sha256": sha256(live).hexdigest(),
                 "atomic_snapshot": False, "actual_invocation_observed": False}
        self.partial["clear_queue"] = queue
        for attempt in range(1, 4):
            pending = 0
            handler = self.word(messenger + 8)
            queue.update(handler=hex(handler), handler_present=bool(handler), attempts=attempt)
            if handler:
                require(handler == ui_base + 0x1EBDE0,
                        "message handler is not the source-bound installed object")
                handler_table = self.word(handler)
                queue["handler_vtable"] = hex(handler_table)
                require(handler_table == ui_base + 0x166B68,
                        "message handler concrete vtable differs")
                pending = self.word(handler + 0x28)
                queue.update(pending_clear_all=hex(pending), has_clear_all_message=bool(pending),
                             handler_rva="0x1ebde0", handler_vtable_rva="0x166b68")
                stable = (self.word(handler + 0x28) == pending and self.word(handler) == handler_table)
            else:
                queue.update(handler_vtable=None, pending_clear_all=None, has_clear_all_message=None,
                             handler_rva=None, handler_vtable_rva=None)
                stable = True
            stable = stable and self.word(messenger + 8) == handler
            stable = stable and self.word(global_address) == messenger and self.word(messenger) == expected_table
            if stable:
                queue.update(pointer_chain_stable_during_reads=True,
                             callback_statically_returns_at_null_handler=not bool(handler),
                             callback_statically_returns_at_pending_gate=bool(handler and pending))
                break
        else:
            raise RuntimeError("message queue changed during three bounded snapshots")
        result["clear_queue"] = queue
        result["rpm_calls_so_far"] = self.read_count
        result["rpm_bytes_so_far"] = self.read_bytes
        self.check()
        return result
