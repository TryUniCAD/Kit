from hashlib import sha256
from struct import unpack

from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
import pefile


MODEL = ("sldmodu.dll", "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e", 0x4B140000)
GEOMETRY = ("sldgcu.dll", "77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594", 0x43740000)


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


class Image:
    def __init__(self, folder, pin):
        name, digest, base = pin
        path = folder / name
        require(path == path.resolve(strict=True), "licensed image is redirected")
        data = path.read_bytes()
        require(sha256(data).hexdigest() == digest, "licensed image has a different build")
        self.identity = {"file": name, "sha256": digest, "image_base": hex(base), "bytes": len(data)}
        self.base = base
        self.pe = pefile.PE(data=data, fast_load=True, max_symbol_exports=50000)
        require(self.pe.FILE_HEADER.Machine == 0x8664 and self.pe.OPTIONAL_HEADER.ImageBase == base,
                "licensed image has a different architecture or base")
        self.pe.parse_data_directories(directories=[0, 1, 3])
        self.exports = {row.name.decode(): base + row.address for row in self.pe.DIRECTORY_ENTRY_EXPORT.symbols
                        if row.name is not None and row.forwarder is None}
        self.imports = {row.address: (table.dll.decode().lower(), row.name.decode())
                        for table in self.pe.DIRECTORY_ENTRY_IMPORT for row in table.imports if row.name is not None}
        self.unwind = {(base + row.struct.BeginAddress, base + row.struct.EndAddress)
                       for row in self.pe.DIRECTORY_ENTRY_EXCEPTION}
        self.decoder = Cs(CS_ARCH_X86, CS_MODE_64)
        self.decoder.detail = True
        self.ranges = {}
        self.instructions = {}

    def raw(self, address, size):
        raw = self.pe.get_data(address - self.base, size)
        require(len(raw) == size, "instruction interval extends past initialized image data")
        return raw

    def span(self, name, start, end, unwind=True):
        require(not unwind or (start, end) in self.unwind, "named native range has no exact unwind identity")
        data = self.raw(start, end - start)
        decoded = tuple(self.decoder.disasm(data, start))
        require(sum(item.size for item in decoded) == len(data), "native range failed exact instruction exhaustion")
        self.instructions.update((item.address, item) for item in decoded)
        self.ranges[name] = {"start": hex(start), "end_exclusive": hex(end), "sha256": sha256(data).hexdigest(),
                             "unwind_range": unwind}
        return decoded

    def call(self, address, target, imported=False):
        item = self.instructions[address]
        require(item.mnemonic == "call", f"expected a call at {address:#x}")
        if imported:
            require(self.effective_address(item, 0) == target, "native call changed its actual import slot")
        else:
            self.immediate(address, 0, target)

    def effective_address(self, item, index):
        operand = item.operands[index]
        require(operand.type == X86_OP_MEM and item.reg_name(operand.mem.base) == "rip",
                "expected an image-relative operand")
        return item.address + item.size + operand.mem.disp

    def op(self, address, mnemonic):
        item = self.instructions[address]
        require(item.mnemonic == mnemonic, f"changed instruction at {address:#x}")
        return item

    def reg(self, address, index, name):
        item = self.instructions[address]
        operand = item.operands[index]
        require(operand.type == X86_OP_REG and item.reg_name(operand.reg) == name,
                f"changed register at {address:#x}")

    def mem(self, address, index, base, offset, size):
        item = self.instructions[address]
        operand = item.operands[index]
        require(operand.type == X86_OP_MEM and item.reg_name(operand.mem.base) == base
                and operand.mem.index == 0 and operand.mem.disp == offset and operand.size == size,
                f"changed member ownership at {address:#x}")

    def immediate(self, address, index, value):
        operand = self.instructions[address].operands[index]
        require(operand.type == X86_OP_IMM and operand.imm == value, f"changed operand at {address:#x}")

    def write(self, address, base, offset, source, size=4):
        self.op(address, "mov")
        self.mem(address, 0, base, offset, size)
        if type(source) is str:
            self.reg(address, 1, source)
        else:
            self.immediate(address, 1, source)

    def read(self, address, dest, base, offset):
        self.op(address, "mov")
        self.reg(address, 0, dest)
        self.mem(address, 1, base, offset, 4)

    def branch(self, address, mnemonic, target):
        self.op(address, mnemonic)
        self.immediate(address, 0, target)

    def guard(self, address, base, offset, branch, target):
        item = self.op(address, "cmp")
        self.mem(address, 0, base, offset, 4)
        self.immediate(address, 1, 0)
        self.branch(address + item.size, branch, target)

    def export(self, owner, name, address, end=None):
        require(any(symbol.startswith(f"?{name}@{owner}@@") and value == address
                    for symbol, value in self.exports.items()),
                f"missing exact export {owner}.{name}")
        if end is not None:
            self.span(f"{owner}.{name}", address, end, unwind=False)
            self.op(end - 1, "ret")

    def result(self):
        return {**self.identity, "ranges": self.ranges}


def accessors(image, owner, fields):
    for name, (offset, getter, setter) in fields.items():
        image.export(owner, "get" + name, getter, getter + 7)
        image.export(owner, "set" + name, setter, setter + 7)
        image.read(getter, "eax", "rcx", offset)
        image.write(setter, "rcx", offset, "edx")


def check_model(model):
    descriptor = model.exports["?classmoEndSpec_c@moEndSpec_c@@2UCRuntimeClass@@A"]
    require(descriptor == 0x4DAD9180, "end spec descriptor moved")
    require(unpack("<IIQ", model.raw(descriptor + 8, 16)) == (0x160, 0x80000001, 0x4BB02220),
            "end spec descriptor factory or schema differs")
    table, = unpack("<Q", model.raw(0x4CF3D3F8 + 5 * 8, 8))
    require(table == 0x4BB10250, "end spec model vtable does not dispatch the exact serializer")
    model.span("schema_one_serializer", table, 0x4BB11067)
    for offset, store, load in ((0x150, 0x4BB105BF, 0x4BB10FAC), (0x154, 0x4BB105CE, 0x4BB10FBC)):
        model.read(store, "edx", "rbx", offset)
        model.call(store + 9, 0x4CD3D880, imported=True)
        model.op(load, "lea")
        model.mem(load, 1, "rbx", offset, 8)
        model.reg(load, 0, "rdx")
        model.call(load + 10, 0x4CD3D888, imported=True)
    model.op(0x4BB10F85, "cmp")
    model.reg(0x4BB10F85, 0, "eax")
    model.immediate(0x4BB10F85, 1, 4460)
    model.branch(0x4BB10F8A, "jb", 0x4BB10FCE)
    model.write(0x4BB10FCE, "rbx", 0x148, 0, 8)
    model.write(0x4BB10FD9, "rbx", 0x150, 0, 8)
    model.op(0x4BB11003, "cmp")
    model.immediate(0x4BB11003, 1, 15105)
    model.branch(0x4BB11008, "jb", 0x4BB1101F)
    model.write(0x4BB1101F, "rbx", 0x158, 1)
    model.span("descriptor_factory", 0x4BB02220, 0x4BB0224E)
    model.call(0x4BB0223C, 0x4BAD2DC0)
    for name, start, stop, anchor in (
        ("factory_default", 0x4BAD2DC0, 0x4BAD2F1C, 0x4BAD2DD6),
        ("copy_in_component", 0x4BAD2F20, 0x4BAD35B8, 0x4BAD2F49),
        ("model_attached_default", 0x4BAD35C0, 0x4BAD37AB, 0x4BAD35F0),
    ):
        model.span(name, start, stop)
        require(model.effective_address(model.op(anchor, "lea"), 1) == 0x4CF3D3F8,
                "constructor did not bind the concrete moEndSpec_c table")
    model.op(0x4BAD2E45, "xor")
    model.reg(0x4BAD2E45, 0, "eax")
    model.reg(0x4BAD2E45, 1, "eax")
    model.write(0x4BAD2E47, "rdi", 0x154, "rax", 8)
    model.write(0x4BAD2F0B, "rdi", 0x150, "eax")
    model.read(0x4BAD3278, "eax", "rdi", 0x150)
    model.write(0x4BAD327E, "rsi", 0x150, "eax")
    model.write(0x4BAD3593, "rsi", 0x154, 0)
    model.op(0x4BAD366F, "xor")
    model.reg(0x4BAD366F, 0, "ebx")
    model.reg(0x4BAD366F, 1, "ebx")
    model.write(0x4BAD3787, "rdi", 0x150, "rbx", 8)
    accessors(model, "moEndSpec_c", {"DelInitFace": (0x150, 0x4B2A30B0, 0x4B30FA30),
                                    "KnitRes": (0x154, 0x4B30C840, 0x4B30FC50),
                                    "CreateSolidFrmCappedMidPlaneSurfExt": (0x158, 0x4B2C61E0, 0x4B2C67B0),
                                    "Merge": (0x128, 0x4B284C30, 0x4B2918C0)})
    model.export("moAtomFeature_c", "getFeatureScope", 0x4B2867D0, 0x4B2867D7)
    model.export("moAtomFeature_c", "setFeatureScope", 0x4B2924F0, 0x4B2924F7)
    model.read(0x4B2867D0, "eax", "rcx", 0x544)
    model.write(0x4B2924F0, "rcx", 0x544, "edx")
    model.span("atom_feature_serializer", 0x4BB0B0C0, 0x4BB0CD82)
    model.op(0x4BB0B8E2, "mov")
    require(any(op.type == X86_OP_MEM and op.mem.disp == 0x544 for op in model.instructions[0x4BB0B8E2].operands),
            "atom feature serializer lost its scope getter")
    model.op(0x4BB0B8F1, "lea")
    require(any(op.type == X86_OP_MEM and op.mem.disp == 0x544 for op in model.instructions[0x4BB0B8F1].operands),
            "atom feature serializer lost its scope destination")
    model.span("selected_scope_dispatch", 0x4B706F00, 0x4B707317)
    model.op(0x4B706FD7, "mov")
    require(any(op.type == X86_OP_MEM and op.mem.disp == 0x548 for op in model.instructions[0x4B706FD7].operands),
            "selected branch does not load the actual selection owner")
    model.branch(0x4B706FE1, "je", 0x4B70729E)


def direct_reach(image, start, end, take=()):
    pending, visited = [start], set()
    while pending:
        address = pending.pop()
        if address in visited:
            continue
        require(start <= address < end and address in image.instructions,
                "native branch escaped the pinned dispatcher range")
        visited.add(address)
        insn = image.instructions[address]
        if insn.mnemonic.startswith("ret") or insn.mnemonic == "int3":
            continue
        if insn.mnemonic.startswith("j"):
            operand = insn.operands[0]
            require(operand.type == X86_OP_IMM, "native dispatcher needs unresolved indirect branch analysis")
            pending.append(operand.imm)
            if insn.mnemonic == "jmp" or address in take:
                continue
        pending.append(address + insn.size)
    return visited


def check_geometry_flow(model, geometry):
    model.export("moEndSpec_c", "genGcEndSpec", 0x4BADE750)
    model.span("end_spec_translation", 0x4BADE750, 0x4BADF01A)
    model.write(0x4BADE789, "rbp", 0x10, "r8", 8)
    for read, store, source, target, base in (
        (0x4BADEF03, 0x4BADEF09, 0xF0, 0x118, "rbp"),
        (0x4BADEF0F, 0x4BADEF16, 0x150, 0x11C, "r13"),
        (0x4BADEF1C, 0x4BADEF23, 0x154, 0x120, "r13"),
        (0x4BADEF40, 0x4BADEF46, 0xF8, 0x130, "rbp"),
    ):
        model.read(read, "eax", base, source)
        model.write(store, "rbx", target, "eax")
    require(unpack("<Q", model.raw(0x4CF3D488 + 0x2658, 8)) == (0x4BAEDB00,),
            "ordinary extrusion no longer calls the measured dispatcher")
    model.span("ordinary_extrusion_thunk", 0x4BAEDB00, 0x4BAEDB05, unwind=False)
    model.branch(0x4BAEDB00, "jmp", 0x4BAEDBC0)
    dispatcher = model.span("ordinary_extrusion_dispatch", 0x4BAEDBC0, 0x4BAEE3DE)
    model.op(0x4BAEDC51, "xor")
    model.reg(0x4BAEDC51, 0, "esi")
    model.reg(0x4BAEDC51, 1, "esi")
    writes_rsi = [item.address for item in dispatcher if 0x4BAEDC51 <= item.address <= 0x4BAEDDD1
                   and {item.reg_name(register) for register in item.regs_access()[1]} & {"rsi", "esi", "si", "sil"}]
    require(writes_rsi == [0x4BAEDC51], "ordinary geometry payload selectors are no longer proven zero")
    model.write(0x4BAEDDBE, "rsp", 0x28, "esi")
    model.write(0x4BAEDDC2, "rsp", 0x20, "esi")
    model.call(0x4BAEDDD1, 0x4BADE750)
    for site, slot, prefix in (
        (0x4BADEEFC, 0x4CD368A0, "?setEndSpecData@gcEndSpec_c@@"),
        (0x4BADEF3A, 0x4CD36530, "?setCapped@gcEndSpec_c@@"),
        (0x4BAEE0ED, 0x4CD36528, "?destroyStartSheet@gcEndSpec_c@@"),
        (0x4BAEE171, 0x4CD36510, "?setFrom2Dto3D@gcEndSpec_c@@"),
        (0x4BAEE306, 0x4CD36890, "?ram_MakeExtrudedBody@@"),
    ):
        model.call(site, slot, imported=True)
        module, symbol = model.imports[slot]
        require(module == GEOMETRY[0] and symbol.startswith(prefix) and symbol in geometry.exports,
                "ordinary extrusion import does not resolve to the pinned geometry image")
    model.span("ordinary_geometry_flag_setup", 0x4BAF8EF0, 0x4BAF90CC)
    model.call(0x4BAEDFF7, 0x4BAF8EF0)
    for site in (0x4BAF8F41, 0x4BAF8F5A, 0x4BAF8F73, 0x4BAF8F8C, 0x4BAF8FA5,
                 0x4BAF8FBE, 0x4BAF8FEF, 0x4BAF903D, 0x4BAF9057, 0x4BAF9073, 0x4BAF908F, 0x4BAF90B1):
        model.call(site, 0x4CD36898, imported=True)
    module, symbol = model.imports[0x4CD36898]
    require(module == GEOMETRY[0] and symbol.startswith("?setVerFlag@gcEndSpec_c@@")
            and geometry.exports[symbol] == 0x43CC9C70, "geometry version flag owner differs")
    geometry.export("gcEndSpec_c", "setVerFlag", 0x43CC9C70, 0x43CC9C7F)
    geometry.write(0x43CC9C76, "rcx", 0xDC, "edx")
    accessors(geometry, "gcEndSpec_c", {"DelInitFace": (0x11C, 0x4376AAF0, 0x4376C3E0),
                                       "KnitRes": (0x120, 0x4375BD60, 0x4376C450)})
    geometry.span("geometry_extrusion", 0x43CB9570, 0x43CBA8A9)
    geometry.op(0x43CB95D6, "mov")
    geometry.reg(0x43CB95D6, 0, "r12")
    geometry.mem(0x43CB95D6, 1, "rbp", 0x140, 8)
    for address, discriminator, branch, target in (
        (0x43CB99FC, 0x130, "je", 0x43CB9A15),
        (0x43CB9A0A, 0x120, "jne", 0x43CB9A34),
        (0x43CB9A37, 0x118, "je", 0x43CB9B52),
        (0x43CB9A46, 0x11C, "je", 0x43CB9ABE),
        (0x43CB9A78, 0x120, "jne", 0x43CB9ABB),
        (0x43CB9ABE, 0x118, "je", 0x43CB9B52),
        (0x43CB9ACD, 0x120, "je", 0x43CB9B52),
    ):
        geometry.guard(address, "r12", discriminator, branch, target)
    field_reads = [item.address for item in geometry.instructions.values()
                   if 0x43CB9570 <= item.address < 0x43CBA8A9
                   and any(op.type == X86_OP_MEM and item.reg_name(op.mem.base) == "r12"
                           and op.mem.disp in (0x11C, 0x120) for op in item.operands)]
    require(sorted(field_reads) == [0x43CB9A0A, 0x43CB9A46, 0x43CB9A78, 0x43CB9ACD],
            "geometry dispatcher has new reads of the bound option words")
    full = direct_reach(geometry, 0x43CB9570, 0x43CBA8A9)
    ordinary = direct_reach(geometry, 0x43CB9570, 0x43CBA8A9, (0x43CB9A05, 0x43CB9A40, 0x43CB9AC7))
    require(set(field_reads) <= full and not set(field_reads) & ordinary,
            "ordinary zero selectors do not bypass all four geometric option reads")
    return {"named_option_reads": [hex(address) for address in field_reads],
            "unrestricted_instruction_count": len(full), "ordinary_instruction_count": len(ordinary),
            "ordinary_named_option_reads_reached": 0, "escaped_or_indirect_branch_count": 0}


def trace_native(folder):
    model, geometry = Image(folder, MODEL), Image(folder, GEOMETRY)
    check_model(model)
    reads = check_geometry_flow(model, geometry)
    return {
        "build": "SOLIDWORKS 2026 SP05.2 (34.5.2.0604)",
        "model": model.result(), "geometry": geometry.result(),
        "model_to_geometry": {"f150": "DeleteOriginalFace at +0x11c", "f154": "KnitResult at +0x120"},
        "ordinary_dispatch_supplies_zero_selectors": ["+0x118", "+0x130"],
        "direct_geometry_control_flow": reads,
        "factory_constructor_neutral": {"f150": 0, "f154": 0},
        "model_attached_constructor_neutral": {"f150": 0, "f154": 0},
        "copy_constructor": {"f150": "source value", "f154": 0},
        "native_processes_started": 0, "vendor_instruction_listings_retained": False,
    }
