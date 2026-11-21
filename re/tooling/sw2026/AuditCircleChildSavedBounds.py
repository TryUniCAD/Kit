from pathlib import Path
from hashlib import sha256
import argparse,json,math,struct,sys


def main():
    parser=argparse.ArgumentParser()
    for name in ('root','packet','kernel-audit','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.root/'src'))
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylNodes import ReadCylNodes
    from convert.adapters.solidworks.Core.TypedMates.Cylinders.PickCylFace import PickCylFace
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.MakeBox import MakeBox
    assert sha256(args.kernel_audit.read_bytes()).hexdigest()=='2bd548351cdcb9ac1a3a4fe533a7184d63862a7f2b5954e82a2d1e2195cce80a'
    known={(r['case'],r['phase']):r for r in json.loads(args.kernel_audit.read_bytes())['rows']}

    def walk(value,seen=None):
        seen=set() if seen is None else seen
        if id(value) in seen:return
        seen.add(id(value))
        if isinstance(value,ArchiveNode):
            yield value
            yield from walk(value.FieldsValue,seen)
        elif isinstance(value,dict):
            for member in value.values():yield from walk(member,seen)
        elif isinstance(value,(list,tuple)):
            for member in value:yield from walk(member,seen)

    rows=[];reference_words=0;exact_words=0;hashes={}
    for case,name in [('D01','ConcentricD01AlignedFree'),('D02','ConcentricD02AlignedLocked'),('D03','ConcentricD03AntiFree')]:
        for phase in ('source','edited'):
            expected=known[(case,phase)];folder=args.packet/'Disclosed'/case/'Native'/phase.title()
            child=folder/(f'Concentric{case}Child.SLDPRT');parent=folder/(name+'.SLDASM')
            for path,key in ((child,'child_sha256'),(parent,'parent_sha256')):
                assert sha256(path.read_bytes()).hexdigest()==expected[key];hashes[str(path)]=expected[key]
            cl=ReadNativeLink(SldprtArchive.from_bytes(child.read_bytes()),0);pl=ReadNativeLink(SldprtArchive.from_bytes(parent.read_bytes()),0)
            nodes=ReadCylNodes(SldprtArchive.from_bytes(child.read_bytes()));face,surface,body=PickCylFace(nodes)
            planes=[node for node in nodes.values() if node.KindValue==50];assert len(planes)==2
            zvalues=[node.FieldsValue['pvec'][2] for node in planes]
            cx,cy,_=surface.FieldsValue['pvec'];radius=surface.FieldsValue['radius'];low=(cx-radius,cy-radius,min(zvalues));high=(cx+radius,cy+radius,max(zvalues));calculated=MakeBox(low,high)
            assert min(zvalues)==0 and max(zvalues)>0 and surface.FieldsValue['axis']==(-0.,-0.,-1.)
            actual=cl.ConfigValue.RootValue.FieldsValue['f7f8'];differences=[]
            for key,value in calculated.items():
                if struct.pack('<d',value)==struct.pack('<d',actual[key]):exact_words+=1
                else:
                    ulps=abs(value-actual[key])/math.ulp(actual[key]);assert ulps<=1
                    differences.append({'field':key,'calculated_hex':value.hex(),'stored_hex':actual[key].hex(),'absolute_m':abs(value-actual[key]),'ulps':ulps})
            references=[n for n in walk((pl.ConfigValue.RootValue,pl.ResolvedValue.RootsValue)) if n.ClassValue.NameValue=='moReference_c'];assert len(references)==2
            for reference in references:
                assert all(struct.pack('<d',reference.FieldsValue['f370'][key])==struct.pack('<d',value) for key,value in actual.items());reference_words+=10
            rows.append({'case':case,'phase':phase,'child_sha256':expected['child_sha256'],'parent_sha256':expected['parent_sha256'],'calculated_bbox':calculated,'stored_bbox':actual,'differences':differences,'reference_feature_ids':[n.FieldsValue['f08'] for n in references]})
    assert exact_words==58 and reference_words==120
    assert all(sha256(Path(path).read_bytes()).hexdigest()==value for path,value in hashes.items())
    result={'passed':True,'source_cases':3,'child_states':6,'exact_calculated_words':exact_words,'calculated_words':60,'reference_words_exact':reference_words,'sphere_words_exact':24,'max_difference_m':max(d['absolute_m'] for r in rows for d in r['differences']),'input_hashes':hashes,'source_unchanged':True,'rows':rows,'native_processes':0,'hidden_inputs_read':0,'writer_outputs':0}
    assert not args.output.exists();args.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n');print(json.dumps({'passed':True,'sha256':sha256(args.output.read_bytes()).hexdigest()}))


if __name__=='__main__':main()
