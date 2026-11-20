from __future__ import annotations

import argparse
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys


def pocket_support_comparison(document):
    from convert.adapters.base.NativeEvidence import KRefSupportSource
    from convert.adapters.solidworks.Core.Adapter import KSourceSemanticShaTwoFive, SemanticShaTwo
    from interchange.serialization.EncodeData import ToData

    stock, profile = document.sketches
    fields = dict(profile.attributes)
    if (
        fields.pop("support_plane_source") != KRefSupportSource
        or fields.pop("unframed_support_plane_native_id") is not None
        or not fields.get("typed_archive_owner")
        or not any(
            plane.id == profile.support_plane_id
            and plane.attributes.get("native_object_id") == fields.get("support_plane_native_id")
            for plane in document.support_planes
        )
        or document.metadata[KSourceSemanticShaTwoFive] != SemanticShaTwo(document)
    ):
        raise ValueError("circle support provenance does not bind its archived plane")
    prior = replace(document, sketches=(stock, replace(profile, attributes=fields)))
    prior = replace(prior, metadata={**prior.metadata, KSourceSemanticShaTwoFive: SemanticShaTwo(prior)})
    canonical = json.dumps(ToData(prior), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return {"prior_shape_sha256": sha256(canonical).hexdigest(), "support_source": KRefSupportSource}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('root',type=Path)
    parser.add_argument('phase',choices=('input','read'))
    parser.add_argument('--kind',choices=('prism','pocket','revolve'),default='prism')
    parser.add_argument('--compare-pocket-support', action='store_true')
    args=parser.parse_args()
    root=args.root.resolve(strict=True)
    sys.path[:0]=[str(root/'src'),str(root)]
    from interchange.serialization.EncodeData import ToData
    from interchange.serialization.Deserialize import FromData
    if args.phase=='input':
        if args.kind=='prism':
            from tests.Convert.Solidworks.Research.Construction.Part.MakePlainDoc import MakePlainDoc
            document=MakePlainDoc('ColdCircleCompatPrism',31.7,18.9,11.3)
        elif args.kind=='pocket':
            sys.path.insert(0,str(root/'re/tooling/sw2026'))
            from AuthorSdkPocketInputs import neutral_document
            document=neutral_document('ColdCircleCompatPocket',61.7,37.9,14.3,(2.3,-1.7),4.1,3.8,None)
        else:
            sys.path.insert(0,str(root/'re/tooling/sw2026/revolve/Construction'))
            from MakeRevolveRequest01 import make_request
            document,_=make_request({'name':'ColdCircleCompatRevolve','radial_mm':[7.31,19.17],'axial_mm':[-9.2,24.8],'axis_x_mm':-4.11,'axis_span_mm':[-20.0,36.0],'angle_deg':147.3,'reverse':True,'edit_angle_deg':213.7,'created_at':1765500071,'self_path':'C:/KitSdkCandidates/ColdCircleCompatRevolve.SLDPRT'})
        print(json.dumps({'kind':args.kind,'document':ToData(document),'created_at':1765500071},sort_keys=True))
        return 0
    from convert import open_document
    from convert.api.ApiContext import GetRegistry
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
    from convert.adapters.solidworks.Archive.Construction.Part.MakePocketPart import MakePocketPart
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPlain import ProjectPlain
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectPocket import ProjectPocket
    from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import ProjectRevolve
    from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevPart import MakeRevPart
    from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
    request=json.load(sys.stdin)
    document=FromData(request['document'])
    GetRegistry()
    for name in ('utf-16-le','utf-8','latin-1'):lookup(name)
    audit=BuildAudit(root/'re/tooling/sw2026/serial/defs')
    sys.addaudithook(audit.InspectEvent)
    kind=request['kind']
    if kind=='prism':
        candidate=MakeBlindPart(document,MakePartRecipe(ProjectPlain(document),request['created_at']))
    elif kind=='pocket':
        candidate=MakePocketPart(document,MakePartRecipe(ProjectPocket(document).BossValue,request['created_at']))
    else:candidate=MakeRevPart(document,MakePartRecipe(ProjectRevolve(document),request['created_at']))
    actual=open_document(candidate.BytesValue,source_format='solidworks.sldprt')
    if args.compare_pocket_support and kind != 'pocket':
        raise ValueError("support comparison requires the pocket case")
    support = pocket_support_comparison(actual) if args.compare_pocket_support else {}
    if actual.brep is None or actual.brep_payloads or audit.DeniedReads or actual.validate():raise ValueError('legacy cold geometry or file boundary failed')
    canonical=json.dumps(ToData(actual),sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    topology=actual.bodies[0].topology
    print(json.dumps({'passed':True,'kind':kind,'generated_sha256':sha256(candidate.BytesValue).hexdigest(),'document_sha256':sha256(canonical).hexdigest(),'solid_count':topology.solid_count,'faces':len(actual.brep.faces),'edges':len(actual.brep.edges),'vertices':len(actual.brep.vertices),'volume_mm3':topology.volume,'area_mm2':topology.surface_area,'runtime_data_file_reads':len(audit.DeniedReads),'native_processes_started':0,'hidden_inputs_read':0,**support},sort_keys=True,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
