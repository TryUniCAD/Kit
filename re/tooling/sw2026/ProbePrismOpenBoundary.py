from argparse import ArgumentParser
from ctypes import byref, create_string_buffer, sizeof
from hashlib import sha256
from json import dumps
from pathlib import Path
from struct import unpack
from threading import Event
from time import monotonic, sleep

from win32process import GetModuleFileNameEx

import DrawingSaveAggregateDbgEng as debug
from OracleIdentity import application_identity
import Swapp


APP_SHA256 = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
ENGINE_SHA256 = "5a2a515f6263c66b0323d8707abf4b64511a9a34f1f1d3fb1f3c4c17f0bf9cad"
MODULES = {
    "sldgciParau": (0x32f70000, "96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce"),
    "sldappu": (0x453f0000, "50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf"),
    "sldmodu": (0x4b140000, "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"),
}
SITES = (
    ("receive_call", "sldgciParau", 0x3305aea7),
    ("receive_return", "sldgciParau", 0x3305aeac),
    ("receive_after_status_store", "sldgciParau", 0x3305aeb0),
    ("receive_after_wrap", "sldgciParau", 0x3305aec5),
    ("ask_bodies_return", "sldgciParau", 0x3305af1c),
    ("model_body_inventory", "sldmodu", 0x4c23edeb),
    ("model_body_replace_return", "sldmodu", 0x4c23f182),
    ("api_error_128", "sldappu", 0x458a1760),
)


CALLERS = {
    "slduiu": (0x48ea0000, "025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7"),
    "sldprtu": (0x332a0000, "54c079c8bbbe13582d062787c07a13f91d91f2d7972715e5d647bb8a1802d494"),
}


def register(registers, name):
    index = debug.U32()
    registers.call(5, "locate AMD64 register", (debug.CSTR, debug.P32), name.encode("ascii"), byref(index))
    raw = create_string_buffer(32)
    registers.call(6, "read AMD64 register", (debug.U32, debug.PTR), index.value, byref(raw))
    return unpack("<Q", raw.raw[:8])[0]


def read_int(data, address, size, *, signed=False):
    raw = create_string_buffer(size)
    done = debug.U32()
    data.call(6, "read one scoped operand", (debug.U64, debug.PTR, debug.U32, debug.P32),
              address, byref(raw), size, byref(done))
    debug.require(done.value == size, "short debugger read")
    return int.from_bytes(raw.raw, "little", signed=signed)


class ColdAdmissionTrace(debug.SaveAggregateTrace):
    def __init__(self, engine, identity, terminal_site, resume):
        super().__init__(Swapp, engine, identity)
        self.opening = Event()
        self.breakpoints = []
        self.terminal_site = terminal_site
        self.resume = resume
        self.result["hits"] = []
        self.result["breakpoint_kind"] = "amd64_execute" if terminal_site != "attach_only" else None

    def _attach_owned(self, client, control, system, handle, state):
        self.result["stage"] = "prepare debugger"
        if not control.value(53, "engine options") & debug.DEBUG_ENGOPT_INITIAL_BREAK:
            control.call(54, "enable initial break", (debug.U32,), debug.DEBUG_ENGOPT_INITIAL_BREAK)
        debug.require(control.value(53, "engine options") & debug.DEBUG_ENGOPT_INITIAL_BREAK,
                      "debugger initial break option is clear")
        self.confirm_owned(handle)
        debug.require(not debug.debugger_present(handle), "the owned CAD process already has a debugger")
        client.call(12, "attach to owned COM process", (debug.U64, debug.U32, debug.U32),
                    0, self.pid, debug.DEBUG_ATTACH_DEFAULT)
        state["attach_requested"] = True
        self.result["attach_requested"] = True
        self.result["cleanup_confirmed"] = False
        self.result["stage"] = "initial debugger stop"
        debug.require(self.wait_event(control, monotonic() + 20), "no initial debugger stop")
        debug.require(system.value(27, "initial OS process id") == self.pid, "unexpected debug target")
        self.confirm_owned(handle)
        self.result["initial_stop_verified"] = True
        for flag in (debug.DEBUG_PROCESS_DETACH_ON_EXIT, debug.DEBUG_PROCESS_ONLY_THIS_PROCESS):
            client.call(16, "restrict debug session", (debug.U32,), flag)
        flags = debug.DEBUG_PROCESS_DETACH_ON_EXIT | debug.DEBUG_PROCESS_ONLY_THIS_PROCESS
        debug.require(client.value(15, "debug process flags") & flags == flags, "unsafe debugger process options")
        self.result["process_options_verified"] = True
        if control.value(47, "effective processor") != debug.AMD64:
            control.call(48, "select AMD64", (debug.U32,), debug.AMD64)
        debug.require(control.value(47, "effective processor") == debug.AMD64, "AMD64 registers unavailable")

    def _arm(self, control, symbols, handle):
        self.result["stage"] = "verify CAD module identities"
        bases = {}
        modules = {module for name, module, _ in SITES if name == self.terminal_site}
        for module in sorted(modules):
            _, digest = MODULES[module]
            index, base = debug.U32(), debug.U64()
            symbols.call(14, "locate loaded module", (debug.CSTR, debug.U32, debug.P32, debug.P64),
                         module.encode("ascii"), 0, byref(index), byref(base))
            debug.require(base.value, "loaded module base is null")
            source = Path(GetModuleFileNameEx(handle, base.value))
            debug.require(source.stem.casefold() == module.casefold(), "loaded module name differs")
            debug.check_amd64_image(source, digest)
            bases[module] = base.value
        self.result["stage"] = "arm selected restore sites"
        site_ids = {}
        if self.terminal_site == "attach_only":
            return site_ids
        for name, module, address in SITES:
            if name != self.terminal_site:
                continue
            offset = bases[module] + address - MODULES[module][0]
            raw = debug.PTR()
            control.call(72, "create hardware breakpoint", (debug.U32, debug.U32, debug.PPTR),
                         debug.DEBUG_BREAKPOINT_DATA, debug.DEBUG_ANY_ID, byref(raw))
            breakpoint = debug.Interface(raw)
            self.breakpoints.append(breakpoint)
            breakpoint.call(11, "bind exact restored-body instruction", (debug.U64,), offset)
            breakpoint.call(13, "select AMD64 execution only", (debug.U32, debug.U32), 1, debug.DEBUG_BREAK_EXECUTE)
            breakpoint.call(7, "enable owned breakpoint", (debug.U32,), debug.DEBUG_BREAKPOINT_ENABLED)
            site_ids[breakpoint.value(3, "breakpoint identity")] = (name, offset, address)
        return site_ids

    def _caller(self, symbols, handle, address):
        index, base = debug.U32(), debug.U64()
        symbols.call(15, "locate actual caller image", (debug.U64, debug.U32, debug.P32, debug.P64),
                     address, 0, byref(index), byref(base))
        path = Path(GetModuleFileNameEx(handle, base.value))
        module = path.stem.casefold()
        result = {"module": module, "return_rva": address - base.value}
        if module not in CALLERS:
            return result
        _, digest = CALLERS[module]
        debug.check_amd64_image(path, digest)
        result["image_sha256"] = digest
        return result

    def _remove_stopped(self, control):
        while self.breakpoints:
            breakpoint = self.breakpoints[-1]
            control.call(73, "remove stopped hardware breakpoint", (debug.PTR,), breakpoint.pointer)
            self.breakpoints.pop()

    def _capture(self, client, interfaces, handle, state):
        control, system = interfaces["control"], interfaces["system"]
        data, registers = interfaces["data"], interfaces["registers"]
        self._attach_owned(client, control, system, handle, state)
        site_ids = self._arm(control, interfaces["symbols"], handle)
        control.call(50, "continue owned process", (debug.U32,), debug.DEBUG_STATUS_GO)
        self.result["armed"] = True
        self.ready.set()
        self.result["stage"] = "observe native open"
        limit = monotonic() + 45
        while not self.cancel.is_set() and self.wait_event(control, limit):
            event, engine_pid, thread, observed, used = (debug.U32() for _ in range(5))
            control.call(94, "read debug event",
                         (debug.P32, debug.P32, debug.P32, debug.PTR, debug.U32, debug.P32,
                          debug.PTR, debug.U32, debug.P32),
                         byref(event), byref(engine_pid), byref(thread), byref(observed),
                         sizeof(observed), byref(used), None, 0, None)
            debug.require(event.value == debug.DEBUG_EVENT_BREAKPOINT and observed.value in site_ids,
                          "debugger stopped outside selected restore sites")
            name, offset, address = site_ids[observed.value]
            debug.require(system.value(27, "debug event OS process") == self.pid and
                          registers.value(11, "executed AMD64 instruction", debug.U64) == offset,
                          "debugger target or source site differs")
            if self.opening.is_set():
                record = {"site": name, "source_address": hex(address), "thread": thread.value}
                stack = registers.value(12, "AMD64 stack", debug.U64)
                if name == "api_error_128":
                    value = register(registers, "r8") & 0xffffffff
                    if value != 128:
                        self.result["other_api_errors"] = self.result.get("other_api_errors", 0) + 1
                        debug.require(self.result["other_api_errors"] < 64, "API diagnostic sample limit reached")
                        control.call(50, "resume past unrelated API error", (debug.U32,), debug.DEBUG_STATUS_GO)
                        continue
                    record["internal_error"] = value
                    record["caller"] = self._caller(interfaces["symbols"], handle, read_int(data, stack, 8))
                if name in ("receive_return", "receive_after_status_store", "ask_bodies_return", "model_body_inventory"):
                    record["eax"] = register(registers, "rax") & 0xffffffff
                if name.startswith("receive_"):
                    record["returned_partition_tag"] = read_int(data, stack + 0x138, 4, signed=True)
                    if name == "receive_after_status_store":
                        record["stored_receive_status"] = read_int(data, stack + 0x20, 4, signed=True)
                elif name == "ask_bodies_return":
                    record["returned_body_tag_count"] = read_int(data, stack + 0x4c, 4, signed=True)
                    record["tag_array_present"] = bool(read_int(data, stack + 0x40, 8))
                self.result["hits"].append(record)
                self.result["stage"] = "terminal native site observed"
                if not self.resume:
                    return
                self._remove_stopped(control)
                self.result["stopped_breakpoint_removed"] = True
                control.call(50, "continue with debugger attached", (debug.U32,), debug.DEBUG_STATUS_GO)
                self.result["continued_with_debugger_attached"] = True
                deadline = monotonic() + 45
                if self.wait_event(control, deadline):
                    raise RuntimeError("unexpected debug event after removing the selected site")
                return
            control.call(50, "resume owned process", (debug.U32,), debug.DEBUG_STATUS_GO)
        self.result["stage"] = "native open observation ended"

    def _cleanup(self, client, interfaces, state, handle):
        failures = []
        for breakpoint in reversed(self.breakpoints):
            try:
                interfaces["control"].call(73, "remove owned hardware breakpoint", (debug.PTR,), breakpoint.pointer)
            except Exception as error:
                failures.append(repr(error))
        super()._cleanup(client, interfaces, state, handle)
        if failures:
            self.result["breakpoint_cleanup_failures"] = failures
            self.result["cleanup_confirmed"] = False


def main():
    cli = ArgumentParser()
    cli.add_argument("engine", type=Path)
    cli.add_argument("control", type=Path)
    cli.add_argument("control_sha256")
    cli.add_argument("part", type=Path)
    cli.add_argument("part_sha256")
    cli.add_argument("output", type=Path)
    cli.add_argument("--terminal-site", choices=("no_debugger", "attach_only", *(name for name, _, _ in SITES)),
                     default="receive_return")
    cli.add_argument("--cold", action="store_true")
    cli.add_argument("--continue-after-hit", action="store_true")
    cli.add_argument("--writable", action="store_true")
    cli.add_argument("--open-delay", type=int, choices=(0, 5, 15), default=0)
    args = cli.parse_args()
    for path, digest in ((args.engine, ENGINE_SHA256), (args.control, args.control_sha256),
                         (args.part, args.part_sha256)):
        debug.require(sha256(path.read_bytes()).hexdigest() == digest, "scoped diagnostic input changed")
    app = None
    model = None
    tracer = None
    report = {"instrumented": args.terminal_site != "no_debugger", "heldout_inputs_read": 0,
              "passed": False, "site": args.terminal_site, "cold": args.cold,
              "writable": args.writable, "delay_seconds": args.open_delay,
              "part_sha256": args.part_sha256, "control_sha256": args.control_sha256}
    with args.output.open("x", encoding="utf-8"):
        pass
    try:
        Swapp.sweep()
        app = Swapp.Sw()
        identity = application_identity(app.app)
        debug.require(identity["version_matches"] and identity["sha256"] == APP_SHA256, "wrong CAD executable")
        report["oracle"] = identity
        if not args.cold:
            model, errors, warnings = app.open(args.control, read_only=True)
            debug.require(model is not None and errors == 0 and warnings in (0, 2) and Swapp.bodies(model) == 1,
                          "module warm-up control failed")
            app.close_doc(model)
            model = None
            report["warmup_control_passed"] = True
        started = monotonic()
        if report["instrumented"]:
            tracer = ColdAdmissionTrace(args.engine, identity, args.terminal_site, args.continue_after_hit)
            tracer.thread.start()
            debug.require(tracer.ready.wait(26) and tracer.result["armed"], "scoped debugger failed to arm")
        sleep(args.open_delay)
        if tracer is not None:
            tracer.opening.set()
        report["post_warmup_seconds"] = monotonic() - started
        model, errors, warnings = app.open(args.part, read_only=not args.writable)
        if tracer is not None:
            tracer.opening.clear()
            report["trace"] = tracer.finish()
            tracer = None
            debug.require(report["trace"]["cleanup_confirmed"], "debugger did not detach cleanly")
        report["open"] = {"opened": model is not None, "errors": errors, "warnings": warnings}
        if model is not None:
            report["bodies_before_rebuild"] = Swapp.bodies(model)
            report["needs_rebuild"] = int(Swapp.cv(model.Extension, "NeedsRebuild2"))
            if report["bodies_before_rebuild"] == 1:
                report["mass"] = Swapp.mass(model)
        report["passed"] = (
            report.get("trace", {}).get("failure") is None
            and sha256(args.part.read_bytes()).hexdigest() == args.part_sha256
            and sha256(args.control.read_bytes()).hexdigest() == args.control_sha256
        )
    except Exception as error:
        report["error"] = repr(error)
    finally:
        if tracer is not None:
            report["trace"] = tracer.finish()
        cleanup = report.get("trace", {})
        if app is not None and (cleanup.get("cleanup_confirmed") is not False
                                or cleanup.get("owned_process_debugger_present_after_cleanup") is False):
            if model is not None:
                app.close_doc(model)
            app.close()
            report["controller_diagnostics"] = app.diagnostics
            if app.diagnostics:
                report["passed"] = False
            report["debugger_absent_before_close"] = cleanup.get("owned_process_debugger_present_after_cleanup") is False
        args.output.write_text(dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
