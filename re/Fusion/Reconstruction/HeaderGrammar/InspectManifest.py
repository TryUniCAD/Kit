import hashlib
import json
from pathlib import Path
import subprocess

original = Path('/Users/odin/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents/Libraries/Neutron/NsDataModel10.dylib')
thin = Path('/tmp/kit-fusion-native-analysis/NsDataModel10.arm64.dylib')
if not thin.exists():
    subprocess.run(['lipo', '-thin', 'arm64', str(original), '-output', str(thin)], check=True)
ranges = [('asset_identity_revision', 0xced40, 0xced98), ('asset_migrator_versions', 0xceddc, 0xcee40), ('segment_allocation_watermark', 0xcf0f8, 0xcf130), ('segment_declarations', 0xcf1c8, 0xcf228), ('document_type_names', 0xcf99c, 0xcfa24), ('document_identity_current_version', 0xcfdd0, 0xcfe98), ('document_migrator_versions', 0xcfe98, 0xcfed4), ('document_version_history', 0xcffac, 0xd0028), ('next_segment_id_getter', 0x2ab5c, 0x2ab78), ('next_segment_id_return', 0x2ac90, 0x2acb0)]
excerpts = []
for name, start, end in ranges:
    data = subprocess.check_output(['xcrun','llvm-objdump','--disassemble','--demangle',f'--start-address={start}',f'--stop-address={end}',str(thin)],text=True)
    excerpts.append({'name':name,'start':hex(start),'end':hex(end),'disassembly':data.splitlines()})
report = {'scope':'Static manifest semantics, no native library loading or tests','source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'thin_sha256':hashlib.sha256(thin.read_bytes()).hexdigest(),'architecture':'arm64','roles':{'root_uuid_first':'Document.identifier','root_uuid_second':'Document.currentVersion','root_name_description':'DocumentType.name and DocumentType.description, not authored document title','extension_versions':'persistedMaxMigratorNumbers constrained by type maxMigratorNumbers','asset_uuid_first':'SaveContext.getSavedGuid(asset)','asset_uuid_second':'Asset.revisionGuid','segment_preamble_word':'AssetImpl.getNextAvailableSegId(false), allocator watermark from AssetImpl+0x48','segment_row':'Segment.id, Segment.userName, SegmentType.identifier'},'excerpts':excerpts}
Path(__file__).with_name('ManifestNative.json').write_text(json.dumps(report,indent=2)+'\n')
