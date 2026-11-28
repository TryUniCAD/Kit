import sys, pefile, capstone
f, va, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
pefile.MAX_IMPORT_SYMBOLS = 100000
pe = pefile.PE(f, fast_load=True, max_symbol_exports=100000)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT'], pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_EXPORT']])
for warning in pe.get_warnings():
    print('PE warning:', warning, file=sys.stderr)
imp = {}
for e in getattr(pe, 'DIRECTORY_ENTRY_IMPORT', []):
    for i in e.imports:
        imp[i.address] = (e.dll.decode(), (i.name or b'#%d' % i.ordinal).decode())
exp = {}
for symbol in getattr(getattr(pe, 'DIRECTORY_ENTRY_EXPORT', None), 'symbols', []):
    if symbol.name:
        exp.setdefault(pe.OPTIONAL_HEADER.ImageBase + symbol.address, []).append(symbol.name.decode())
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
        if t in exp: note = '  ; ' + ' | '.join(exp[t])
    print(hex(ins.address), ins.mnemonic, ins.op_str, note)
    if ins.mnemonic == 'int3': break
