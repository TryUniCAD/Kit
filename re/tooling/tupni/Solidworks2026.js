let Sequence = 0
let Dropped = 0
let Phase = "armed"
const Budget = 50000
const Hooks = []
const Scopes = new Map()
const Epochs = new Map()
const ModelScopes = new Map()

function emit(Value) {
  if (Sequence >= Budget) { Dropped++; return }
  send({sequence: Sequence++, phase: Phase, ...Value})
}

function location(Address) {
  const Module = Process.findModuleByAddress(Address)
  return Module === null ? {address: Address.toString(), module: null} : {module: Module.name, rva: Address.sub(Module.base).toString()}
}

function archive(Address) {
  try {
    const Start = Address.add(0x48).readPointer()
    const Cursor = Address.add(0x38).readPointer()
    return {pointer: Address.toString(), buffer_start: Start.toString(), cursor: Cursor.toString(), buffer_offset: Cursor.sub(Start).toString(), buffer_end: Address.add(0x40).readPointer().toString(), map_count: Address.add(0x50).readU32(), epoch: Epochs.get(Address.toString()) || 0, logical_stream_offset: null}
  } catch (ErrorInfo) { return {pointer: Address.toString(), error: String(ErrorInfo)} }
}

function sketch(Address) {
  try { return {pointer: Address.toString(), profile: Address.add(0x138).readPointer().toString(), points: sketchpoints(Address), lines: sketchlines(Address), saved_status: Address.add(0x128).readS32(), status: Address.add(0x12c).readS32(), flags: Address.add(0x188).readU32(), raw_f37c_u16: Address.add(0x37c).readU16(), runtime_f388: Address.add(0x388).readPointer().toString(), runtime_f3e0: Address.add(0x3e0).readPointer().toString(), stamp: Address.add(0x56c).readU32()} }
  catch (ErrorInfo) { return {pointer: Address.toString(), error: String(ErrorInfo)} }
}

function sketchpoints(Address) {
  try {
    const Array = Address.add(8).readPointer()
    if (Array.isNull()) return {array: Array.toString(), raw_count: null, active_count: null, bounded_scan_complete: false}
    const Data = Array.add(8).readPointer()
    const Count = Data.isNull() ? 0 : Data.sub(0x10).readS32()
    if (Count < 0 || Count > 10000) return {raw_count: Count, active_count: null, bounded_scan_complete: false}
    let Active = 0
    for (let Index = 0; Index < Count; Index++) if ((Data.add(Index * 0x158 + 0x54).readU8() & 1) === 0) Active++
    return {array: Array.toString(), data: Data.toString(), raw_count: Count, active_count: Active, bounded_scan_complete: true}
  } catch (ErrorInfo) { return {error: String(ErrorInfo)} }
}

function sketchlines(Address) {
  try {
    const Array = Address.add(0x10).readPointer()
    if (Array.isNull()) return {array: Array.toString(), raw_count: null, bounded_scan_complete: false}
    const Data = Array.add(8).readPointer()
    const Count = Data.isNull() ? 0 : Data.sub(0x10).readS32()
    if (Count < 0 || Count > 512) return {array: Array.toString(), data: Data.toString(), raw_count: Count, bounded_scan_complete: false}
    const Lines = []
    for (let Index = 0; Index < Count; Index++) {
      const Line = Data.add(Index * 0xf0)
      const Flags = Line.add(0x54).readU32()
      Lines.push({index: Index, flags_f54: Flags, deleted: (Flags & 1) !== 0, start_point_index: Line.add(0xc8).readS32(), end_point_index: Line.add(0xcc).readS32()})
    }
    return {array: Array.toString(), data: Data.toString(), raw_count: Count, bounded_scan_complete: true, slots: Lines}
  } catch (ErrorInfo) { return {error: String(ErrorInfo)} }
}

function attach(Address, Handlers) {
  Hooks.push(Interceptor.attach(Address, Handlers))
}

function entity(Handle, Caller, Model) {
  try {
    const Sketch = Handle.add(0x10).readPointer()
    const Index = Handle.add(0x18).readS32()
    const Result = {handle: Handle.toString(), handle_vtable: location(Handle.readPointer()), sketch: Sketch.toString(), index: Index}
    const PointCaller = Model.base.add(0x4c5043a9 - 0x4b140000)
    const LineCaller = Model.base.add(0x4c502e43 - 0x4b140000)
    const IsPoint = Caller.equals(PointCaller)
    if ((!IsPoint && !Caller.equals(LineCaller)) || Index < 0 || Index >= 1000000) return {...Result, resolved: false}
    const Array = Sketch.add(IsPoint ? 8 : 0x10).readPointer()
    const Data = Array.add(8).readPointer()
    const Address = Data.add(Index * (IsPoint ? 0x158 : 0xf0))
    Object.assign(Result, {resolved: true, kind: IsPoint ? "point" : "line", pointer: Address.toString(), color: Address.add(0x30).readU32(), constraint_status: Address.add(0x34).readS32(), line_type: Address.add(0x38).readU32()})
    if (IsPoint) Object.assign(Result, {point_type_i32: Address.add(0xe4).readS32(), xyz: [0xc8, 0xd0, 0xd8].map(Offset => Address.add(Offset).readDouble())})
    return Result
  } catch (ErrorInfo) { return {handle: Handle.toString(), error: String(ErrorInfo)} }
}

function header(Address) {
  try { return {pointer: Address.toString(), update_stamp: Address.add(0x40).readU32(), body_stamp: Address.add(0x44).readU32(), update_time_i64: Address.add(0x48).readS64().toString()} }
  catch (ErrorInfo) { return {pointer: Address.toString(), error: String(ErrorInfo)} }
}

function runtimeclass(Address) {
  try {
    if (Address.isNull()) return null
    const Bytes = new Uint8Array(Address.readPointer().readByteArray(160))
    const End = Bytes.indexOf(0)
    return {pointer: Address.toString(), name: String.fromCharCode(...Bytes.slice(0, End < 0 ? Bytes.length : End)), name_truncated: End < 0, schema: Address.add(12).readU32()}
  }
  catch (ErrorInfo) { return {pointer: Address.toString(), error: String(ErrorInfo)} }
}

function objectmap(Address) {
  try {
    const Array = Address.add(0x58).readPointer()
    const Cursor = Address.add(0x38).readPointer()
    const End = Address.add(0x40).readPointer()
    return {array: Array.toString(), length: Array.add(0x10).readU32(), next_u16: End.sub(Cursor).toInt32() >= 2 ? Cursor.readU16() : null}
  } catch (ErrorInfo) { return {error: String(ErrorInfo)} }
}

function throwInfo(Address) {
  try {
    const Image = Process.getModuleByAddress(Address)
    const Types = Image.base.add(Address.add(12).readS32())
    const Count = Types.readS32()
    if (Count < 0 || Count > 64) return {error: "implausible MSVC catchable-type count", count: Count}
    const Names = []
    for (let Index = 0; Index < Count; Index++) {
      const Entry = Image.base.add(Types.add(4 + Index * 4).readS32())
      const Descriptor = Image.base.add(Entry.add(4).readS32())
      const Bytes = new Uint8Array(Descriptor.add(16).readByteArray(160))
      const End = Bytes.indexOf(0)
      Names.push(String.fromCharCode(...Bytes.slice(0, End < 0 ? Bytes.length : End)))
    }
    return {module: Image.name, rva: Address.sub(Image.base).toString(), candidate_msvc_type_names: Names}
  } catch (ErrorInfo) { return {error: String(ErrorInfo)} }
}

function prefix(Address) {
  try { return Array.from(new Uint8Array(Address.readByteArray(64))).map(Value => Value.toString(16).padStart(2, "0")).join("") }
  catch (ErrorInfo) { return {error: String(ErrorInfo)} }
}

rpc.exports = {
  markphase(Value) {
    if (typeof Value !== "string" || Value.length === 0 || Value.length > 120) throw new Error("one bounded phase label is required")
    Phase = Value
    emit({kind: "action-phase"})
    return {phase: Phase}
  },
  moduleidentity() {
    return Process.enumerateModules().filter(Value => ["sldmodu.dll", "swccu.dll", "sldarchiveu.dll", "sldmfcu.dll", "mfc140u.dll", "vcruntime140.dll", "vcruntime140_1.dll", "kernelbase.dll", "user32.dll"].includes(Value.name.toLowerCase())).map(Value => ({name: Value.name, path: Value.path, base: Value.base.toString(), size: Value.size}))
  },
  activate(Profile = "full", ExceptionProbes = false) {
    if (Process.arch !== "x64" || Hooks.length !== 0) throw new Error("exactly one activation in an x64 target is required")
    if (!["full", "loader", "sketch"].includes(Profile)) throw new Error("a supported observation profile is required")
    const Model = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "sldmodu.dll")
    const Common = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "swccu.dll")
    const Archive = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "sldarchiveu.dll")
    const Mfc = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "sldmfcu.dll")
    if (Model === undefined || Common === undefined || Archive === undefined || Mfc === undefined) throw new Error("selected target modules are not loaded")
    if (Profile !== "sketch") {
    attach(Common.base.add(0xa550), {
      onEnter(Args) { this.archive = Args[0]; emit({kind: "archive-object-enter", archive: archive(this.archive), map: objectmap(this.archive), requested_class: runtimeclass(Args[1]), caller: location(this.returnAddress)}) },
      onLeave(ReturnValue) { emit({kind: "archive-object-leave", archive: archive(this.archive), map: objectmap(this.archive), object: ReturnValue.toString()}) }
    })
    attach(Common.base.add(0xa2d0), {
      onEnter(Args) { this.archive = Args[0]; this.schema_pointer = Args[2]; this.tag_pointer = Args[3]; this.caller = location(this.returnAddress) },
      onLeave(ReturnValue) {
        try { emit({kind: "archive-class-read", archive: archive(this.archive), map: objectmap(this.archive), runtime_class: runtimeclass(ReturnValue), schema_out: this.schema_pointer.isNull() || ReturnValue.isNull() ? null : this.schema_pointer.readU32(), tag_out: this.tag_pointer.isNull() ? null : this.tag_pointer.readU32(), caller: this.caller}) }
        catch (ErrorInfo) { emit({kind: "archive-class-read-error", error: String(ErrorInfo), caller: this.caller}) }
      }
    })
    attach(Model.base.add(0x4c229a60 - 0x4b140000), {
      onEnter(Args) {
        this.thread = Process.getCurrentThreadId()
        ModelScopes.set(this.thread, (ModelScopes.get(this.thread) || 0) + 1)
        this.object = Args[0]
        emit({kind: "part-serialize-enter", object: this.object.toString(), archive: archive(Args[1]), global_file_version: Mfc.base.add(0x3ce97b90 - 0x3c720000).readU32(), caller: location(this.returnAddress)})
      },
      onLeave() { emit({kind: "part-serialize-leave", object: this.object.toString()}); ModelScopes.set(this.thread, ModelScopes.get(this.thread) - 1) }
    })
    for (const [Address, Kind] of [[0x3c7a8e60, "su-archive"], [0x3c7a8e10, "mfc-archive"]]) {
      attach(Mfc.base.add(Address - 0x3c720000), {
        onEnter(Args) { this.active = (ModelScopes.get(Process.getCurrentThreadId()) || 0) > 0; this.object = Args[0]; this.input_archive = Args[1]; this.caller = location(this.returnAddress) },
        onLeave() {
          if (!this.active) return
          try {
            const Context = this.object.readPointer()
            emit({kind: "part-archive-helper", overload: Kind, input_archive: this.input_archive.toString(), context: Context.toString(), context_file_version: Context.isNull() ? null : Context.add(0x7c0).readU32(), caller: this.caller})
          } catch (ErrorInfo) { emit({kind: "part-archive-helper-error", error: String(ErrorInfo), caller: this.caller}) }
        }
      })
    }
    attach(Mfc.base.add(0x3c752350 - 0x3c720000), {
      onEnter() { this.active = (ModelScopes.get(Process.getCurrentThreadId()) || 0) > 0; this.caller = location(this.returnAddress) },
      onLeave(ReturnValue) { if (this.active) emit({kind: "part-version-fallback", file_version: ReturnValue.toUInt32(), caller: this.caller}) }
    })
    }
    attach(Common.base.add(0xa3a7), {onEnter() {
      try {
        const Runtime = this.context.rax
        const NameBytes = new Uint8Array(Runtime.readPointer().readByteArray(160))
        const End = NameBytes.indexOf(0)
        emit({kind: "archive-class-schema", class_name: String.fromCharCode(...NameBytes.slice(0, End < 0 ? NameBytes.length : End)), runtime_schema: Runtime.add(12).readU32(), file_schema: this.context.rsp.add(0x28).readU32(), archive: archive(this.context.rbx), instruction: location(Common.base.add(0xa3a7))})
      } catch (ErrorInfo) { emit({kind: "archive-class-schema-error", error: String(ErrorInfo)}) }
    }})
    if (ExceptionProbes) {
    const ThrowHooks = new Set()
    for (const Image of Process.enumerateModules().filter(Value => /^(mfc140u|vcruntime140|vcruntime140_1)\.dll$/i.test(Value.name))) {
      for (const Entry of Image.enumerateExports()) {
        if (!Entry.name.includes("CxxThrowException") && !Entry.name.includes("AfxThrowArchiveException") && !Entry.name.includes("AfxThrowFileException")) continue
        if (ThrowHooks.has(Entry.address.toString())) continue
        ThrowHooks.add(Entry.address.toString())
        attach(Entry.address, {onEnter(Args) {
          if (Entry.name.includes("CxxThrowException")) {
            let Indirect = null
            try { Indirect = prefix(Args[0].readPointer()) } catch (ErrorInfo) { Indirect = {error: String(ErrorInfo)} }
            emit({kind: "cpp-throw", api: Entry.name, object: Args[0].toString(), throw_info: throwInfo(Args[1]), object_prefix_hex: prefix(Args[0]), indirect_object_prefix_hex: Indirect, caller: location(this.returnAddress)})
          } else {
            emit({kind: "mfc-throw", api: Entry.name, cause: Args[0].toInt32(), caller: location(this.returnAddress)})
          }
        }})
      }
    }
    Process.setExceptionHandler(Details => {
      const Registers = {}
      for (const Name of ["pc", "sp", "rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"]) {
        if (Details.context[Name] !== undefined) Registers[Name] = Details.context[Name].toString()
      }
      let Frames = []
      let BacktraceError = null
      try { Frames = Thread.backtrace(Details.context, Backtracer.ACCURATE).map(location) }
      catch (ErrorInfo) { BacktraceError = String(ErrorInfo) }
      emit({kind: "native-exception", type: Details.type, address: location(Details.address), memory: Details.memory === undefined ? null : {operation: Details.memory.operation, address: Details.memory.address.toString()}, registers: Registers, backtrace: Frames, backtrace_error: BacktraceError, handled: false})
      return false
    })
    }
    if (Profile !== "loader") {
    attach(Model.base.add(0x4c5916f0 - 0x4b140000), {
      onEnter(Args) {
        this.thread = Process.getCurrentThreadId()
        this.object = Args[0]
        this.archive = Args[1]
        Scopes.set(this.thread, (Scopes.get(this.thread) || 0) + 1)
        emit({kind: "sketch-serialize-enter", thread: this.thread, sketch: sketch(this.object), archive: archive(this.archive), caller: location(this.returnAddress)})
      },
      onLeave() {
        emit({kind: "sketch-serialize-leave", thread: this.thread, sketch: sketch(this.object), archive: archive(this.archive)})
        Scopes.set(this.thread, Scopes.get(this.thread) - 1)
      }
    })
    attach(Model.base.add(0x4c5195d0 - 0x4b140000), {
      onEnter(Args) { this.wrapper = Args[0]; this.object = this.wrapper.add(8).readPointer(); this.before = sketch(this.object); this.caller = location(this.returnAddress) },
      onLeave(ReturnValue) { emit({kind: "sketch-update", wrapper: this.wrapper.toString(), before: this.before, after: sketch(this.object), result: ReturnValue.toString(), caller: this.caller}) }
    })
    attach(Model.base.add(0x4c5167d0 - 0x4b140000), {
      onEnter(Args) { this.wrapper = Args[0]; this.object = this.wrapper.add(8).readPointer(); this.before = sketch(this.object); this.caller = location(this.returnAddress) },
      onLeave(ReturnValue) { emit({kind: "sketch-coordinate-commit", wrapper: this.wrapper.toString(), before: this.before, after: sketch(this.object), changed_coordinate_count: ReturnValue.toUInt32(), raw_rax: ReturnValue.toString(), caller: this.caller}) }
    })
    attach(Model.base.add(0x4c549ab0 - 0x4b140000), {
      onEnter(Args) {
        this.object = Args[0]
        this.before = sketch(this.object)
        this.caller = location(this.returnAddress)
        emit({kind: "sketch-whole-update-enter", before: this.before, transform: Args[1].toString(), result_pointer: Args[2].toString(), update_engine: Args[3].toString(), stack_i32: [this.context.rsp.add(0x28).readS32(), this.context.rsp.add(0x30).readS32()], constraint_balance: this.context.rsp.add(0x38).readPointer().toString(), tolerance_f64: this.context.rsp.add(0x40).readDouble(), tolerance_raw_u64: this.context.rsp.add(0x40).readU64().toString(16), caller: this.caller})
      },
      onLeave(ReturnValue) { emit({kind: "sketch-whole-update-leave", before: this.before, after: sketch(this.object), constrained_status: ReturnValue.toInt32(), raw_rax: ReturnValue.toString(), caller: this.caller}) }
    })
    attach(Model.base.add(0x4c5077f0 - 0x4b140000), {
      onEnter(Args) { this.handle = Args[0]; this.caller_pointer = this.returnAddress; this.before = entity(this.handle, this.caller_pointer, Model); this.raw_status = Args[1].toInt32(); this.drawing = Args[2].toInt32() },
      onLeave(ReturnValue) { emit({kind: "solver-status-map", handle: this.handle.toString(), raw_status: this.raw_status, drawing: this.drawing, mapped_status: ReturnValue.toInt32(), before: this.before, after_mapping_before_caller_resumes: entity(this.handle, this.caller_pointer, Model), caller: location(this.caller_pointer)}) }
    })
    attach(Model.base.add(0x4c0363c0 - 0x4b140000), {
      onEnter(Args) { this.object = Args[0]; this.status = Args[1].toInt32(); this.before = this.object.add(0xc).readU32(); this.caller = location(this.returnAddress) },
      onLeave() { emit({kind: "model-needs-update", object: this.object.toString(), requested_status: this.status, before: this.before, after: this.object.add(0xc).readU32(), caller: this.caller}) }
    })
    attach(Model.base.add(0x4bb38350 - 0x4b140000), {
      onEnter(Args) { this.object = Args[0]; this.caller = location(this.returnAddress) },
      onLeave() { emit({kind: "feature-constructor", object: this.object.toString(), date_code: this.object.add(0x2b4).readS32(), parasolid_behavior: this.object.add(0x2ac).readS32(), caller: this.caller}) }
    })
    attach(Model.base.add(0x4c03a810 - 0x4b140000), {
      onEnter(Args) { this.object = Args[0]; this.arguments = [Args[1].toString(), Args[2].toString(), Args[3].toString()]; this.caller = location(this.returnAddress) },
      onLeave(ReturnValue) { emit({kind: "update-session-stamp", object: this.object.toString(), arguments: this.arguments, raw_rax_not_semantic_result: ReturnValue.toString(), caller: this.caller}) }
    })
    if (Profile === "full") {
      for (const [Address, Kind] of [[0x4c1c8320, "model-finalization"], [0x4b79aaf0, "model-modified-flag"], [0x4bcf3170, "model-get-bodies"]]) {
        attach(Model.base.add(Address - 0x4b140000), {
          onEnter(Args) {
            this.object = Args[0]
            this.arguments = [Args[1].toString(), Args[2].toString(), Args[3].toString()]
            if (Kind === "model-get-bodies") this.output = Args[1]
            this.caller = location(this.returnAddress)
            emit({kind: Kind + "-enter", object: this.object.toString(), arguments: this.arguments, caller: this.caller})
          },
          onLeave(ReturnValue) {
            const Event = {kind: Kind + "-leave", object: this.object.toString(), raw_rax_not_semantic_result: ReturnValue.toString(), caller: this.caller}
            if (Kind === "model-get-bodies") {
              try { Event.output_count = this.output.add(0x10).readS32() }
              catch (ErrorInfo) { Event.output_count_error = String(ErrorInfo) }
            }
            emit(Event)
          }
        })
      }
    }
    for (const [Offset, Kind] of [[0x15350, "header-next-update-stamp"], [0x15340, "header-next-body-stamp"]]) {
      attach(Archive.base.add(Offset), {
        onEnter(Args) { this.object = Args[0]; this.before = header(this.object); this.caller = location(this.returnAddress) },
        onLeave(ReturnValue) { emit({kind: Kind, before: this.before, after: header(this.object), returned_u32: ReturnValue.toUInt32(), caller: this.caller}) }
      })
    }
    const Seen = new Set()
    for (const Entry of Common.enumerateExports()) {
      if (!Entry.name.startsWith("??5su_CArchive@@") || Seen.has(Entry.address.toString())) continue
      Seen.add(Entry.address.toString())
      attach(Entry.address, {
        onEnter(Args) {
          this.active = (Scopes.get(Process.getCurrentThreadId()) || 0) > 0
          if (!this.active) return
          this.archive = Args[0]
          this.before = archive(this.archive)
          this.caller = location(this.returnAddress)
        },
        onLeave() { if (this.active) emit({kind: "archive-primitive", api: Entry.name, before: this.before, after: archive(this.archive), caller: this.caller}) }
      })
    }
    attach(Common.base.add(0x5bd0), {
      onEnter(Args) { this.archive = Args[0]; this.active = (Scopes.get(Process.getCurrentThreadId()) || 0) > 0; this.before = this.active ? archive(this.archive) : null },
      onLeave() {
        const Key = this.archive.toString()
        Epochs.set(Key, (Epochs.get(Key) || 0) + 1)
        if (this.active) emit({kind: "archive-refill", before: this.before, after: archive(this.archive)})
      }
    })
    attach(Common.base.add(0x6ad0), {
      onEnter(Args) {
        this.active = (Scopes.get(Process.getCurrentThreadId()) || 0) > 0
        if (this.active) { this.archive = Args[0]; this.before = archive(this.archive); this.caller = location(this.returnAddress) }
      },
      onLeave(ReturnValue) { if (this.active) emit({kind: "archive-count", count: ReturnValue.toUInt32(), before: this.before, after: archive(this.archive), caller: this.caller}) }
    })
    }
    emit({kind: "hooks-ready", architecture: Process.arch, profile: Profile, exception_probes: ExceptionProbes, hook_count: Hooks.length, instruction_taint: false, absolute_stream_offsets: false})
    return {hooks: Hooks.length}
  },
  statistics() { return {events: Sequence, dropped: Dropped} }
}
