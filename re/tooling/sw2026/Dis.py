import sys, pefile, capstone
f, va, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
pe = pefile.PE(f)
imp = {}
for e in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
    for i in e.imports:
        imp[i.address] = (e.dll.decode(), (i.name or b'#%d' % i.ordinal).decode())
exp = {pe.OPTIONAL_HEADER.ImageBase + s.address: s.name.decode() for s in pe.DIRECTORY_ENTRY_EXPORT.symbols if s.name} if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT') else {}
rva = va - pe.OPTIONAL_HEADER.ImageBase
data = pe.get_memory_mapped_image()[rva:rva + n]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
md.detail = True
for ins in md.disasm(data, va):
    note = ''
    for operand in ins.operands:
        if operand.type == capstone.x86.X86_OP_MEM and operand.mem.base == capstone.x86.X86_REG_RIP:
            tgt = ins.address + ins.size + operand.mem.disp
            if tgt in imp: note = '  ; ' + imp[tgt][1]
    if ins.mnemonic in ('call', 'jmp') and ins.op_str.startswith('0x'):
        t = int(ins.op_str, 16)
        if t in exp: note = '  ; ' + exp[t]
    print(hex(ins.address), ins.mnemonic, ins.op_str, note)
    if ins.mnemonic == 'int3': break
