import hashlib
import json
import re
import struct
import subprocess
import tempfile
from pathlib import Path


BASE = Path(__file__).resolve().parent
CONTENTS = Path('~/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents').expanduser()
SOURCE = CONTENTS / 'Libraries/Applications/FusionDoc/NaFusionDoc10.dylib'


def sections(data):
    result = []
    offset = 32
    for _ in range(struct.unpack_from('<I', data, 16)[0]):
        command, size = struct.unpack_from('<II', data, offset)
        if command == 0x19:
            address, length, file_offset, file_length = struct.unpack_from('<QQQQ', data, offset + 24)
            result.append((address, address + file_length, file_offset))
        offset += size
    return result


def string_at(data, segments, address):
    for lower, upper, file_offset in segments:
        if lower <= address < upper:
            offset = file_offset + address - lower
            if data[offset + 1:offset + 4] == bytes(3):
                chars = []
                for at in range(offset, min(len(data), offset + 2000), 4):
                    char = struct.unpack_from('<I', data, at)[0]
                    if char == 0:
                        if len(chars) > 1:
                            return ''.join(chars)
                        break
                    if not 32 <= char < 127:
                        break
                    chars.append(chr(char))
            end = data.find(b'\0', offset, offset + 3000)
            if end < 0:
                return None
            value = data[offset:end]
            if value and all(32 <= char < 127 for char in value):
                return value.decode('ascii')
    return None


def analyze(binary, start, end, data, segments, stubs):
    command = ['xcrun', 'llvm-objdump', '--disassemble', '--demangle', '--start-address=' + hex(start), '--stop-address=' + hex(end), str(binary)]
    lines = subprocess.check_output(command, text=True).splitlines()[4:]
    pages = {}
    references = []
    annotated = []
    for line in lines:
        match = re.search(r'adrp\s+(x\d+), (0x[0-9a-f]+)', line)
        if match:
            pages[match[1]] = int(match[2], 16)
        match = re.search(r'add\s+(x\d+), (x\d+), #(0x[0-9a-f]+)', line)
        if match and match[2] in pages:
            address = pages[match[2]] + int(match[3], 16)
            value = string_at(data, segments, address)
            if value:
                references.append(dict(instruction=line.strip().split(':')[0], address=hex(address), text=value))
                line += ' [string: ' + value + ']'
        match = re.search(r'\b(?:bl|b)\s+(0x[0-9a-f]+)', line)
        if match and int(match[1], 16) in stubs:
            line += ' [stub: ' + stubs[int(match[1], 16)] + ']'
        annotated.append(line)
    return dict(start=hex(start), end=hex(end), stringReferences=references, disassembly=annotated)


def main():
    with tempfile.TemporaryDirectory(dir=BASE) as temporary:
        binary = Path(temporary) / 'Drawing.arm64.dylib'
        subprocess.run(['xcrun', 'lipo', str(SOURCE), '-thin', 'arm64', '-output', str(binary)], check=True)
        data = binary.read_bytes()
        segments = sections(data)
        symbol_output = subprocess.check_output(['xcrun', 'llvm-objdump', '--macho', '--indirect-symbols', str(binary)], text=True)
        stubs = {}
        for line in symbol_output.splitlines():
            match = re.match(r'(0x[0-9a-f]+)\s+\d+\s+(\S+)', line)
            if match:
                name = match[2][1:] if match[2].startswith('__Z') else match[2]
                stubs[int(match[1], 16)] = name
        demangled = subprocess.check_output(['c++filt'], input='\n'.join(stubs.values()) + '\n', text=True).splitlines()
        stubs = dict(zip(stubs, demangled, strict=True))
        intervals = {
            'ExtFileSerializer.initializeMemberSet': (0x2689e0, 0x268aa8),
            'FusionDocAssetSettings.initializeMemberSet': (0x2ee7d0, 0x2ef400),
            'FusionDocExternalFileRefs.initializeMemberSet': (0x2f94e8, 0x2fa4b4),
            'FusionDocTrackedEntities.initializeMemberSet': (0x313358, 0x31335c),
            'FusionDocAssetAdapter.dwgFileNameAndPath': (0x290e00, 0x290e90),
            'ExtFileBlobSerializer.doSave': (0x2650b4, 0x265610),
            'ExtFileBlobSerializer.doLoadPart': (0x266690, 0x266838),
        }
        excerpts = {name: analyze(binary, *bounds, data, segments, stubs) for name, bounds in intervals.items()}
        report = dict(scope='Static disassembly only; no native code loaded or executed', source=str(SOURCE), sourceSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(), arm64Sha256=hashlib.sha256(data).hexdigest(), addressBasis='Unslid arm64 virtual address', excerpts=excerpts)
        report['intrinsicGlobalPointers'] = {hex(address): stubs.get(address) for address in [0x59ef50, 0x59ef58, 0x59ef68, 0x5a1110, 0x5a1128]}
        report['legacyVersion'] = dict(raw=0x080006a7, major=2, minor=0, build=1703, formula='major = word >> 26; minor = (word >> 20) & 63; build = word & 0xfffff', metadataReadGate='Metadata version <=5 converts the first u32 as saved software version; newer versions read a following u64')
        report['legacyDisassembly'] = []
        for name, start, end in [('NsBaseCore10', 0x12d114, 0x12d130), ('NsDataModel10', 0x25ffd8, 0x260034)]:
            cached = Path('/tmp/kit-fusion-native-analysis') / (name + '.arm64.dylib')
            command = ['xcrun', 'llvm-objdump', '--disassemble', '--demangle', '--start-address=' + hex(start), '--stop-address=' + hex(end), str(cached)]
            report['legacyDisassembly'].append(dict(image=name, sha256=hashlib.sha256(cached.read_bytes()).hexdigest(), start=hex(start), end=hex(end), disassembly=subprocess.check_output(command, text=True).splitlines()[4:]))
        (BASE / 'NativeDrawing.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps({name: value['stringReferences'] for name, value in excerpts.items()}, indent=2))


if __name__ == '__main__':
    main()
