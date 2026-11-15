let Sequence = 0
let Dropped = 0
const Budget = 50000
const Hooks = []
const Scopes = new Map()
const Epochs = new Map()

function emit(Value) {
  if (Sequence >= Budget) { Dropped++; return }
  send({sequence: Sequence++, ...Value})
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
  try { return {pointer: Address.toString(), saved_status: Address.add(0x128).readS32(), status: Address.add(0x12c).readS32(), flags: Address.add(0x188).readU32(), stamp: Address.add(0x56c).readU32()} }
  catch (ErrorInfo) { return {pointer: Address.toString(), error: String(ErrorInfo)} }
}

function attach(Address, Handlers) {
  Hooks.push(Interceptor.attach(Address, Handlers))
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
  moduleidentity() {
    return Process.enumerateModules().filter(Value => ["sldmodu.dll", "swccu.dll", "mfc140u.dll", "vcruntime140.dll", "vcruntime140_1.dll", "kernelbase.dll", "user32.dll"].includes(Value.name.toLowerCase())).map(Value => ({name: Value.name, path: Value.path, base: Value.base.toString(), size: Value.size}))
  },
  activate() {
    if (Process.arch !== "x64" || Hooks.length !== 0) throw new Error("exactly one activation in an x64 target is required")
    const Model = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "sldmodu.dll")
    const Common = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "swccu.dll")
    if (Model === undefined || Common === undefined) throw new Error("selected target modules are not loaded")
    attach(Common.base.add(0xa3a7), {onEnter() {
      try {
        const Runtime = this.context.rax
        const NameBytes = new Uint8Array(Runtime.readPointer().readByteArray(160))
        const End = NameBytes.indexOf(0)
        emit({kind: "archive-class-schema", class_name: String.fromCharCode(...NameBytes.slice(0, End < 0 ? NameBytes.length : End)), runtime_schema: Runtime.add(12).readU32(), file_schema: this.context.rsp.add(0x28).readU32(), archive: archive(this.context.rbx), instruction: location(Common.base.add(0xa3a7))})
      } catch (ErrorInfo) { emit({kind: "archive-class-schema-error", error: String(ErrorInfo)}) }
    }})
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
    attach(Model.base.add(0x4c5077f0 - 0x4b140000), {
      onEnter(Args) { emit({kind: "solver-status-map", handle: Args[0].toString(), raw_status: Args[1].toInt32(), drawing: Args[2].toInt32(), caller: location(this.returnAddress)}) }
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
    emit({kind: "hooks-ready", architecture: Process.arch, hook_count: Hooks.length, instruction_taint: false, absolute_stream_offsets: false})
    return {hooks: Hooks.length}
  },
  statistics() { return {events: Sequence, dropped: Dropped} }
}
