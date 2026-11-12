import hashlib
import json
import lzma
from pathlib import Path
import struct
import subprocess

binary = Path('/tmp/kit-fusion-native-analysis/libASMkern232.arm64.dylib')
output = Path(__file__).resolve().parent
payload = binary.read_bytes()
segments = []
position = 32
for index in range(struct.unpack_from('<I', payload, 16)[0]):
    command, size = struct.unpack_from('<II', payload, position)
    if command == 0x19:
        vmaddr, vmsize, fileoff, filesize = struct.unpack_from('<4Q', payload, position + 24)
        segments.append((vmaddr, filesize, fileoff))
    position += size

def offset(address):
    for start, size, fileoff in segments:
        if start <= address < start + size:
            return fileoff + address - start
    raise ValueError(f'Unmapped virtual address {address:x}')

def string(address):
    position = offset(address)
    return payload[position:payload.index(b'\0', position)].decode('ascii')

ranges = {
    'HISTORY_STREAM::save': (0x62ca60, 0x62cb64),
    'HISTORY_STREAM::get_current_state': (0x169e50, 0x169e74),
    'HISTORY_STREAM::get_delta_state': (0x169d70, 0x169d8c),
    'HISTORY_STREAM::set_delta_state': (0x169dd8, 0x169dfc),
    'HISTORY_STREAM::set_current_state': (0x169e74, 0x169eb8),
    'note_state': (0x16788c, 0x167b6c),
    'HISTORY_STREAM::tag': (0x161898, 0x161998),
    'HISTORY_STREAM::assign_tag': (0x161a88, 0x161b74),
    'HISTORY_STREAM::set_max_states_to_keep': (0x627848, 0x6278b4),
    'DELTA_STATE::save': (0x62cb64, 0x62ce2c),
    'DELTA_STATE::restore': (0x62dd20, 0x62dfc0),
    'DELTA_STATE::debug': (0x16379c, 0x163a24),
    'BULLETIN_BOARD::save': (0x62dfc0, 0x62e0f0),
    'BULLETIN_BOARD::restore': (0x62e0f0, 0x62e20c),
    'BULLETIN_BOARD::debug': (0x163a24, 0x163aa4),
    'BULLETIN::save': (0x62e280, 0x62e2f4),
}
disassembly = {}
for name, (start, stop) in ranges.items():
    disassembly[name] = subprocess.check_output([
        '/Library/Developer/CommandLineTools/usr/bin/llvm-objdump', '--disassemble', '--demangle',
        f'--start-address={start:#x}', f'--stop-address={stop:#x}', str(binary)
    ], text=True)
encoded = lzma.compress(json.dumps(disassembly, indent=2).encode())
(output / 'NativeDisassembly.json.xz').write_bytes(encoded)
statuses = []
for index in range(4):
    pointer = struct.unpack_from('<Q', payload, offset(0xb026a8) + 8 * index)[0]
    address = pointer & ((1 << 36) - 1)
    statuses.append({'value': index, 'name': string(address), 'stringAddress': hex(address), 'pointerWord': hex(pointer)})
report = {
    'schema': 'FusionHistoryNativeSemantics/1',
    'scope': 'Static disassembly and Mach-O data reads only; no application calls, product execution or tests',
    'binary': str(binary), 'binarySha256': hashlib.sha256(payload).hexdigest(),
    'architecture': 'arm64', 'product': 'ASM 232 bundled with Fusion 2706.1.17',
    'disassembly': {'path': 'NativeDisassembly.json.xz', 'sha256': hashlib.sha256(encoded).hexdigest(), 'ranges': {key: [hex(value) for value in pair] for key, pair in ranges.items()}},
    'preambleFields': [
        {'position': 0, 'name': 'currentStateId', 'nativeOffset': '0x90', 'save': ['0x62caa0', '0x62caa4'], 'proof': 'get_current_state loads object+0x90; set_current_state writes it subject to current <= maximum'},
        {'position': 1, 'name': 'maxStateId', 'nativeOffset': '0x94', 'save': ['0x62caa8', '0x62caac'], 'proof': 'note_state at 0x167a10..0x167a24 increments +0x94 then writes both +0x90 and +0x94; set_delta_state and set_current_state bound current by maximum'},
        {'position': 2, 'name': 'maxStatesToKeep', 'nativeOffset': '0x78', 'save': ['0x62cab0', '0x62cab4'], 'proof': 'named set_max_states_to_keep stores its int argument at +0x78; zero avoids the pruning loop'},
        {'position': 3, 'name': 'nextEntityTag', 'nativeOffset': '0x0', 'save': ['0x62cb5c', '0x62cae8'], 'proof': 'tag at 0x1618e4..0x161904 chooses this counter for an unspecified entity tag and stores chosenTag+1; assign_tag uses the same counter', 'qualification': 'native save option may emit -1 instead; existing production profiles require nonnegative entity-tag state'},
    ],
    'integerDomain': 'All four preamble scalars are native signed int values emitted by write_int(int); BinaryFile8 uses a signed 64-bit tagged wire slot',
    'boardStatus': {'nativeOffset': '0x50', 'save': '0x62dfc0', 'restore': '0x62e0f0 calls read_enum', 'debugLookup': '0x163a48..0x163a54 indexes four strings at 0xb026a8', 'values': statuses},
    'priorHypotheses': [
        {'claim': 'first two values are duplicated stream generation or stream size', 'status': 'refuted', 'reason': 'native accessor and state-allocation instructions prove distinct current and maximum state IDs; rolled_back stores 3 and 10'},
        {'claim': 'fourth value is history entry count, board allocation or stream identifier', 'status': 'refuted', 'reason': 'named tag and assign_tag mutate the exact saved object+0 counter for ENTITY tag allocation'},
        {'claim': 'board value is an ordinal identity', 'status': 'refuted', 'reason': 'restore reads an enum and debug maps values to mainline/stacked/succeeded/failed'},
    ],
    'oldApiMapping': {'HistoryState.Generation': 'CurrentStateId', 'HistoryState.Allocation': 'NextEntityTag', 'HistoryState.BoardNumber': 'BoardStatus', 'HistoryState.CurrentId': 'unchanged delta-state identity', 'HistoryState.InitialId': 'unchanged initial delta-state identity', 'newMaxStateId': 'defaults to CurrentStateId when omitted, is independently preserved when present'},
    'canonicalAuthoredPreamble': [4, 4, 0, 1, -1, 0, 1, -1],
    'canonicalBoardStatus': 2,
    'unresolvedGeneralFields': ['DELTA_STATE +0x15 boolean purpose', 'DELTA_STATE +0x48 state-list purpose', 'DELTA_STATE +0x50 state-reference purpose', 'HISTORY_STREAM +0x88 entity owner role', 'FPM_tracked_attrib_def payload identity role'],
    'externalResearch': {'repository': 'https://github.com/cadmpeg/cadmpeg', 'localClone': 're/Fusion/External/cadmpeg', 'commit': 'de2726870ff728352163f601ab4e60bbd54fbade', 'codeLicense': 'Apache-2.0', 'specLicense': 'CC-BY-4.0', 'use': 'Independent comparison of history framing and archived revision semantics; disputed preamble labels are superseded by the native evidence above'},
}
(output / 'NativeEvidence.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'binarySha256': report['binarySha256'], 'boardStatuses': statuses, 'disassemblySha256': report['disassembly']['sha256']}, indent=2))
