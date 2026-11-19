from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json


def digest(value):
    return sha256(value).hexdigest()


def main():
    parser=ArgumentParser()
    parser.add_argument('--kernel',type=Path,required=True)
    parser.add_argument('--bridge',type=Path,required=True)
    parser.add_argument('--record',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError('output already exists')
    record_raw=args.record.read_bytes()
    record=json.loads(record_raw)
    if record.get('schema')!='kit.sw2026.parasolid-receive-chain-source.v1':
        raise ValueError('source record identity differs')
    paths={'PSKERNEL.dll':args.kernel,'sldgciParau.dll':args.bridge}
    images={}
    modules=[]
    for module in record['modules']:
        raw=paths[module['name']].read_bytes()
        if len(raw)!=module['bytes'] or digest(raw)!=module['sha256']:
            raise ValueError('original module differs '+module['name'])
        images[module['name']]=raw
        modules.append({'name':module['name'],'sha256':digest(raw),'bytes':len(raw)})
    checked=[]
    for function in record['functions']:
        raw=images[function['module']]
        fragments=[]
        for fragment in function['fragments']:
            start=fragment['file_offset']
            data=raw[start:start+fragment['bytes']]
            if len(data)!=fragment['bytes'] or digest(data)!=fragment['sha256']:
                raise ValueError('original code interval differs '+function['name'])
            fragments.append({'start':fragment['start'],'end_exclusive':fragment['end_exclusive'],'bytes':len(data),'sha256':digest(data)})
        checked.append({'module':function['module'],'name':function['name'],'entry':function['entry'],'fragments':fragments})
    result={'schema':'kit.sw2026.parasolid-receive-chain-source-verification.v1','passed':True,'record_sha256':digest(record_raw),'tool_sha256':digest(Path(__file__).read_bytes()),'modules':modules,'functions':checked,'native_runs':0,'vendor_bytes_or_listings_published':False,'source_pin_verification_only':True,'complete_load_order_qualified':False}
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'functions':len(checked),'sha256':digest(args.output.read_bytes()),'native_runs':0}))


if __name__=='__main__':
    main()
