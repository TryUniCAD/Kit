import hashlib,json,runpy,struct
from pathlib import Path
BASE=Path(__file__).resolve().parent
API=runpy.run_path(str(BASE.parent/'ReadBinaryMembers.py'))
ROOT=Path('~/Library/Application Support/Autodesk/webdeploy/production/b43a07003c01dd54425db484d23b1c5e6248a21d/Autodesk Fusion.app/Contents/Libraries').expanduser()
asset=API['Binary'](ROOT/'libadskassetapi_new-16.dylib')
ns=API['Binary'](ROOT/'Neutron/NsTypes10.dylib')
def pointer(image,addr):return struct.unpack('<Q',image.read(addr,8))[0]&((1<<48)-1)
def literal(image,addr):return image.read(addr,80).split(b'\0')[0].decode('ascii')
assert pointer(asset,0x2c7590)==0x2a690
suffix=literal(asset,pointer(asset,0x2dc578))
assert suffix=='_Post2015'
record={
 'applicationVersion':'2706.1.17','architecture':'arm64','addressBasis':'Unslid Mach-O virtual address; authenticated chained pointer target shown without high fixup bits',
 'images':[{'path':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name in ('libadskassetapi_new-16.dylib','Neutron/NsTypes10.dylib')],
 'suffix':{'symbol':'autodesk::platform::assets::K_Suffix_Post2015_Asset_ID','pointerAddress':'0x2dc578','literalAddress':hex(pointer(asset,0x2dc578)),'value':suffix},
 'vtable':{'class':'autodesk::platform::assets::AssetDeSerializer','symbolAddress':'0x2c7548','addressPoint':'0x2c7558','slotOffset':'0x38','pointerAddress':'0x2c7590','methodAddress':hex(pointer(asset,0x2c7590))},
 'resolution':{'symbol':'AssetDeSerializer::ResolveAssetReference(IString const&, MultipleDataResolvingPriority)','address':'0x2a690','baseLookup':'0x2a6d8','suffixAppend':'0x2a6e4..0x2a6f8','suffixLookup':'0x2a704','requireBoth':'0x2a76c..0x2a770','priorityEqualsTwo':'0x2a774..0x2a778','renameSuffixToOriginal':'0x2a77c..0x2a784','selectSuffixResult':'0x2a788','meaning':'When both base and base+_Post2015 assets exist and priority is2, resolve to the suffixed asset and assign its runtime name to the original reference. When the original is absent the method returns null; it does not resolve a suffixed-only entry.'},
 'nativeCaller':{'symbol':'Ns::MaterialCatalogHolder::hydrateFromSnapshotST(MaterialCatalogPersistenceSnapshot const&, IAssetDeSerializer*)','address':'0x3b7ac','physicalLoop':'0x3b940..0x3b954','visualLoop':'0x3bc6c..0x3bc80','meaning':'Both loops call IAssetDeSerializer vtable0x38 with w2=2'},
 'productRule':'Resolve the base identity; if it exists, prefer the exactly suffixed identity. Validate selected asset role, definition ID and library ID exactly. Retain both original persisted asset names and every typed asset payload for re-emission; do not rewrite body identities.'
}
(BASE/'MaterialAliasEvidence.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
