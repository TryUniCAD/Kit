from __future__ import annotations

import ctypes
from hashlib import sha256
from pathlib import Path
from struct import unpack_from

import DrawingSaveAggregateDbgEng as engine
import DrawingSavePropertiesGateDbgEng as restoration


UI_SHA256 = '025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7'
CALL_RVA = 0x13AAED7
RETURN_RVA = 0x13AAEDC
ALLOWED_RVAS = frozenset((CALL_RVA, RETURN_RVA))


def original_byte(path, rva):
    data = Path(path).read_bytes()
    engine.require(sha256(data).hexdigest() == UI_SHA256, 'original slduiu differs')
    pe = unpack_from('<I', data, 0x3c)[0]
    table = pe + 24 + unpack_from('<H', data, pe + 20)[0]
    for index in range(unpack_from('<H', data, pe + 6)[0]):
        _, address, size, raw = unpack_from('<IIII', data, table + 40 * index + 8)
        if address <= rva < address + size:
            return data[raw + rva - address:raw + rva - address + 1]
    raise ValueError('whitelisted source site has no initialized original bytes')


def register64(registers, name):
    index = engine.U32()
    registers.call(5, 'locate the whitelisted AMD64 register', (engine.CSTR, engine.P32), name.encode('ascii'), ctypes.byref(index))
    value = engine.DebugValue()
    registers.call(6, 'sample the whitelisted AMD64 register', (engine.U32, engine.PTR), index.value, ctypes.byref(value))
    engine.require(value.type == engine.DEBUG_VALUE_INT64, 'register has no typed AMD64 integer')
    return value.integer


class EdgeCacheTrace(restoration.PropertiesGateTrace):
    def __init__(self, sw, debugger_engine, identity):
        super().__init__(sw, debugger_engine, identity)
        self.result['trace_scope'] = 'first actual pre-event7 UI downstream edge-cache lookup call/return; intended selected edge not yet joined'
        self.result['edge_lookup_path'] = {}
        self.result['breakpoint_kind'] = 'dbgeng_managed_software'
        self._entry = None

    def ui_base(self, symbols, handle):
        from win32process import GetModuleFileNameEx

        index, base = engine.U32(), engine.U64()
        symbols.call(14, 'locate pinned loaded slduiu', (engine.CSTR, engine.U32, engine.P32, engine.P64),
                     b'slduiu', 0, ctypes.byref(index), ctypes.byref(base))
        engine.require(base.value != 0, 'owned slduiu is not loaded')
        path = Path(GetModuleFileNameEx(handle, base.value))
        engine.require(path.name.casefold() == 'slduiu.dll', 'loaded image is not the exact UI module')
        engine.check_amd64_image(path, UI_SHA256)
        engine.require(self._module_base in (None, base.value), 'owned UI module base changed')
        self._module_base, self._module_path, self._process_handle = base.value, path, handle
        return base.value

    def verify_owned_module(self, handle):
        from win32process import GetModuleFileNameEx

        self.confirm_owned(handle)
        engine.require(self._module_base is not None and self._module_path is not None, 'owned UI module is unbound')
        path = Path(GetModuleFileNameEx(handle, self._module_base))
        engine.require(path == self._module_path and path.name.casefold() == 'slduiu.dll', 'owned UI module identity changed')
        engine.check_amd64_image(path, UI_SHA256)

    def arm_breakpoint(self, control, state, offset):
        engine.require(self._module_base is not None, 'owned UI module is unbound')
        rva = offset - self._module_base
        engine.require(rva in ALLOWED_RVAS, 'software stop is outside the two fixed source sites')
        self.verify_owned_module(self._process_handle)
        original = original_byte(self._module_path, rva)
        before = restoration.owned_process_byte(self._process_handle, offset)
        engine.require(before == original, 'owned instruction differs before arming')
        row = {'rva': rva, 'bytes': 1, 'original_sha256': sha256(original).hexdigest(),
               'before_arm_sha256': sha256(before).hexdigest(), 'before_arm_matches_original': True,
               'armed': False, 'remove_call_succeeded': False}
        self._sites.append(row)
        self._active_site = row
        identifier = engine.SaveAggregateTrace.arm_breakpoint(self, control, state, offset)
        row['armed'] = True
        return identifier

    def snapshot_sites(self, handle, phase):
        self.verify_owned_module(handle)
        for row in self._sites:
            expected = original_byte(self._module_path, row['rva'])
            actual = restoration.owned_process_byte(handle, self._module_base + row['rva'])
            row[phase] = {'bytes_read': len(actual), 'sha256': sha256(actual).hexdigest(), 'matches_original': actual == expected}

    def verify_stop(self, interfaces, handle, *, break_id, base, rva):
        control, system = interfaces['control'], interfaces['system']
        event, engine_pid, engine_tid, identifier, used = [engine.U32() for _ in range(5)]
        control.call(94, 'read the fixed source-site breakpoint event',
                     (engine.P32, engine.P32, engine.P32, engine.PTR, engine.U32, engine.P32, engine.PTR, engine.U32, engine.P32),
                     ctypes.byref(event), ctypes.byref(engine_pid), ctypes.byref(engine_tid), ctypes.byref(identifier),
                     ctypes.sizeof(identifier), ctypes.byref(used), None, 0, None)
        engine.require((event.value, identifier.value, used.value) == (engine.DEBUG_EVENT_BREAKPOINT, break_id, ctypes.sizeof(identifier)), 'received a different debug event')
        engine.require(self.save_entered.is_set() and not self.save_returned.is_set() and not self.event7_seen.is_set(), 'source stop was outside the actual pre-event7 owned SaveAs interval')
        engine.require(system.value(27, 'verify source stop owned OS PID') == self.pid, 'source stop belongs to a different process')
        self.confirm_owned(handle)
        effective = control.value(47, 'effective CPU at source stop')
        executing = control.value(36, 'executing CPU at source stop')
        engine.require(effective == executing == engine.AMD64, 'source stop lacks executed AMD64 context')
        registers = interfaces['registers']
        engine.require(registers.value(11, 'source RIP', engine.U64) == base + rva, 'source stop RIP differs')
        stack = registers.value(12, 'source stack', engine.U64)
        engine.require(stack and self.ui_base(interfaces['symbols'], handle) == base, 'source stack/module changed')
        selected = system.value(7, 'capture exact owned engine process id')
        engine.require(self._engine_process_id in (None, selected), 'owned engine process id changed')
        self._engine_process_id = selected
        self.result['engine_process_id_captured'] = True
        return engine_tid.value, stack

    def _capture(self, client, interfaces, handle, state):
        control, system = interfaces['control'], interfaces['system']
        deadline = engine.monotonic() + engine.SETUP_SECONDS
        self.result['stage'] = 'verify_initial_break_engine_option'
        current = control.value(53, 'read engine initial-break options')
        self.result['initial_break_already_enabled'] = bool(current & engine.DEBUG_ENGOPT_INITIAL_BREAK)
        if not current & engine.DEBUG_ENGOPT_INITIAL_BREAK:
            control.call(54, 'enable the owned initial stop', (engine.U32,), engine.DEBUG_ENGOPT_INITIAL_BREAK)
        engine.require(control.value(53, 'verify engine initial-break options') & engine.DEBUG_ENGOPT_INITIAL_BREAK, 'initial stop option not retained')
        self.result['initial_break_option_verified'] = True
        self.result['stage'] = 'request_owned_attach'
        engine.require(not self.cancel.is_set(), 'owned source trace canceled before attachment')
        self.confirm_owned(handle)
        engine.require(not engine.debugger_present(handle), 'owned process already has a debugger')
        client.call(12, 'attach only the exact COM-owned process', (engine.U64, engine.U32, engine.U32), 0, self.pid, engine.DEBUG_ATTACH_DEFAULT)
        state['attach_requested'] = self.result['attach_requested'] = True
        self.result['cleanup_confirmed'] = False
        self.result['stage'] = 'wait_initial_stop'
        engine.require(self.wait_event(control, deadline), 'owned initial stop was not delivered')
        engine.require(system.value(27, 'verify initial owned OS PID') == self.pid, 'initial stop is not owned')
        self.confirm_owned(handle)
        self.result['initial_stop_verified'] = True
        self._engine_process_id = system.value(7, 'capture exact initial engine process id')
        client.call(16, 'set owned target detach-on-exit', (engine.U32,), engine.DEBUG_PROCESS_DETACH_ON_EXIT)
        client.call(16, 'restrict debugging to the owned process', (engine.U32,), engine.DEBUG_PROCESS_ONLY_THIS_PROCESS)
        options = client.value(15, 'verify owned target process options')
        wanted = engine.DEBUG_PROCESS_DETACH_ON_EXIT | engine.DEBUG_PROCESS_ONLY_THIS_PROCESS
        engine.require(options & wanted == wanted and engine.debugger_present(handle), 'owned process options were not retained')
        self.result['process_options'] = options
        self.result['process_options_verified'] = True
        control.call(6, 'set bounded owned cleanup interrupt', (engine.U32,), engine.CLEANUP_INTERRUPT_SECONDS)
        engine.require(control.value(5, 'verify cleanup interrupt timeout') == engine.CLEANUP_INTERRUPT_SECONDS, 'cleanup timeout not retained')
        base = self.ui_base(interfaces['symbols'], handle)
        if control.value(47, 'initial effective CPU') != engine.AMD64:
            control.call(48, 'select AMD64 for the owned session', (engine.U32,), engine.AMD64)
        engine.require(control.value(47, 'verify selected AMD64 CPU') == engine.AMD64, 'AMD64 context unavailable')
        engine.require(not self.cancel.is_set(), 'owned source trace canceled before arming')
        path = self.result['edge_lookup_path']
        for name, rva in [('call', CALL_RVA), ('return', RETURN_RVA)]:
            row = {'rva': rva, 'armed': False, 'sample': None, 'state': 'unqualified'}
            path[name] = row
            if state['breakpoint'] is not None:
                self.remove_software_breakpoint(interfaces, state['breakpoint'], handle)
                state['breakpoint'] = None
            self.result['stage'] = 'arm_' + name
            identifier = self.arm_breakpoint(control, state, base + rva)
            row['armed'] = True
            self.result['armed'] = True
            row['resume_requested_offset_ns'] = self.event_offset()
            control.call(50, 'continue owned source trace to ' + name, (engine.U32,), engine.DEBUG_STATUS_GO)
            self.result['stage'] = 'wait_' + name
            try:
                stopped = self.wait_for_save_stop(control, row, signal_ready=name == 'call')
            finally:
                row['save_wait_ended_offset_ns'] = self.event_offset()
            if not stopped:
                if row.get('wait_exit_reason') == 'save_returned':
                    row['state'] = 'unobserved_after_completed_save'
                    self.result['route'] = name + '_unobserved'
                else:
                    self.result['route'] = 'unqualified'
                return
            thread, stack = self.verify_stop(interfaces, handle, break_id=identifier, base=base, rva=rva)
            registers = interfaces['registers']
            if name == 'call':
                component, unique, kernel_edge = (register64(registers, register) for register in ('rcx', 'rdx', 'r8'))
                unique &= 0xffffffff
                engine.require(component and unique and kernel_edge, 'actual cache lookup operands are null/zero')
                self._entry = (component, unique, kernel_edge, thread, stack)
                row['sample'] = {'component_nonnull': True, 'requested_downstream_id_u32': unique, 'kernel_edge_nonnull': True,
                                 'event7_seen': False, 'effective_cpu': hex(engine.AMD64), 'executing_cpu': hex(engine.AMD64)}
            else:
                engine.require(self._entry is not None and (thread, stack) == self._entry[3:], 'lookup return belongs to another call frame')
                returned = register64(registers, 'rax')
                row['sample'] = {'reference_nonnull': returned != 0, 'same_call_thread_and_stack': True,
                                 'requested_downstream_id_u32': self._entry[1], 'event7_seen': False,
                                 'effective_cpu': hex(engine.AMD64), 'executing_cpu': hex(engine.AMD64)}
                self.result['route'] = 'paired_lookup_nonnull' if returned else 'paired_lookup_null'
            row['state'] = 'observed'
        self.result['stage'] = 'paired_lookup_observed'


def qualified(trace):
    path = trace.get('edge_lookup_path') or {}
    call, returned = path.get('call') or {}, path.get('return') or {}
    cleanup = trace.get('breakpoint_cleanup') or {}
    complete = bool(trace.get('armed') and trace.get('failure') is None and trace.get('initial_stop_verified')
                    and trace.get('initial_break_option_verified') and trace.get('process_options_verified')
                    and trace.get('cleanup_confirmed') and cleanup.get('qualified')
                    and cleanup.get('all_sites_original_after_detach') and trace.get('owned_process_debugger_present_after_cleanup') is False)
    clock = [call.get('resume_requested_offset_ns'), call.get('save_wait_started_offset_ns'), trace.get('save_entered_offset_ns'),
             call.get('save_wait_ended_offset_ns'), returned.get('resume_requested_offset_ns'), returned.get('save_wait_started_offset_ns'),
             returned.get('save_wait_ended_offset_ns'), trace.get('event7_offset_ns'), trace.get('save_returned_offset_ns')]
    ordered = None not in clock and clock == sorted(clock)
    observed = bool(complete and ordered and call.get('state') == returned.get('state') == 'observed'
                    and returned.get('sample', {}).get('same_call_thread_and_stack')
                    and call['sample']['requested_downstream_id_u32'] == returned['sample']['requested_downstream_id_u32'])
    return {'observer_completed_cleanly': complete, 'paired_cache_lookup_observed': observed,
            'nonnull_cache_reference_observed': observed and returned['sample']['reference_nonnull'],
            'route': trace.get('route', 'unqualified'), 'pre_event7_clock_order_verified': ordered, 'selected_annotation_edge_joined': False,
            'fallback_asserted': False}
