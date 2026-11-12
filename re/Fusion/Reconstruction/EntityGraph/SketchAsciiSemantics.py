import collections
import hashlib
import json
import lzma
import runpy
import subprocess
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
BINARY = Path('/tmp/kit-fusion-native-analysis/NsASMInterface10.arm64.dylib')
DECODER = runpy.run_path(str(BASE.parent / 'BrepTokens.py'))['read_stream']


def corpus():
    inventory_path = BASE.parent / 'BrepCoverage/Inventory.json.xz'
    inventory = json.loads(lzma.decompress(inventory_path.read_bytes()))
    seen = set()
    versions = collections.Counter()
    directions = collections.Counter()
    flags = collections.Counter()
    splits = collections.Counter()
    secondary_ids = collections.Counter()
    examples = []
    example_keys = set()
    outside = []
    total = 0
    largest_primary = 0
    for entry in inventory['members']:
        if entry['sha256'] in seen:
            continue
        seen.add(entry['sha256'])
        with zipfile.ZipFile(ROOT / entry['path']) as archive:
            payload = archive.read(entry['member'])
        if hashlib.sha256(payload).hexdigest() != entry['sha256']:
            raise ValueError('Source member digest changed')
        parsed = DECODER(payload)
        for record in parsed['records']:
            if record['name'] != 'ATTRIB_CUSTOM-attrib':
                continue
            values = [item['value'] for item in record['fields']]
            if values[5] != 'sketch_attrib_def':
                continue
            versions[values[8]] += 1
            if values[8] != 3:
                continue
            if len(values) != 10:
                raise ValueError('Unexpected ASCII sketch attribute layout')
            parts = [int(part) for part in values[9].split(' ')]
            if len(parts) != 6:
                raise ValueError('ASCII sketch attribute lacks six fields')
            primary, secondary, direction, roleflags, sequence, count = parts
            total += 1
            largest_primary = max(largest_primary, primary)
            directions[direction] += 1
            flags[roleflags] += 1
            splits[(sequence, count)] += 1
            secondary_ids[secondary] += 1
            invalid = not (0 <= primary < 1 << 64 and 0 <= secondary < 1 << 64 and 0 <= roleflags < 1 << 64 and direction in (0, 1, 4294967295) and 1 <= sequence <= count < 1 << 32)
            sample = dict(path=entry['path'], member=entry['member'], sha256=entry['sha256'], physicalRecordIndex=record['physical_record_index'], byteOffset=record['offset'], text=values[9])
            if invalid:
                outside.append(sample)
            example_key = (bool(secondary), roleflags, sequence, count, direction)
            if (roleflags or secondary or (sequence, count) != (1, 1) or direction == 4294967295) and example_key not in example_keys and len(examples) < 24:
                example_keys.add(example_key)
                examples.append(sample)
    return dict(scope='Every sketch attribute including archived revisions in each distinct ASM blob; repeated member digests counted once', sourceInventorySha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(), distinctBlobs=len(seen), versionCounts=dict(versions), asciiAttributes=total, maximumPrimaryId=largest_primary, secondaryIdCounts=dict(secondary_ids), directionCounts=dict(directions), roleFlagsCounts=dict(flags), splitPairs=[dict(sequence=key[0], total=key[1], count=value) for key, value in sorted(splits.items())], nontrivialExamples=examples, outsideSemanticDomain=outside)


def main():
    ranges = [('attributeSave', '0xdb9a0', '0xdb9dc'), ('asciiSave', '0xdc8d8', '0xdc9bc'), ('asciiRestore', '0xdcbc8', '0xdccc4'), ('binarySave', '0xdd1cc', '0xdd274'), ('compareDirection', '0xdc8bc', '0xdc8d8'), ('exactMatch', '0xde724', '0xde7b0')]
    disassembly = {name: subprocess.check_output(['xcrun', 'llvm-objdump', '--disassemble', '--demangle', '--start-address=' + start, '--stop-address=' + end, str(BINARY)], text=True) for name, start, end in ranges}
    indirect = subprocess.check_output(['xcrun', 'llvm-objdump', '--macho', '--indirect-symbols', str(BINARY)], text=True)
    stubs = [line for line in indirect.splitlines() if line.startswith(tuple('0x0000000000' + address for address in ('1065d0', '1065dc', '1077a0', '1077ac', '107878', '107890')))]
    rows = [('primaryId', '0x8', 'uint64', '0xdc908', '0xdc910', '0xdcc8c', '0xdcc90'), ('secondaryId', '0x10', 'uint64', '0xdc924', '0xdc928', '0xdcc94', '0xdcc98'), ('direction', '0x18', 'uint32', '0xdc93c', '0xdc940', '0xdcc9c', '0xdcca0'), ('topologyRoleFlags', '0x20', 'uint64', '0xdc954', '0xdc958', '0xdcca4', '0xdcca8'), ('splitSequenceId', '0x28', 'uint32', '0xdc96c', '0xdc970', '0xdccac', '0xdccb0'), ('splitTotalNumber', '0x2c', 'uint32', '0xdc984', '0xdc988', '0xdccb4', '0xdccb8')]
    report = dict(schema='FusionSketchAsciiSemantics/1', method='Read-only native symbol/disassembly and raw corpus token inspection; no native calls, product execution or tests', binary=str(BINARY), binarySha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(), asciiFields=[dict(position=index, name=name, objectOffset=offset, nativeType=kind, loadAddress=load, outputCall=output, inputTarget=target, inputCall=input_call) for index, (name, offset, kind, load, output, target, input_call) in enumerate(rows, 1)], binaryStreamerOrder=['version', 'primaryId', 'secondaryId', 'direction', 'splitSequenceId', 'splitTotalNumber', 'topologyRoleFlags'], qualifiedDomain=dict(primaryId='uint64 storage; source-key allocation semantics separately qualified', secondaryId='uint64 storage; existing authored ordinary sketch profile zero', direction=[0, 1, 4294967295], topologyRoleFlags='uint64 mask; existing ordinary authored profile zero; complete named bit dictionary unresolved', split='1 <= splitSequenceId <= splitTotalNumber <= UINT32_MAX'), semanticEvidence=['SketchTagSemantics.json', 'SketchSplitSemantics.json'], caveats=['The first/second identity and flags values use unsigned64 ostream and istream overloads, not signed64', 'The fourth ASCII field is loaded from the actual topologyRoleFlags member; it is not an inserted constant', 'Split sequence and total are ordinal/count, not two unrelated enums', 'ASCII version3 and fixed binary Design streamer use different member orders', 'Older <=2 kernel forms use signed integer reads; version2 places flags after ordinal/count, while earlier forms omit flags', 'topologyRoleFlags is a behavior-based name from existing evidence; exact native source member name and complete bit meanings remain unresolved'], importStubs=stubs, corpus=corpus(), disassembly=disassembly)
    report['directionReversal'] = dict(nativeComparison='compareDirection0xdc8bc accepts equal values or UINT32_MAX in either operand; exactMatch0xde768..0xde784 repeats wildcard branches', proposedMapping={'0': 1, '1': 0, '4294967295': 4294967295}, evidenceClass='Semantic inference from native wildcard comparison; not a traced native reversal implementation', symbolSearch=['NsASMInterface10', 'NsASMEntityTracking10', 'NaFusion10', 'NaTagUtility10'], namedSketchTagReverseOrFlipMethodFound=False, limitation='Absence of a named symbol does not rule out inlined reversal logic')
    output = BASE / 'SketchAsciiSemantics.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report['corpus'], indent=2))


if __name__ == '__main__':
    main()
