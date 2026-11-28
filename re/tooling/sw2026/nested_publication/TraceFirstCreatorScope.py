from struct import unpack

from capstone.x86 import X86_OP_MEM

from TraceSavedEndWords import Image, MODEL, require


EDITOR = ("slduiu.dll", "025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7", 0x48EA0000)
BOSS = 0x4CF3D488
SELECT = 0x4B706F00
MERGE = 0x4B70C7C0


def whole(image, name, start):
    end, = (end for first, end in image.unwind if first == start)
    return image.span(name, start, end)


def pointer(image, address):
    return unpack("<Q", image.raw(address, 8))[0]


def named_import(image, address, slot, name):
    image.call(address, slot, imported=True)
    _, symbol = image.imports[slot]
    require(symbol.startswith(name), "native instruction references a different imported owner")


def zero_register(image, address, register):
    image.op(address, "xor")
    image.reg(address, 0, register)
    image.reg(address, 1, register)


def trace_wire_defaults(model):
    descriptor = model.exports["?classmoExtrusion_c@moExtrusion_c@@2UCRuntimeClass@@A"]
    require(descriptor == 0x4DAD9270 and pointer(model, descriptor + 16) == 0x4BB02340,
            "concrete boss archive factory differs")
    for name, entry, site, target in (
        ("archive_factory", 0x4BB02340, 0x4BB0235C, 0x4BAD3A20),
        ("extrusion_factory_constructor", 0x4BAD3A20, 0x4BAD3A2D, 0x4C5A8980),
        ("profile_base_constructor", 0x4C5A8980, 0x4C5A898F, 0x4B76EF40),
        ("body_feature_constructor", 0x4B76EF40, 0x4B76EF54, 0x4B6FEEC0),
    ):
        whole(model, name, entry)
        model.call(site, target)
    require(model.effective_address(model.op(0x4BAD3A33, "lea"), 1) == BOSS,
            "factory constructor does not bind the exact ordinary boss")
    zero_register(model, 0x4B76EF72, "esi")
    model.write(0x4B76EF74, "rdi", 0x6C0, "rsi", 8)
    whole(model, "atom_feature_constructor", 0x4B6FEEC0)
    zero_register(model, 0x4B6FEF31, "ebp")
    model.write(0x4B6FF050, "rdi", 0x530, "rbp", 8)
    model.write(0x4B6FF05E, "rdi", 0x540, "rbp", 8)
    model.write(0x4B6FF065, "rdi", 0x548, "rbp", 8)
    model.write(0x4B6FF073, "rdi", 0x558, "ebp")
    model.export("moAtomFeature_c", "setFeatureScope", 0x4B2924F0, 0x4B2924F7)
    model.write(0x4B2924F0, "rcx", 0x544, "edx")
    model.export("moAtomFeature_c", "setAutoSelect", 0x4B291060, 0x4B291067)
    model.write(0x4B291060, "rcx", 0x558, "edx")
    require(pointer(model, BOSS + 0x28) == 0x4BB11640, "concrete boss serializer dispatch differs")
    whole(model, "ordinary_boss_serializer", 0x4BB11640)
    model.call(0x4BB116C2, 0x4BB0D460)
    whole(model, "body_feature_serializer", 0x4BB0D460)
    model.call(0x4BB0D46E, 0x4BB0B0C0)
    atom = whole(model, "atom_feature_serializer", 0x4BB0B0C0)
    for address, opcode, offset in ((0x4BB0B8C2, "lea", 0x548), (0x4BB0B8E2, "mov", 0x544),
                                    (0x4BB0B8F1, "lea", 0x544)):
        require(any(operand.type == X86_OP_MEM and operand.mem.disp == offset
                    for operand in model.op(address, opcode).operands), "persisted scope field changed")
    require(not any(operand.type == X86_OP_MEM and operand.mem.disp == 0x558
                    for item in atom for operand in item.operands), "runtime selection has direct wire ownership here")


def trace_no_prior_targets(model):
    for slot, value in ((0x2090, 0x4BAD58D0), (0x2678, 0x4B27CBE0), (0x6E8, 0x4B27CBE0),
                        (0x1898, 0x4B27E150)):
        require(pointer(model, BOSS + slot) == value, "ordinary extrusion vtable changed")
    model.span("ordinary_zero_predicate", 0x4B27CBE0, 0x4B27CBE3, unwind=False)
    zero_register(model, 0x4B27CBE0, "eax")
    model.op(0x4B27CBE2, "ret")
    whole(model, "ordinary_rebuild", 0x4BAD58D0)
    model.op(0x4BAD5B10, "call")
    model.mem(0x4BAD5B10, 0, "rax", 0x2678, 8)
    model.write(0x4BAD5B18, "rbp", -0x80, "eax")
    model.read(0x4BAD6520, "r9d", "rbp", -0x80)
    model.call(0x4BAD652C, MERGE)
    whole(model, "merge_and_output", MERGE)
    model.write(0x4B70C7FB, "rsp", 0x50, "ebx")
    named_import(model, 0x4B70C9FA, 0x4CD33D60, "??0suPtrArray@@")
    zero_register(model, 0x4B70CB0E, "r9d")
    zero_register(model, 0x4B70CB11, "r8d")
    model.call(0x4B70CB1B, SELECT)
    whole(model, "ordinary_selection", SELECT)
    zero_register(model, 0x4B706F28, "r13d")
    model.op(0x4B706F2B, "mov")
    model.reg(0x4B706F2B, 0, "r12d")
    model.reg(0x4B706F2B, 1, "r13d")
    for address, offset, branch, target in ((0x4B706FB5, 0x544, "je", 0x4B707207),
                                            (0x4B706FC2, 0x558, "jne", 0x4B707212)):
        model.op(address, "cmp")
        model.mem(address, 0, "rdi", offset, 4)
        model.reg(address, 1, "r12d")
        model.branch(address + model.instructions[address].size, branch, target)
    model.op(0x4B706F3B, "cmp")
    model.mem(0x4B706F3B, 0, "rdi", 0x6C0, 8)
    model.branch(0x4B706F42, "je", 0x4B706FB5)
    model.op(0x4B706FD7, "mov")
    model.mem(0x4B706FD7, 1, "rdi", 0x548, 8)
    model.branch(0x4B706FE1, "je", 0x4B70729E)
    model.op(0x4B7072A4, "call")
    model.mem(0x4B7072A4, 0, "rax", 0x6E8, 8)
    model.branch(0x4B7072AC, "je", 0x4B7072F9)
    model.op(0x4B707316, "ret")
    model.read(0x4B70CD6C, "eax", "rbp", 0x10)
    model.branch(0x4B70CD72, "jle", 0x4B70CE95)
    model.branch(0x4B70CE97, "jne", 0x4B70D091)
    model.guard(0x4B70CEA6, "rsp", 0x50, "je", 0x4B70CF2C)
    model.op(0x4B70CEBD, "mov")
    model.reg(0x4B70CEBD, 0, "edx")
    model.immediate(0x4B70CEBD, 1, 0x3A95)
    model.branch(0x4B70CF2F, "jle", 0x4B70D03F)
    named_import(model, 0x4B70D045, 0x4CD384E8, "?count@gcEntityList_c@@")
    named_import(model, 0x4B70D058, 0x4CD384F0, "?getAt@gcEntityList_c@@")
    named_import(model, 0x4B70D061, 0x4CD385F8, "?isValid@gcEnt_w@@")
    model.branch(0x4B70D069, "je", 0x4B70D082)
    named_import(model, 0x4B70D07C, 0x4CD33D70, "?addUnique@suPtrArray@@")
    model.guard(0x4B70D0EB, "rsi", 0x544, "je", 0x4B70D101)
    model.guard(0x4B70D0F4, "rsi", 0x558, "je", 0x4B70D1CD)
    model.read(0x4B70D101, "eax", "rbp", 0x10)
    model.branch(0x4B70D106, "jle", 0x4B70D1CD)
    model.call(0x4B70D18A, 0x4B7E8980)


def trace_author_options(editor):
    whole(editor, "extrusion_dialog_application", 0x493E5A80)
    editor.read(0x493E60B9, "eax", "rsi", 0x158)
    editor.write(0x493E60BF, "rbx", 0x544, "eax")
    editor.read(0x493E60C5, "eax", "rsi", 0x15C)
    editor.write(0x493E60CB, "rbx", 0x558, "eax")
    editor.write(0x493E60F2, "rbx", 0x548, "r14", 8)
    item = editor.op(0x493E60F9, "cmp")
    editor.mem(0x493E60F9, 0, "rsi", 0x160, 8)
    editor.immediate(0x493E60F9, 1, 0)
    editor.branch(item.address + item.size, "je", 0x493E61A8)
    editor.guard(0x493E6185, "r15", 0x10, "jle", 0x493E6195)
    editor.write(0x493E618C, "rbx", 0x548, "r15", 8)


def trace_scope(folder):
    model, editor = Image(folder, MODEL), Image(folder, EDITOR)
    trace_wire_defaults(model)
    trace_no_prior_targets(model)
    trace_author_options(editor)
    return {
        "build": "SOLIDWORKS 2026 SP05.2 (34.5.2.0604)", "model": model.result(), "editor": editor.result(),
        "stored_policy": {"all_existing_bodies": 0, "selected_existing_bodies": 1, "owner": "moAtomFeature_c.f544"},
        "runtime_auto_select": {"owner": "moAtomFeature_c+0x558", "constructor_default": 0, "direct_archive_member": False},
        "bootstrap_selected_list": "absent from fresh first-creator construction",
        "no_target_non_cut_geometry": ["0x4b70ce95", "0x4b70cea6", "0x4b70cf2c", "0x4b70d03f", "0x4b70d07c"],
        "automatic_wrapper_requires_existing_targets": True,
        "native_processes_started": 0, "vendor_instruction_listings_retained": False,
    }
