let Sequence = 0
let Dropped = 0
let Phase = "armed"
const Budget = 50000
const Hooks = []
const Scopes = new Map()
const Epochs = new Map()
const ModelScopes = new Map()

const TrainingHookWindows = [{"module":"sldmodu.dll","rva":24640528,"bytes":20},{"module":"sldmodu.dll","rva":24755440,"bytes":14},{"module":"sldmodu.dll","rva":24060064,"bytes":14},{"module":"sldmodu.dll","rva":24060252,"bytes":15},{"module":"sldmodu.dll","rva":21021482,"bytes":14},{"module":"sldmodu.dll","rva":21021512,"bytes":15},{"module":"sldmodu.dll","rva":6654129,"bytes":18},{"module":"slduiu.dll","rva":4260336,"bytes":14},{"module":"slduiu.dll","rva":4260602,"bytes":14},{"module":"slduiu.dll","rva":4260683,"bytes":16},{"module":"sldmodu.dll","rva":21106256,"bytes":15}]
let TrainingInstructionCache = null

let TrainingActive = false
let TrainingCapture = false
let TrainingModel = null
const TrainingObjects = new Map()
const TrainingSolves = new Map()
const TrainingEvents = new Map()
let TrainingIncomplete = 0

function trainingpoint(Address) {
  const Result = {pointer: Address.toString(), coordinates: [], raw_bits_u64: [], complete: false}
  try {
    for (const Offset of [0, 8, 16]) {
      const Value = Address.add(Offset).readDouble()
      Result.coordinates.push(Number.isFinite(Value) ? Value : null)
      Result.raw_bits_u64.push(Address.add(Offset).readU64().toString(16))
    }
    Result.complete = Result.coordinates.every(Value => Value !== null)
  } catch (ErrorInfo) { Result.error = String(ErrorInfo) }
  return Result
}

function trainingpointadjacency(Address) {
  const Result = {complete: false}
  try {
    for (const [Offset, Name] of [[0xf8, "h1"], [0x100, "h2"]]) {
      const Handle = Address.add(Offset).readPointer()
      Result[Name] = Handle.isNull() ? {pointer: Handle.toString(), null: true, complete: true} : traininggeometryhandle(Handle)
    }
    Result.complete = Result.h1.complete && Result.h2.complete
  } catch (ErrorInfo) { Result.error = String(ErrorInfo) }
  return Result
}

function traininggeometryhandle(Address) {
  const Result = {pointer: Address.toString(), layout_read_complete: false, semantic_class_admitted: false, complete: false}
  try {
    const Table = Address.readPointer()
    Result.vtable = location(Table)
    if (TrainingModel === null || ![0x4d1cdd80, 0x4d1c5ae8].some(Value => Table.equals(TrainingModel.base.add(Value - 0x4b140000)))) return {...Result, reason: "unbound geometry-handle class"}
    Result.semantic_class_admitted = true
    Object.assign(Result, {vtable: location(Table), retention_predicate_slot_2d8: location(Address.readPointer().add(0x2d8).readPointer()), raw_f08_u32: Address.add(8).readU32(), raw_f0c_u32: Address.add(12).readU32(), sketch: Address.add(0x10).readPointer().toString(), index: Address.add(0x18).readS32(), raw_f1c_i32: Address.add(0x1c).readS32(), layout_read_complete: true, complete: true})
  } catch (ErrorInfo) { Result.error = String(ErrorInfo) }
  return Result
}

function traininghandle(Address, Model) {
  const Result = {pointer: Address.toString(), complete: false, dimension_resolution_complete: false}
  try {
    const Table = Address.readPointer()
    Result.vtable = location(Table)
    if (!Table.equals(Model.base.add(0x4d242c18 - 0x4b140000))) return {...Result, reason: "unbound concrete handle"}
    const Sketch = Address.add(0xf0).readPointer()
    const Index = Address.add(0xf8).readS32()
    const Gfr = Address.add(0xe8).readPointer()
    const Component = Address.add(0x58).readPointer()
    const Frozen = Address.add(0x100).readPointer()
    const FrozenState = Address.add(0x118).readS32()
    Object.assign(Result, {sketch: Sketch.toString(), index: Index, gfr: Gfr.toString(), component: Component.toString(), frozen_dimension: Frozen.toString(), frozen_state_i32: FrozenState, precision_source_u8: Address.add(0x150).readU8(), model_context: Address.add(0x168).readPointer().toString(), view_context: Address.add(0x170).readPointer().toString(), view_tag: Address.add(0x130).readPointer().toString(), complete: true})
    if (!Gfr.isNull() || !Component.isNull() || !Frozen.isNull() || FrozenState !== 0 || Sketch.isNull() || Index < 0) return {...Result, reason: "outside retained local uncached handle resolution"}
    const Array = Sketch.add(0x68).readPointer()
    const Data = Array.add(8).readPointer()
    const Count = Data.isNull() ? 0 : Data.sub(0x10).readS32()
    Object.assign(Result, {value_array: Array.toString(), value_data: Data.toString(), value_count_i32: Count})
    if (Count < 0 || Count > 512 || Index >= Count) return {...Result, reason: "value index or count is outside the bounded array"}
    const Dimension = Data.add(Index * 0x1a0)
    const DimensionTable = Dimension.readPointer()
    Result.dimension = {pointer: Dimension.toString(), vtable: location(DimensionTable)}
    if (!DimensionTable.equals(Model.base.add(0x4cf79588 - 0x4b140000))) return {...Result, reason: "resolved value is not the bound sgCircleDim"}
    Object.assign(Result.dimension, {type_i32: Dimension.add(0x80).readS32(), sketch: Dimension.add(0x88).readPointer().toString(), raw_f90_i32: Dimension.add(0x90).readS32(), raw_f94_i32: Dimension.add(0x94).readS32(), raw_f98_i32: Dimension.add(0x98).readS32(), parameter: Dimension.add(0x28).readPointer().toString(), feature_owner: Dimension.add(0x40).readPointer().toString(), tolerance: Dimension.add(0x48).readPointer().toString(), h1: traininggeometryhandle(Dimension.add(0x130)), h2: traininggeometryhandle(Dimension.add(0x158))})
    Result.dimension_resolution_complete = Result.dimension.h1.complete && Result.dimension.h2.complete
  } catch (ErrorInfo) { Result.complete = false; Result.error = String(ErrorInfo) }
  return Result
}

function trainingradial(Address) {
  const Result = {pointer: Address.toString(), complete: false, handles: []}
  try {
    const Model = TrainingModel
    const Table = Address.readPointer()
    Result.vtable = location(Table)
    if (!Table.equals(Model.base.add(0x4d255be0 - 0x4b140000))) return {...Result, reason: "unbound concrete radial display"}
    Object.assign(Result, {ffd8_u32: Address.add(0xfd8).readU32(), ffd8_i32: Address.add(0xfd8).readS32(), ffd4_u32: Address.add(0xfd4).readU32(), common_flags_f8a4_u32: Address.add(0x8a4).readU32(), raw_ae0_i32: Address.add(0xae0).readS32(), view_id_count_i32: Address.add(0x2b8).readS32(), align_group: Address.add(0xa68).readPointer().toString(), raw_a70_u64: Address.add(0xa70).readU64().toString(16), callout_data: Address.add(0x1050).readPointer().toString(), mirror_helper: Address.add(0x1090).readPointer().toString(), hole_wizard_info: Address.add(0x10a8).readPointer().toString(), transform: Address.add(0x1060).readPointer().toString(), witness_first: trainingpoint(Address.add(0x1010)), witness_second: trainingpoint(Address.add(0x1028))})
    const Count = Address.add(0x860).readS32()
    const Data = Address.add(0x858).readPointer()
    Object.assign(Result, {handle_count_i32: Count, handle_data: Data.toString()})
    if (Count < 0 || Count > 8 || (Count > 0 && Data.isNull())) return {...Result, reason: "handle collection is outside its bound"}
    for (let Index = 0; Index < Count; Index++) {
      const Handle = Data.add(Index * 8).readPointer()
      Result.handles.push(Handle.isNull() ? {pointer: Handle.toString(), complete: false, reason: "null model-dimension handle"} : traininghandle(Handle, Model))
    }
    Result.complete = Count > 0 && Result.handles.every(Value => Value.complete && Value.dimension_resolution_complete) && Result.witness_first.complete && Result.witness_second.complete
  } catch (ErrorInfo) { Result.error = String(ErrorInfo) }
  return Result
}

function trainingtrack(Address) {
  const Key = Address.toString()
  if (!TrainingObjects.has(Key) && TrainingObjects.size >= 128) {
    TrainingIncomplete++
    emit({kind: "training-object-bound", pointer: Key, complete: false})
    return false
  }
  TrainingObjects.set(Key, Address)
  return true
}

function trainingradials(Sketch = null) {
  const Result = {tracked_objects: TrainingObjects.size, subjects_observed: TrainingObjects.size > 0, capture_enabled: TrainingCapture, objects: [], complete: true}
  if (!TrainingCapture) return Result
  for (const Address of TrainingObjects.values()) {
    const Value = trainingradial(Address)
    const Matches = Sketch === null || Value.handles.some(Handle => Handle.sketch === Sketch.toString())
    if (Matches || !Value.complete) Result.objects.push(Value)
    if ((!Value.complete && Matches) || (!Value.complete && Value.handles.length === 0)) Result.complete = false
  }
  return Result
}

function trainingregistration(Address) {
  const Result = {pointer: Address.toString(), rows: [], complete: false}
  try {
    const Count = Address.add(0x210).readS32()
    const Cookies = Address.add(0x208).readPointer()
    const Eligibility = Address.add(0x228).readPointer()
    Object.assign(Result, {vtable: location(Address.readPointer()), count_i32: Count, cookies: Cookies.toString(), eligibility: Eligibility.toString(), raw_cached_168: Address.add(0x168).readPointer().toString()})
    if (Count < 0 || Count > 64 || (Count > 0 && (Cookies.isNull() || Eligibility.isNull()))) return {...Result, reason: "registration rows are outside the bounded table"}
    for (let Index = 0; Index < Count; Index++) {
      const Word = Eligibility.add(Index * 8).readU64().toString(16)
      Result.rows.push({index: Index, cookie_u32: Cookies.add(Index * 4).readU32(), raw_eligibility_u64: Word, eligible: Word !== "0"})
    }
    Result.complete = true
  } catch (ErrorInfo) { Result.error = String(ErrorInfo) }
  return Result
}

function traininglisteners(Address) {
  const Result = {pointer: Address.toString(), slots: [], complete: false, implementation_bound: false}
  try {
    const Count = Address.add(0x10).readS32()
    const Data = Address.add(8).readPointer()
    Object.assign(Result, {count_i32: Count, raw_count_u64: Address.add(0x10).readU64().toString(16), data: Data.toString()})
    if (Count < 0 || Count > 64 || (Count > 0 && Data.isNull())) return {...Result, reason: "listener collection is outside the bound"}
    for (let Index = 0; Index < Count; Index++) {
      const Listener = Data.add(Index * 8).readPointer()
      const Item = {index: Index, pointer: Listener.toString(), complete: false}
      Result.slots.push(Item)
      if (!Listener.isNull()) {
        const Table = Listener.readPointer()
        Object.assign(Item, {vtable: location(Table), release_target: location(Table.add(0x10).readPointer()), invoke_target: location(Table.add(0x30).readPointer())})
      }
      Item.complete = true
    }
    Result.complete = true
  } catch (ErrorInfo) { Result.error = String(ErrorInfo) }
  return Result
}

function trainingtop(Scopes) {
  const Values = Scopes.get(Process.getCurrentThreadId())
  return Values === undefined || Values.length === 0 ? null : Values[Values.length - 1]
}

function emit(Value) {
  if (Sequence >= Budget) { Dropped++; return }
  send({sequence: Sequence++, phase: Phase, ...(TrainingActive ? {thread: Process.getCurrentThreadId()} : {}), ...Value})
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
  try { return {pointer: Address.toString(), profile: Address.add(0x138).readPointer().toString(), ...(TrainingCapture ? {callback_f4b0: location(Address.add(0x4b0).readPointer()), radial_objects: trainingradials(Address)} : {}), points: sketchpoints(Address), lines: sketchlines(Address), arcs: sketcharcs(Address), next_permanent_marker: Address.add(0x130).readU32(), next_creation_ids: {point: Address.add(0x148).readS32(), line: Address.add(0x14c).readS32(), arc: Address.add(0x150).readS32()}, saved_status: Address.add(0x128).readS32(), status: Address.add(0x12c).readS32(), flags: Address.add(0x188).readU32(), raw_f37c_u16: Address.add(0x37c).readU16(), runtime_f388: Address.add(0x388).readPointer().toString(), runtime_f3e0: Address.add(0x3e0).readPointer().toString(), stamp: Address.add(0x56c).readU32()} }
  catch (ErrorInfo) { return {pointer: Address.toString(), error: String(ErrorInfo)} }
}

function sketchpoints(Address) {
  const Result = {array: null, data: null, raw_count: null, active_count: null, active_count_partial: null, scanned_count: 0, bounded_scan_complete: false, slot_scan_complete: false, completed_slots: 0, failing_index: null, slots: []}
  try {
    const Array = Address.add(8).readPointer()
    Result.array = Array.toString()
    if (Array.isNull()) return Result
    const Data = Array.add(8).readPointer()
    Result.data = Data.toString()
    const Count = Data.isNull() ? 0 : Data.sub(0x10).readS32()
    Result.raw_count = Count
    if (Count < 0 || Count > 10000) return Result
    let Active = 0
    Result.active_count_partial = Active
    for (let Index = 0; Index < Count; Index++) {
      Result.failing_index = Index
      const Point = Data.add(Index * 0x158)
      const Flags = Point.add(0x54).readU32()
      if (Count <= 512) Result.slots.push({index: Index, permanent_marker: Point.add(8).readU32(), creation_id: Point.add(0xc).readS32(), raw_f54_u32: Flags, deleted: (Flags & 1) !== 0, color: Point.add(0x30).readU32(), constraint_status: Point.add(0x34).readS32(), point_type_i32: Point.add(0xe4).readS32(), ...(TrainingCapture ? {adjacency_handles: trainingpointadjacency(Point)} : {}), role_uses_i32: Point.add(0xe8).readS32(), center_uses_i32: Point.add(0xec).readS32(), final_counter_i32: Point.add(0xf0).readS32(), xyz: [0xc8, 0xd0, 0xd8].map(Offset => Point.add(Offset).readDouble())})
      if ((Flags & 1) === 0) Active++
      Result.scanned_count = Index + 1
      Result.active_count_partial = Active
      Result.completed_slots = Result.slots.length
    }
    return {...Result, active_count: Active, bounded_scan_complete: true, slot_scan_complete: Count <= 512, failing_index: null}
  } catch (ErrorInfo) { return {...Result, error: String(ErrorInfo), bounded_scan_complete: false, slot_scan_complete: false} }
}

function sketchlines(Address) {
  const Result = {array: null, data: null, raw_count: null, scanned_count: 0, bounded_scan_complete: false, completed_slots: 0, failing_index: null, slots: []}
  try {
    const Array = Address.add(0x10).readPointer()
    Result.array = Array.toString()
    if (Array.isNull()) return Result
    const Data = Array.add(8).readPointer()
    Result.data = Data.toString()
    const Count = Data.isNull() ? 0 : Data.sub(0x10).readS32()
    Result.raw_count = Count
    if (Count < 0 || Count > 512) return Result
    for (let Index = 0; Index < Count; Index++) {
      Result.failing_index = Index
      const Line = Data.add(Index * 0xf0)
      const Flags = Line.add(0x54).readU32()
      Result.slots.push({index: Index, permanent_marker: Line.add(8).readU32(), creation_id: Line.add(0xc).readS32(), color: Line.add(0x30).readU32(), constraint_status: Line.add(0x34).readS32(), flags_f54: Flags, deleted: (Flags & 1) !== 0, start_point_index: Line.add(0xc8).readS32(), end_point_index: Line.add(0xcc).readS32()})
      Result.scanned_count = Index + 1
      Result.completed_slots = Result.slots.length
    }
    return {...Result, bounded_scan_complete: true, failing_index: null}
  } catch (ErrorInfo) { return {...Result, error: String(ErrorInfo), bounded_scan_complete: false} }
}

function sketcharcs(Address) {
  const Result = {array: null, data: null, raw_count: null, scanned_count: 0, bounded_scan_complete: false, completed_slots: 0, failing_index: null, slots: []}
  try {
    const Array = Address.add(0x28).readPointer()
    Result.array = Array.toString()
    if (Array.isNull()) return Result
    const Data = Array.add(8).readPointer()
    Result.data = Data.toString()
    const Count = Data.isNull() ? 0 : Data.sub(0x10).readS32()
    Result.raw_count = Count
    if (Count < 0 || Count > 512) return Result
    for (let Index = 0; Index < Count; Index++) {
      Result.failing_index = Index
      const Arc = Data.add(Index * 0xf8)
      const Flags = Arc.add(0x54).readU32()
      const Start = Arc.add(0xc8).readS32()
      const End = Arc.add(0xcc).readS32()
      Result.slots.push({index: Index, permanent_marker: Arc.add(8).readU32(), creation_id: Arc.add(0xc).readS32(), raw_f54_u32: Flags, deleted: (Flags & 1) !== 0, color: Arc.add(0x30).readU32(), constraint_status: Arc.add(0x34).readS32(), start_point_index: Start, end_point_index: End, endpoint_indices_equal: Start === End, contour_admission_i32: Arc.add(0xd0).readS32(), flipped_i32: Arc.add(0xd4).readS32(), orientation_i32: Arc.add(0xd8).readS32(), center_point_index: Arc.add(0xdc).readS32(), raw_fe0_reference_i32: Arc.add(0xe0).readS32(), raw_fe4_fe8_references_i32: [Arc.add(0xe4).readS32(), Arc.add(0xe8).readS32()], raw_fec_reference_i32: Arc.add(0xec).readS32()})
      Result.scanned_count = Index + 1
      Result.completed_slots = Result.slots.length
    }
    return {...Result, bounded_scan_complete: true, failing_index: null}
  } catch (ErrorInfo) { return {...Result, error: String(ErrorInfo), bounded_scan_complete: false} }
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
  traininghookinstructions() {
    if (Process.arch !== "x64" || Hooks.length !== 0) throw new Error("mapped training instruction verification must precede activation")
    const Rows = TrainingHookWindows.map(Value => {
      const Module = Process.enumerateModules().find(Item => Item.name.toLowerCase() === Value.module)
      if (Module === undefined) throw new Error("a pinned hook module is missing")
      const Address = Module.base.add(Value.rva)
      const Hex = Array.from(new Uint8Array(Address.readByteArray(Value.bytes))).map(Byte => Byte.toString(16).padStart(2, "0")).join("")
      return {...Value, mapped_address: Address.toString(), bytes_hex: Hex}
    })
    TrainingInstructionCache = Rows
    return Rows
  },
  resettrainingobjects(Capture = true) {
    if (!TrainingActive || TrainingSolves.size !== 0 || TrainingEvents.size !== 0) throw new Error("training reset requires an idle radial-training profile")
    if (typeof Capture !== "boolean") throw new Error("one explicit capture Boolean is required")
    const Cleared = TrainingObjects.size
    TrainingObjects.clear()
    TrainingCapture = Capture
    emit({kind: "training-object-tracker-reset", cleared: Cleared, capture_enabled: TrainingCapture})
    return {process_id: Process.id, cleared: Cleared, capture_enabled: TrainingCapture, incomplete: TrainingIncomplete}
  },
  markphase(Value) {
    if (typeof Value !== "string" || Value.length === 0 || Value.length > 120) throw new Error("one bounded phase label is required")
    Phase = Value
    emit({kind: "action-phase"})
    return {phase: Phase}
  },
  moduleidentity() {
    return Process.enumerateModules().filter(Value => ["sldmodu.dll", "sldmgu.dll", "slduiu.dll", "sldprtu.dll", "sldappu.dll", "swccu.dll", "sldarchiveu.dll", "sldmfcu.dll", "mfc140u.dll", "vcruntime140.dll", "vcruntime140_1.dll", "kernelbase.dll", "user32.dll"].includes(Value.name.toLowerCase())).map(Value => ({name: Value.name, path: Value.path, base: Value.base.toString(), size: Value.size}))
  },
  activate(Profile = "full", ExceptionProbes = false) {
    if (Process.arch !== "x64" || Hooks.length !== 0) throw new Error("exactly one activation in an x64 target is required")
    if (!["full", "loader", "sketch", "repair", "frame", "radial-training"].includes(Profile)) throw new Error("a supported observation profile is required")
    if (Profile === "radial-training") {
      if (TrainingInstructionCache === null || TrainingInstructionCache.length !== TrainingHookWindows.length) throw new Error("mapped hook instructions were not verified before activation")
      for (const Value of TrainingInstructionCache) {
        const Hex = Array.from(new Uint8Array(ptr(Value.mapped_address).readByteArray(Value.bytes))).map(Byte => Byte.toString(16).padStart(2, "0")).join("")
        if (Hex !== Value.bytes_hex) throw new Error("mapped hook instructions changed before activation")
      }
    }
    const Model = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "sldmodu.dll")
    const Common = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "swccu.dll")
    const Archive = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "sldarchiveu.dll")
    const Mfc = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "sldmfcu.dll")
    const Application = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "sldappu.dll")
    if (Model === undefined || Common === undefined || Archive === undefined || Mfc === undefined) throw new Error("selected target modules are not loaded")
    if (Profile === "full" || Profile === "loader") {
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
    if (Profile !== "repair" && Profile !== "frame") attach(Common.base.add(0xa3a7), {onEnter() {
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
    }
    if (ExceptionProbes || Profile === "frame") Process.setExceptionHandler(Details => {
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
    if (Profile === "frame") {
      if (Application === undefined) throw new Error("selected application module is not loaded")
      attach(Application.base.add(0x45bda7b0 - 0x453f0000), {onEnter(Args) {
        try {
          const Table = Args[0].readPointer()
          emit({kind: "initial-frame-enter", thread: Process.getCurrentThreadId(), template: Args[0].toString(), frame: Args[1].toString(), document: Args[2].toString(), make_visible_raw: Args[3].toInt32(), vtable: location(Table), target: location(Table.add(0xf8).readPointer()), caller: location(this.returnAddress)})
        } catch (ErrorInfo) { emit({kind: "initial-frame-probe-error", error: String(ErrorInfo)}) }
      }})
    }
    if (Profile === "full" || Profile === "repair") {
      if (Application === undefined) throw new Error("selected application module is not loaded")
      for (const [Address, Register, Kind] of [[0x45d718ca, "rax", "critical-repair-setter-handler"], [0x458a288a, "rbx", "critical-repair-api-test"]]) {
        attach(Application.base.add(Address - 0x453f0000), {
          onEnter() {
            try {
              const ObjectPointer = this.context[Register]
              emit({kind: Kind, thread: Process.getCurrentThreadId(), instruction: location(Application.base.add(Address - 0x453f0000)), application: ObjectPointer.toString(), fields: {raw_314: ObjectPointer.add(0x314).readU32(), raw_318: ObjectPointer.add(0x318).readU32(), critical_31c: ObjectPointer.add(0x31c).readU32(), raw_320: ObjectPointer.add(0x320).readU32()}})
            } catch (ErrorInfo) { emit({kind: "critical-repair-probe-error", site: Kind, error: String(ErrorInfo)}) }
          }
        })
      }
    }
    if (Profile === "radial-training") {
      const UI = Process.enumerateModules().find(Value => Value.name.toLowerCase() === "slduiu.dll")
      if (UI === undefined) throw new Error("the pinned UI module must already be loaded")
      TrainingModel = Model
      TrainingActive = true
      TrainingCapture = true
      attach(Model.base.add(0x4c8bfc10 - 0x4b140000), {
        onEnter(Args) { this.capture = TrainingCapture; if (!this.capture) return;
          this.object = Args[0]
          this.model = Args[1]
          this.handle = traininghandle(Args[2], Model)
          this.position = trainingpoint(Args[3])
          this.caller = location(this.returnAddress)
          this.arguments = {model: this.model.toString(), handle: this.handle, position: this.position, raw_argument_four_i32: this.context.rsp.add(0x28).readS32(), transform: this.context.rsp.add(0x30).readPointer().toString(), raw_argument_six_i32: this.context.rsp.add(0x38).readS32()}
          emit({kind: "radial-constructor-enter", thread: Process.getCurrentThreadId(), object: this.object.toString(), arguments: this.arguments, caller: this.caller})
        },
        onLeave() { if (!this.capture || !TrainingCapture) return;
          trainingtrack(this.object)
          emit({kind: "radial-constructor-leave", object: trainingradial(this.object), arguments: this.arguments, caller: this.caller})
        }
      })
      attach(Model.base.add(0x4c8dbcf0 - 0x4b140000), {
        onEnter(Args) { this.capture = TrainingCapture; if (!this.capture) return; this.object = Args[0]; trainingtrack(this.object); this.before = trainingradial(this.object); this.caller = location(this.returnAddress); emit({kind: "radial-engine-enter", object: this.before, caller: this.caller}) },
        onLeave() { if (!this.capture || !TrainingCapture) return; emit({kind: "radial-engine-leave", before: this.before, after: trainingradial(this.object), caller: this.caller}) }
      })
      attach(Model.base.add(0x4c8320a0 - 0x4b140000), {
        onEnter(Args) { this.capture = TrainingCapture; if (!this.capture) return; this.object = Args[0]; this.archive = Args[1]; this.loading = (this.archive.add(0x20).readU32() & 1) !== 0; if (!this.loading) trainingtrack(this.object); this.caller = location(this.returnAddress); emit({kind: "radial-serialize-enter", loading: this.loading, object: this.loading ? {pointer: this.object.toString(), vtable: location(this.object.readPointer()), fields_captured: false, state: "pre-load identity only"} : trainingradial(this.object), archive: archive(this.archive), caller: this.caller}) },
        onLeave() { if (!this.capture || !TrainingCapture) return; trainingtrack(this.object); emit({kind: "radial-serialize-leave", loading: this.loading, object: trainingradial(this.object), archive: archive(this.archive), caller: this.caller}) }
      })
      attach(Model.base.add(0x4c83215c - 0x4b140000), function () { if (!TrainingCapture) return;
        try { emit({kind: "radial-raw-word-store", object: trainingradial(this.context.rdi), archive: archive(this.context.rsi), archive_mode_u32: this.context.rsi.add(0x20).readU32(), instruction: location(Model.base.add(0x4c83215c - 0x4b140000))}) }
        catch (ErrorInfo) { TrainingIncomplete++; emit({kind: "radial-raw-word-store-error", complete: false, error: String(ErrorInfo)}) }
      })
      attach(Model.base.add(0x4c54c32a - 0x4b140000), function () { if (!TrainingCapture) return;
        const Scope = trainingtop(TrainingSolves)
        try {
          const Target = this.context.r15.add(0x4b0).readPointer()
          const Value = {sketch: this.context.r15.toString(), target_at_load: location(Target), target_nonnull: !Target.isNull(), before: sketch(this.context.r15), external_call_execution_proven: false}
          if (Scope !== null) Scope.callback = Value
          emit({kind: "sketch-callback-target-load", active_solve: Scope !== null, ...Value})
        } catch (ErrorInfo) { TrainingIncomplete++; emit({kind: "sketch-callback-target-load-error", complete: false, error: String(ErrorInfo)}) }
      })
      attach(Model.base.add(0x4c54c348 - 0x4b140000), function () { if (!TrainingCapture) return;
        const Scope = trainingtop(TrainingSolves)
        try {
          emit({kind: "sketch-callback-after-owner-query-boundary", active_solve: Scope !== null, target_load_observed: Scope !== null && Scope.callback !== null, interval_includes_model_owner_query: true, admission: Scope === null ? null : Scope.callback, after: sketch(this.context.r15), callback_effects_proven: false})
          if (Scope !== null) Scope.callback = null
        } catch (ErrorInfo) { TrainingIncomplete++; emit({kind: "sketch-callback-return-error", complete: false, error: String(ErrorInfo)}) }
      })
      attach(Model.base.add(0x4b7988b1 - 0x4b140000), function () { if (!TrainingCapture) return;
        try {
          const Context = this.context.rax
          const Table = Context.readPointer()
          const Scope = trainingtop(TrainingSolves)
          emit({kind: "model-context-target-selection", context: Context.toString(), vtable: location(Table), slot_target: location(Table.add(0x640).readPointer()), actual_target_loaded: false, sketch: Scope === null ? null : Scope.object.toString(), radials: trainingradials(Scope === null ? null : Scope.object), callback_effects_proven: false})
        } catch (ErrorInfo) { TrainingIncomplete++; emit({kind: "model-context-notification-error", complete: false, error: String(ErrorInfo)}) }
      })
      attach(UI.base.add(0x492b01f0 - 0x48ea0000), {
        onEnter(Args) { this.capture = TrainingCapture; if (!this.capture) return;
          this.thread = Process.getCurrentThreadId()
          this.entry = {event_id: Args[1].toInt32(), object: Args[0], selected_acquisition_attempts: 0, selected_list_observed: false}
          const Stack = TrainingEvents.get(this.thread) || []
          Stack.push(this.entry)
          TrainingEvents.set(this.thread, Stack)
          if (this.entry.event_id === 0x28) emit({kind: "sketch-solve-event-enter", automation_document: Args[0].toString(), registration: trainingregistration(Args[0]), descriptor: Args[2].toString(), argument_list: Args[3].toString(), caller: location(this.returnAddress), radials: trainingradials()})
        },
        onLeave(ReturnValue) { if (!this.capture || !TrainingCapture) return;
          const Stack = TrainingEvents.get(this.thread)
          if (this.entry.event_id === 0x28) emit({kind: "sketch-solve-event-leave", automation_document: this.entry.object.toString(), raw_return: ReturnValue.toString(), selected_acquisition_attempts_observed: this.entry.selected_acquisition_attempts, selected_list_observed: this.entry.selected_list_observed, radials: trainingradials(), callback_effects_proven: false})
          if (Stack !== undefined) { Stack.pop(); if (Stack.length === 0) TrainingEvents.delete(this.thread) }
        }
      })
      attach(UI.base.add(0x492b02fa - 0x48ea0000), function () { if (!TrainingCapture) return;
        const Scope = trainingtop(TrainingEvents)
        if (Scope === null || Scope.event_id !== 0x28) return
        Scope.selected_acquisition_attempts++
        try {
          const Document = this.context.rsi
          const Index = this.context.rbx.toInt32()
          const Count = Document.add(0x210).readS32()
          const Git = this.context.rax
          if (!Document.equals(Scope.object) || Count < 0 || Count > 64 || Index < 0 || Index >= Count || Git.isNull()) throw new Error("selected acquisition receiver or row is outside the bound")
          const Cookies = Document.add(0x208).readPointer()
          if (Cookies.isNull()) throw new Error("selected acquisition cookie array is null")
          const Target = Git.readPointer().add(0x28).readPointer()
          emit({kind: "sketch-solve-listener-acquisition-selection", observation_boundary: "before target and cookie argument loads", automation_document: Document.toString(), row_index_i32: Index, git_interface: Git.toString(), selected_target: location(Target), target_not_yet_loaded: true, selected_cookie_u32: Cookies.add(Index * 4).readU32(), selected_iid_pointer: UI.base.add(0x4a8cc0a8 - 0x48ea0000).toString(), selected_output_pointer: this.context.rsp.add(0x48).toString(), call_execution_proven: false, selected_acquisition_attempts_observed: Scope.selected_acquisition_attempts, radials: trainingradials(), implementation_bound: false, complete: true})
        } catch (ErrorInfo) {
          TrainingIncomplete++
          emit({kind: "sketch-solve-listener-acquisition-selection-error", complete: false, error: String(ErrorInfo), selected_acquisition_attempts_observed: Scope.selected_acquisition_attempts, call_execution_proven: false})
        }
      })
      attach(UI.base.add(0x492b034b - 0x48ea0000), function () { if (!TrainingCapture) return;
        const Scope = trainingtop(TrainingEvents)
        if (Scope === null || Scope.event_id !== 0x28) return
        Scope.selected_list_observed = true
        emit({kind: "sketch-solve-listener-selection", listeners: traininglisteners(this.context.r14), selected_acquisition_attempts_observed: Scope.selected_acquisition_attempts, radials: trainingradials(), callback_effects_proven: false})
      })
      attach(Model.base.add(0x4c560e50 - 0x4b140000), {
        onEnter(Args) { this.capture = TrainingCapture; if (!this.capture) return;
          this.object = Args[0]
          this.output = this.context.rsp.add(0x30).readPointer()
          this.caller = location(this.returnAddress)
          emit({kind: "circle-unique-point-search-enter", sketch: this.object.toString(), center: trainingpoint(Args[1]), normal: trainingpoint(this.context.rsp.add(0x28).readPointer()), output: this.output.toString(), native_radius: null, native_step: null, floating_register_capture: "not exposed by this observer", caller: this.caller})
        },
        onLeave(ReturnValue) { if (!this.capture || !TrainingCapture) return; const Success = ReturnValue.toInt32(); emit({kind: "circle-unique-point-search-leave", sketch: this.object.toString(), signed_result: Success, accepted_point: Success === 0 ? null : trainingpoint(this.output), caller: this.caller}) }
      })
    }
    if (Profile === "full" || Profile === "sketch" || Profile === "radial-training") {
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
        this.training_scope = TrainingCapture
        if (this.training_scope) {
          this.training_thread = Process.getCurrentThreadId()
          const Stack = TrainingSolves.get(this.training_thread) || []
          Stack.push({object: this.object, callback: null})
          TrainingSolves.set(this.training_thread, Stack)
        }
        this.before = sketch(this.object)
        this.caller = location(this.returnAddress)
        emit({kind: "sketch-whole-update-enter", before: this.before, transform: Args[1].toString(), result_pointer: Args[2].toString(), update_engine: Args[3].toString(), stack_i32: [this.context.rsp.add(0x28).readS32(), this.context.rsp.add(0x30).readS32()], constraint_balance: this.context.rsp.add(0x38).readPointer().toString(), tolerance_f64: this.context.rsp.add(0x40).readDouble(), tolerance_raw_u64: this.context.rsp.add(0x40).readU64().toString(16), caller: this.caller})
      },
      onLeave(ReturnValue) {
        try { emit({kind: "sketch-whole-update-leave", before: this.before, after: sketch(this.object), constrained_status: ReturnValue.toInt32(), raw_rax: ReturnValue.toString(), caller: this.caller}) }
        finally {
          if (this.training_scope) {
            const Stack = TrainingSolves.get(this.training_thread)
            if (Stack !== undefined) { Stack.pop(); if (Stack.length === 0) TrainingSolves.delete(this.training_thread) }
          }
        }
      }
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
  statistics() { return {events: Sequence, dropped: Dropped, training_hook_errors: TrainingIncomplete, training_objects: TrainingObjects.size, training_solves: TrainingSolves.size, training_events: TrainingEvents.size} }
}
