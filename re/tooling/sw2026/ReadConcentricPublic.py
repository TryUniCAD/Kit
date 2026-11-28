from __future__ import annotations

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import os
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('choose a new public read receipt')
    request = json.load(sys.stdin)
    sys.path.insert(0, str(args.root.resolve(strict=True) / 'src'))
    from convert import open_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from interchange import frozen_mapping
    path = Path(request['path']).resolve(strict=True)
    if sha256(path.read_bytes()).hexdigest() != request['sha256']:
        raise ValueError('public read source changed')
    options = {} if request['mode'] == 'default' else {'include_brep': False, 'include_tessellation': False}
    if request.get('adapter_values') is None:
        document = open_document(path, **options)
    else:
        document = SldprtAdapter().read(path, ReadOptions(**options, values=request['adapter_values']))
    document.assert_valid()
    original = document.to_json(indent=None)
    metadata = dict(document.metadata)
    metadata.pop('solidworks.typed_mates_semantics', None)
    metadata.pop('solidworks_source_semantic_sha256', None)
    legacy = replace(document, metadata=frozen_mapping(metadata)).to_json(indent=None)
    assembly = document.assembly
    if assembly is None:
        raise ValueError('declared public source is not an assembly')
    instances = {value.id: value for value in assembly.instances}
    definitions = {value.id: value for value in assembly.definitions}
    children = {value.id: value.document for value in assembly.documents}
    result = {'schema': 'kit.sw2026.concentric-public-process-read.v1', 'passed': True,
        'process_id': os.getpid(), 'mode': request['mode'], 'source_sha256': document.source.sha256,
        'document_sha256': sha256(original.encode()).hexdigest(),
        'legacy_semantics_sha256': sha256(legacy.encode()).hexdigest(),
        'fallback_comparison_excluded_metadata': ['solidworks.typed_mates_semantics','solidworks_source_semantic_sha256'],
        'source_semantic_sha256': document.metadata.get('solidworks_source_semantic_sha256'),
        'typed_report': dict(document.metadata).get('solidworks.typed_mates_semantics'),
        'mates': [{'id':value.id, 'kind':str(value.kind), 'name':value.name, 'order':value.order,
            'entity_ids':value.entity_ids, 'alignment':str(value.alignment), 'value':None if value.value is None else value.value.value,
            'suppressed':value.suppressed, 'driving':value.driving, 'attributes':dict(value.attributes)} for value in assembly.mates],
        'entities': [{'id':value.id, 'kind':str(value.kind), 'instance_path':value.instance_path,
            'source_entity_id':value.source_entity_id, 'radius':value.radius, 'frame_present':value.frame is not None,
            'attributes':dict(value.attributes)} for value in assembly.mate_entities],
        'instances': [{'id':value.id, 'definition_id':value.definition_id, 'fixed':value.fixed,
            'name':value.name, 'reference_number':value.reference_number, 'configuration_name':value.configuration_name,
            'native_feature_id':value.attributes.get('native_feature_id')} for value in instances.values()],
        'children': [], 'native_processes_started': 0, 'writer_outputs': 0,
        'oracle_modules_imported': [name for name in sys.modules if name.split('.')[0] in ('win32com','pythoncom','FreeCAD','adsk')],
        'diagnostics': [{'code':value.code,'severity':str(value.severity),'message':value.message} for value in document.diagnostics]}
    for definition in definitions.values():
        if definition.document_id not in children:
            continue
        child = children[definition.document_id]
        surfaces = {value.id:value for value in child.brep.surfaces} if child.brep is not None else {}
        result['children'].append({'definition_id':definition.id, 'document_id':definition.document_id,
            'sha256':child.source.sha256, 'configuration_names':[value.name for value in child.configurations],
            'brep_present':child.brep is not None, 'geometry_faces': [] if child.brep is None else
                [{'id':face.id, 'surface_class':type(surfaces[face.surface_id]).__name__,
                    'radius':getattr(surfaces[face.surface_id],'radius',None)} for face in child.brep.faces]})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'passed':True,'sha256':sha256(args.output.read_bytes()).hexdigest(),
        'typed_status': None if result['typed_report'] is None else result['typed_report']['status'],
        'document_sha256':result['document_sha256']},sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'passed':False,'error_type':type(error).__name__,'error':str(error)},sort_keys=True))
        raise SystemExit(3)
