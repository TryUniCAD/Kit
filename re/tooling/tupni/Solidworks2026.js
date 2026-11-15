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

rpc.exports = {
  moduleidentity() {
    return Process.enumerateModules().filter(Value => ["sldmodu.dll", "swccu.dll"].includes(Value.name.toLowerCase())).map(Value => ({name: Value.name, path: Value.path, base: Value.base.toString(), size: Value.size}))
  },
  activate() {
    if (Process.arch !== "x64" || Hooks.length !== 0) throw new Error("exactly one activation in an x64 target is required")
    const Model = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "sldmodu.dll")
    const Common = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "swccu.dll")
    if (Model === undefined || Common === undefined) throw new Error("selected target modules are not loaded")
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
      onEnter(Args) { this.object = Args[0]; this.before = sketch(this.object); this.caller = location(this.returnAddress) },
      onLeave(ReturnValue) { emit({kind: "sketch-update", before: this.before, after: sketch(this.object), result: ReturnValue.toString(), caller: this.caller}) }
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
      onLeave(ReturnValue) { emit({kind: "update-session-stamp", object: this.object.toString(), arguments: this.arguments, result: ReturnValue.toString(), caller: this.caller}) }
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
