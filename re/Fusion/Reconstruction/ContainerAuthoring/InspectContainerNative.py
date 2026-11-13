import hashlib
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent
INSTALL = Path('~/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents/Libraries/Neutron').expanduser()
RANGES = {
    'NsBrowser10.dylib': [
        ('RelationshipsBrowserEntry::assyConstraints getter', 0x6A964, 0x6A9C0),
        ('RelationshipsBrowserEntry::appearance typed AssyConstraints virtual call', 0x6AA14, 0x6ABA8),
    ],
    'NsBaseCore10.dylib': [
        ('ZipPackage::buildFolderTree implicit direct parent construction', 0x200A64, 0x200B98),
        ('ZipPackage::buildFolderTree implicit ancestor construction', 0x200C40, 0x200D5C),
    ],
    'NsDataModel10.dylib': [
        ('SegmentBinaryMetaStreamer::initializeStream load path', 0x25FC6C, 0x25FECC),
        ('SegmentBinaryMetaStreamer::load initialization before stream reads', 0x25FF40, 0x260034),
        ('AssetImpl::segmentFolder lookup and creation', 0x2B938, 0x2B9D8),
        ('SegmentImpl::uniqueName lazy derivation', 0x267E38, 0x267EA4),
        ('SegmentImpl::uniqueSegmentFolderName occurrence suffix', 0x267EA4, 0x2680CC),
        ('BinaryBulkLoadVisitor::buildEntities ordered index traversal', 0x298780, 0x2988D0),
        ('BinaryBulkLoadVisitor::buildEntities nonpositive offset errors', 0x298BFC, 0x298CC0),
    ],
}


def main():
    report = {'scope': 'Static disassembly only; no library loading or native calls', 'architecture': 'arm64', 'addressBasis': 'Mach-O arm64 slice virtual address before slide', 'images': []}
    for filename, ranges in RANGES.items():
        path = INSTALL / filename
        text = subprocess.run(['otool', '-arch', 'arm64', '-tvV', str(path)], capture_output=True, text=True, check=True).stdout
        instructions = []
        for line in text.splitlines():
            try:
                address = int(line.split('\t')[0], 16)
            except ValueError:
                continue
            instructions.append((address, line))
        excerpts = [{'name': name, 'start': hex(start), 'endExclusive': hex(end), 'instructions': [line for address, line in instructions if start <= address < end]} for name, start, end in ranges]
        report['images'].append({'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'excerpts': excerpts})
    (BASE / 'NativeEvidence.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
