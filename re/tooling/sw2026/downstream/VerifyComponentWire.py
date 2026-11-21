from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json


def digest(value):
    return sha256(value).hexdigest()


def main():
    parser=ArgumentParser()
    parser.add_argument('--bin-directory',type=Path,required=True)
    parser.add_argument('--record',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError('output exists')
    wire=args.record.read_bytes()
    record=json.loads(wire)
    if record.get('schema')!='kit.sw2026.downstream-component-wire-source.v1':
        raise ValueError('source record identity differs')
    images={}
    for row in record['modules']:
        raw=(args.bin_directory/row['name']).read_bytes()
        if len(raw)!=row['bytes'] or digest(raw)!=row['sha256']:
            raise ValueError('original module differs '+row['name'])
        images[row['name']]=raw
    def check(module,pin):
        data=images[module][pin['file_offset']:pin['file_offset']+pin['bytes']]
        if len(data)!=pin['bytes'] or digest(data)!=pin['sha256']:
            raise ValueError('source interval differs '+pin['name'])
    for row in record['functions']:
        for pin in row['fragments']:
            check(row['module'],pin)
    for row in record['runtime_classes']:
        check('sldmodu.dll',row['descriptor_pin'])
        check('sldmodu.dll',row['serialize_slot_pin'])
    result={'schema':'kit.sw2026.downstream-component-source-verification.v1','passed':True,'record_sha256':digest(wire),'tool_sha256':digest(Path(__file__).read_bytes()),'verified_modules':len(images),'complete_function_entries':len(record['functions']),'runtime_descriptors':len(record['runtime_classes']),'serialize_cells':len(record['runtime_classes']),'source_pin_verification_only':True,'native_runs':0,'cad_inputs_read':0,'vendor_bytes_or_listings_published':False,'full_native_admission_qualified':False}
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'passed':True,'sha256':digest(args.output.read_bytes()),'source_only':True}))


if __name__=='__main__':
    main()
