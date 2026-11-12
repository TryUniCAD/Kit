import json,runpy
from pathlib import Path
BASE=Path(__file__).resolve().parent
m=runpy.run_path(str(BASE/'InspectNative.py'));b=m['TOOLS']['Binary'](m['APP']/m['RELATIVE'])
records=[
 ('weighted-point','Exported Grip_point3d copies all 32 bytes (four f64) from surface grip array; native validation reads fourth scalar +0x18 and compares it with zero before the grip-weight diagnostic; native PlaneEdited retains weight 1.0000000000000002. Finite positive weights are preserved without normalization',[(0x856874,32),(0x5f9e4c,20),(0x5f9ee4,12)]),
 ('extension-crease','tskern::ExCrease namespace 100, writer 0x177684, reader 0x177918',[(0x178da4,8),(0x1776b4,8),(0x1776f8,8)]),
 ('extension-smart-grip','tskern::ExSmartGrip namespace 50000; ordered grip-index set, not UI selection or freezing',[(0x19f1dc,8),(0x19d048,4),(0x55373c,20),(0x553770,12)]),
 ('extension-freeze','Distinct tskern::ExFreeze namespace 50001, unsupported by qualified codec',[(0x189b14,8)]),
 ('extension-symmetry','tskern::ExSymmetry namespace 105, virtual per-reflection writer, mode 0 qualified',[(0x1b7c6c,8),(0x1aead4,24)]),
 ('edge-end-condition','ec is edge key + f64 end-condition value; same tree queried by exported Edge_hasEndCondition and Edge_endCondition',[(0x7fccd0,12),(0x7fcd18,4),(0x7fcd8c,20),(0x83b124,12),(0x83b1a8,8)]),
 ('link-order','TSM link values are native struct offsets 0/4/8/12/16/20/24; exported Link_prev reads +0; previous precedes next',[(0x7fc99c,4),(0x7fca14,4),(0x85aa40,12)]),
 ('link-valence-offset','Serialized final link u32 low two bits are exported Link_valenceOffset; unproved higher bits rejected',[(0x7fcc68,8),(0x85ae90,16)]),
 ('face-hidden','Serialized face second u32 bit 0 is exported tsdebug_Face_isHidden; unproved higher bits rejected',[(0x7fc538,8),(0x86ea08,12)]),
 ('vertex-orientation','Vertex textual NORTH/EAST/SOUTH/WEST value is native Vert_orientDirection at vertex struct+4',[(0x7fc8a0,16),(0x8687cc,12)]),
 ('central-grip','gvp selected when vertex-to-central-grip index equals current grip; same reciprocal maps used by Grip_isCentral',[(0x6eb3b4,24),(0x8569d8,12)]),
 ('compound-grip','cg stores vertex, spoke count, signed spoke lengths, then grip-index map; internal debug names SpokeLengths/SpokeEndI/SpokeMap corroborate',[(0x6eb538,4),(0x6eb57c,4),(0x6eb604,12),(0x6eb6d4,16)])]
report={'image':m['RELATIVE'],'image_sha256':b.sha256,'application_version':'2706.1.17','architecture':'arm64','address_basis':'Unslid Mach-O virtual address','scope':'Minimal static instruction evidence; no execution of vendor binaries; interpretation linked to exported function names and RTTI','fields':[]}
for name,meaning,ranges in records:
 report['fields'].append({'field':name,'meaning':meaning,'evidence':[{'address':hex(addr),'bytes_hex':b.read(addr,count).hex()} for addr,count in ranges]})
(BASE/'FieldEvidence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'fields':len(records),'instruction_bytes':sum(n for _,_,ranges in records for _,n in ranges)}))
