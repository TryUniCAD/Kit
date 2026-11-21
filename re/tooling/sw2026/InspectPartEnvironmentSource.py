import argparse
import hashlib
import json
import struct
from pathlib import Path


class Image:
    def __init__(self, path, expected):
        self.data = path.read_bytes()
        if hashlib.sha256(self.data).hexdigest() != expected:
            raise ValueError('original module identity differs: ' + path.name)
        pe = struct.unpack_from('<I', self.data, 60)[0]
        optional = pe + 24
        if self.data[pe:pe + 4] != b'PE\0\0':
            raise ValueError('missing PE signature')
        if struct.unpack_from('<H', self.data, pe + 4)[0] != 0x8664:
            raise ValueError('expected AMD64 original image')
        self.base = struct.unpack_from('<Q', self.data, optional + 24)[0]
        section_at = optional + struct.unpack_from('<H', self.data, pe + 20)[0]
        section_count = struct.unpack_from('<H', self.data, pe + 6)[0]
        self.sections = [struct.unpack_from('<8sIIII', self.data, section_at + 40 * i) for i in range(section_count)]
        self.directories = [struct.unpack_from('<II', self.data, optional + 112 + 8 * i) for i in range(16)]
        rva, size = self.directories[3]
        if size % 12:
            raise ValueError('invalid AMD64 exception directory size')
        self.functions = [struct.unpack_from('<III', self.data, self.offset(rva) + i) for i in range(0, size, 12)]

    def offset(self, rva):
        for _, virtual_size, address, raw_size, file_at in self.sections:
            if address <= rva < address + max(virtual_size, raw_size):
                if rva - address >= raw_size:
                    raise ValueError('range has no original file bytes')
                return file_at + rva - address
        raise ValueError('unmapped RVA: ' + hex(rva))

    def read(self, start, end):
        first = self.offset(start - self.base)
        last = self.offset(end - self.base - 1) + 1
        if last - first != end - start:
            raise ValueError('range crosses noncontiguous file mapping')
        return self.data[first:last]

    def root(self, record, seen=()):
        if record in seen:
            raise ValueError('cyclic unwind chain')
        at = self.offset(record[2])
        if self.data[at] >> 3 & 4:
            count = self.data[at + 2]
            chained = at + 4 + ((count + 1) & ~1) * 2
            return self.root(struct.unpack_from('<III', self.data, chained), seen + (record,))
        return record

    def verify_span(self, row):
        start = int(row['start'], 0)
        end = int(row['end_exclusive'], 0)
        data = self.read(start, end)
        if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('original span differs: ' + row.get('name', row['start']))

    def verify_function(self, row):
        self.verify_span(row)
        fragments = row['unwind_fragments']
        if not fragments:
            if any(self.base + r[0] <= int(row['start'], 0) < self.base + r[1] for r in self.functions):
                raise ValueError('leaf unexpectedly has declared unwind metadata')
            return
        first = next(r for r in self.functions if self.base + r[0] == int(fragments[0]['start'], 0))
        group = sorted(r for r in self.functions if self.root(r) == self.root(first))
        expected = [(int(r['start'], 0) - self.base, int(r['end_exclusive'], 0) - self.base, int(r['unwind_rva'], 0)) for r in fragments]
        if group != expected:
            raise ValueError('complete declared unwind group differs')
        for fragment in fragments:
            self.verify_span(fragment)

    def imports(self):
        def text(rva):
            at = self.offset(rva)
            return self.data[at:self.data.index(b'\0', at)].decode('ascii')
        rva, size = self.directories[1]
        result = {}
        for at in range(self.offset(rva), self.offset(rva) + size, 20):
            table, timestamp, forwarder, dll_at, iat = struct.unpack_from('<IIIII', self.data, at)
            if not any((table, timestamp, forwarder, dll_at, iat)):
                break
            index = 0
            while True:
                value = struct.unpack_from('<Q', self.data, self.offset(table or iat) + 8 * index)[0]
                if not value:
                    break
                name = 'ordinal:' + str(value & 65535) if value >> 63 else text(value + 2)
                result[hex(self.base + iat + 8 * index)] = {'module': text(dll_at), 'name': name}
                index += 1
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bin-directory', required=True, type=Path)
    parser.add_argument('--record', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    record = json.loads(args.record.read_text())
    images = {r['name']: Image(args.bin_directory / r['name'], r['sha256']) for r in record['modules']}
    for row in record['functions']:
        images[row['module']].verify_function(row)
    for row in record['instruction_windows'] + record['data_windows']:
        images[row['module']].verify_span(row)
    for row in record['imports']:
        actual = images[row['source_module']].imports()[row['iat']]
        if actual != {key: row[key] for key in ('module', 'name')}:
            raise ValueError('selected import differs')
    for row in record['vtable_cells']:
        actual = struct.unpack('<Q', images[row['module']].read(int(row['cell'], 0), int(row['cell'], 0) + 8))[0]
        if actual != int(row['target'], 0):
            raise ValueError('selected virtual target differs')
    result = {'verified': True, 'record_sha256': hashlib.sha256(args.record.read_bytes()).hexdigest(), 'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'modules': len(images), 'complete_functions': len(record['functions']), 'instruction_windows': len(record['instruction_windows']), 'data_windows': len(record['data_windows']), 'imports': len(record['imports']), 'vtable_cells': len(record['vtable_cells']), 'native_execution': False, 'cad_execution': False, 'schema_or_codec_execution': False, 'tests': False, 'acceptance': False}
    with args.output.open('x') as output:
        output.write(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
