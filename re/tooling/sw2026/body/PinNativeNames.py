from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
from struct import unpack_from


class Image:
    def __init__(self, path):
        self.path = path
        self.data = path.read_bytes()
        self.pe = unpack_from('<I', self.data, 0x3c)[0]
        if self.data[:2] != b'MZ' or self.data[self.pe:self.pe + 4] != b'PE\0\0':
            raise ValueError('not PE')
        self.sections_n = unpack_from('<H', self.data, self.pe + 6)[0]
        self.optional_n = unpack_from('<H', self.data, self.pe + 20)[0]
        self.optional = self.pe + 24
        if unpack_from('<H', self.data, self.optional)[0] != 0x20b:
            raise ValueError('not PE32+')
        self.base = unpack_from('<Q', self.data, self.optional + 24)[0]
        self.sections = []
        for i in range(self.sections_n):
            off = self.optional + self.optional_n + 40 * i
            virtual_n, rva, raw_n, raw_off = unpack_from('<IIII', self.data, off + 8)
            self.sections.append((rva, virtual_n, raw_off, raw_n))

    def offset(self, rva, size=1):
        matches = [raw + rva - start for start, virtual_n, raw, raw_n in self.sections
                   if start <= rva and rva + size <= start + raw_n]
        if len(matches) != 1:
            raise ValueError('unmapped or ambiguous original source range')
        return matches[0]

    def at(self, va, size):
        off = self.offset(va - self.base, size)
        return self.data[off:off + size]

    def text(self, rva):
        off = self.offset(rva)
        end = self.data.index(0, off)
        return self.data[off:end].decode('ascii')

    def exports(self):
        directory_rva = unpack_from('<I', self.data, self.optional + 112)[0]
        off = self.offset(directory_rva, 40)
        count, funcs, names, ords = unpack_from('<IIII', self.data, off + 24)
        names_off = self.offset(names, count * 4)
        ords_off = self.offset(ords, count * 2)
        for i in range(count):
            name = self.text(unpack_from('<I', self.data, names_off + 4 * i)[0])
            ordinal = unpack_from('<H', self.data, ords_off + 2 * i)[0]
            rva = unpack_from('<I', self.data, self.offset(funcs + 4 * ordinal, 4))[0]
            yield name, self.base + rva

    def lea_literal(self, va):
        code = self.at(va, 7)
        if code[:3] not in (b'\x48\x8d\x0d', b'\x48\x8d\x15'):
            raise ValueError('not the expected RIP-relative LEA')
        address = va + 7 + unpack_from('<i', code, 3)[0]
        return {'va': hex(address), 'file_offset': self.offset(address - self.base),
                'ascii': self.text(address - self.base)}


def main():
    parser = ArgumentParser()
    parser.add_argument('--binaries', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    pins = {}
    for name in ('sldgcu.dll', 'sldgciParau.dll', 'sldmodu.dll'):
        image = Image(args.binaries / name)
        entries = tuple(image.exports())
        pins[name] = {'sha256': sha256(image.data).hexdigest(), 'bytes': len(image.data),
                      'image_base': hex(image.base),
                      'body_name_exports': {symbol: hex(address) for symbol, address in entries
                                            if ('Name' in symbol or 'name' in symbol)
                                            and ('Body' in symbol or 'Atom' in symbol)}}
        if name == 'sldgcu.dll':
            ranges = ((0x43890a30, 0x43890b46), (0x438a43b0, 0x438a4482),
                      (0x43893570, 0x4389361b), (0x43893620, 0x4389364c),
                      (0x43e86230, 0x43e8625d))
            pins[name]['ranges'] = [{'start': hex(start), 'end_exclusive': hex(end),
                                    'file_offset': image.offset(start - image.base, end - start),
                                    'sha256': sha256(image.at(start, end - start)).hexdigest()}
                                   for start, end in ranges]
            pins[name]['getter_literals'] = [image.lea_literal(0x43890a4d),
                                              image.lea_literal(0x43890a76)]
    args.output.write_text(dumps(pins, indent=2, sort_keys=True) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
