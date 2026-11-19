from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import csv
import io
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))

ORACLE = '3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe'
LIBRARIES = {'sldworks': '{83A33D31-27C5-11CE-BFD4-00400513BB57}',
             'swconst': '{4687F359-55D0-4CD3-B6CF-2EB42C11F989}'}
MEMBERS = {
    'ISldWorks': ('GetProcessID', 'RevisionNumber', 'GetDocumentCount', 'GetMaterialDatabases', 'GetMaterialSchemaPathName', 'ExitApp'),
    'IPartDoc': ('SetMaterialPropertyName2', 'GetMaterialPropertyName2', 'GetMaterialVisualProperties',
                 'SetMaterialVisualProperties', 'MaterialPropertyValues', 'GetBodies2'),
    'IBody2': ('GetMaterialPropertyName', 'GetMaterialIdName2', 'GetMaterialUserName2', 'SetMaterialProperty',
               'RemoveMaterialProperty', 'GetType'),
    'IModelDoc2': ('Parameter', 'ForceRebuild3'),
    'IDimension': ('SetSystemValue3', 'SystemValue', 'DrivenState', 'ReadOnly'),
    'IMassProperty': ('UseSystemUnits', 'Density', 'Mass', 'Volume', 'SurfaceArea', 'CenterOfMass'),
}
ENUMS = ('swBodyMaterialApplicationError_e', 'swBodyType_e')


def require(value, message):
    if not value:
        raise ValueError(message)


def read(obj, name):
    value = getattr(obj, name)
    return value() if callable(value) and not hasattr(value, '_oleobj_') else value


def application_pids():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq SLDWORKS.exe', '/FO', 'CSV', '/NH'],
                            text=True, capture_output=True, check=True)
    return {int(row[1].replace(',', '')) for row in csv.reader(io.StringIO(result.stdout))
            if len(row) > 1 and row[0].casefold() == 'sldworks.exe'}


def metadata(pythoncom):
    interfaces, enums, libraries = {}, {}, {}
    for key, guid in LIBRARIES.items():
        library = pythoncom.LoadRegTypeLib(guid, 34, 0, 0)
        attr = library.GetLibAttr()
        require(tuple(attr[3:5]) == (34, 0), 'registered type-library version differs')
        libraries[key] = {'guid': str(attr[0]), 'major': attr[3], 'minor': attr[4]}
        for index in range(library.GetTypeInfoCount()):
            info = library.GetTypeInfo(index); name = info.GetDocumentation(-1)[0]; typeattr = info.GetTypeAttr()
            if key == 'sldworks' and name in MEMBERS:
                rows = []
                for ordinal in range(typeattr.cFuncs):
                    desc = info.GetFuncDesc(ordinal); names = list(info.GetNames(desc.memid))
                    if names and names[0] in MEMBERS[name]:
                        rows.append({'names': names, 'member_id': desc.memid, 'invoke_kind': desc.invkind,
                                     'argument_types': repr(desc.args), 'return_type': repr(desc.rettype)})
                interfaces[name] = {'iid': str(typeattr[0]), 'members': rows,
                                    'missing': sorted(set(MEMBERS[name]) - {row['names'][0] for row in rows})}
            if key == 'swconst' and name in ENUMS:
                values = {}
                for ordinal in range(typeattr.cVars):
                    desc = info.GetVarDesc(ordinal); names = info.GetNames(desc.memid)
                    if type(desc.value) is int:
                        values[names[0]] = desc.value
                enums[name] = values
    require('ISldWorks' in interfaces and not interfaces['ISldWorks']['missing'], 'registered application getter/exit shapes incomplete')
    return {'libraries': libraries, 'interfaces': interfaces, 'enums': enums,
            'all_requested_member_shapes_present': all(name in interfaces and not interfaces[name]['missing'] for name in MEMBERS)}


def local(tag):
    return str(tag).rsplit('}', 1)[-1]


def bounded(value):
    return str(value)[:512]


def file_identity(path):
    if not path.is_file():
        return {'path': str(path), 'exists': False}
    require(path.stat().st_size <= 32 * 1024 * 1024, 'installed material metadata file exceeds bounded read')
    raw = path.read_bytes()
    return {'path': str(path), 'exists': True, 'bytes': len(raw), 'sha256': sha256(raw).hexdigest()}


def database_metadata(path):
    record = file_identity(path)
    if not record['exists']:
        return record
    try:
        tree = ET.fromstring(path.read_bytes())
        record.update(root_tag=tree.tag, root_attributes={k: bounded(v) for k, v in tree.attrib.items()},
                      material_count=0, density_entries=[])
        selected = set()
        for material in tree.iter():
            if local(material.tag).lower() != 'material':
                continue
            record['material_count'] += 1
            props = next((node for node in material if local(node.tag).lower() == 'physicalproperties'), None)
            if props is None:
                continue
            density = next((node for node in props if local(node.tag).upper() == 'DENS'), None)
            if density is None:
                continue
            raw_value = next((node.text or '' for node in density if local(node.tag).lower() == 'value'), '').strip()
            if raw_value in selected or len(record['density_entries']) >= 2:
                continue
            selected.add(raw_value)
            record['density_entries'].append({
                'material_name': bounded(material.get('name', '')),
                'material_attributes': {k: bounded(v) for k, v in material.attrib.items()},
                'physical_properties_attributes': {k: bounded(v) for k, v in props.attrib.items()},
                'property_code': local(density.tag), 'raw_value': bounded(raw_value),
                'density_attributes': {k: bounded(v) for k, v in density.attrib.items()},
                'density_child_metadata': [{'tag': local(node.tag), 'text': bounded(node.text or ''),
                                             'attributes': {k: bounded(v) for k, v in node.attrib.items()}}
                                            for node in density],
                'density_si_interpretation': 'unqualified until source/schema unit rule is bound',
            })
        record['xml_parsed'] = True
    except Exception as error:
        record.update(xml_parsed=False, parse_error=repr(error))
    require(file_identity(path) == {key: record[key] for key in ('path', 'exists', 'bytes', 'sha256')},
            'installed database changed during read-only metadata query')
    return record


def schema_metadata(path):
    record = file_identity(path)
    if not record['exists']:
        return record
    try:
        tree = ET.fromstring(path.read_bytes())
        record.update(root_tag=tree.tag, root_attributes={k: bounded(v) for k, v in tree.attrib.items()},
                      selected_declarations=[])
        for node in tree.iter():
            if node.get('name', '').lower() in ('dens', 'physicalproperties', 'units', 'unit', 'material', 'materials'):
                record['selected_declarations'].append({'tag': local(node.tag),
                                                        'attributes': {k: bounded(v) for k, v in node.attrib.items()},
                                                        'documentation': [bounded(child.text or '') for child in node.iter()
                                                                          if local(child.tag) == 'documentation']})
        record['xml_parsed'] = True
    except Exception as error:
        record.update(xml_parsed=False, parse_error=repr(error))
    require(file_identity(path) == {key: record[key] for key in ('path', 'exists', 'bytes', 'sha256')},
            'installed schema changed during read-only metadata query')
    return record


def wrapper_identity():
    from win32com.client import gencache
    module = gencache.GetModuleForTypelib(LIBRARIES['sldworks'], 0, 34, 0)
    path = Path(module.__file__)
    if path.suffix == '.pyc':
        import importlib.util
        path = Path(importlib.util.source_from_cache(str(path)))
    require(path.is_file(), 'existing registered generated wrapper source unavailable')
    return {'name': path.name, 'bytes': path.stat().st_size, 'sha256': sha256(path.read_bytes()).hexdigest()}


def capture(output, launch_fresh):
    require(os.name == 'nt', 'capture runs only in the root-owned Windows oracle')
    require(not output.exists(), 'unused metadata output path required')
    import pythoncom
    import win32com.client
    from win32api import OpenProcess
    from win32event import WaitForSingleObject, WAIT_OBJECT_0
    from OracleIdentity import application_identity

    pythoncom.CoInitialize()
    app = handle = None
    owned = False
    result = {'schema': 'kit.sw2026.assigned-material-catalog-metadata.v1', 'passed': False,
              'inspection_scope': 'registered type metadata and installed database/schema metadata only',
              'native_processes_started': 0, 'model_documents_opened': 0,
              'model_documents_created': 0, 'model_rebuilds': 0, 'model_saves': 0,
              'preferences_written': 0, 'license_process_actions': 0, 'heldout_inputs_read': 0,
              'catalog_binding_ready': False, 'cleanup': {'exit_requested': False, 'exit_confirmed': False},
              'tool_sha256': {name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                              for name in ('CaptureMaterialCatalog.py', 'OracleIdentity.py')}}
    try:
        result['metadata'] = metadata(pythoncom)
        result['wrapper'] = wrapper_identity()
        if launch_fresh:
            before = application_pids()
            result['processes_before'] = sorted(before)
            require(not before, 'existing SOLIDWORKS processes prevent a fresh owned launch')
            app = win32com.client.DispatchEx('SldWorks.Application.34')
            pid = int(read(app, 'GetProcessID'))
            require(pid > 0 and application_pids() == {pid}, 'COM did not yield exactly one fresh owned process')
            handle = OpenProcess(0x00100000, False, pid)
            owned = True
            result['native_processes_started'] = 1
            identity = application_identity(app)
            result['identity'] = identity
            require(identity['process_id'] == pid and identity['sha256'] == ORACLE and identity['version_matches'], 'oracle executable differs')
            require(str(read(app, 'RevisionNumber')) == '34.5.2', 'oracle revision differs')
            result['document_count_before'] = int(read(app, 'GetDocumentCount'))
            require(result['document_count_before'] == 0, 'owned oracle is not document-idle')
            databases = read(app, 'GetMaterialDatabases')
            require(databases is None or isinstance(databases, (list, tuple)), 'database getter returned an unexpected type')
            paths = list(databases or ())
            require(len(paths) <= 64 and all(isinstance(path, str) for path in paths), 'material database list exceeds bounded metadata scope')
            result['database_names_unique'] = len({Path(path).name.casefold() for path in paths}) == len(paths)
            result['databases'] = [database_metadata(Path(path)) for path in paths]
            schema = str(read(app, 'GetMaterialSchemaPathName'))
            result['material_schema'] = schema_metadata(Path(schema))
            result['document_count_after'] = int(read(app, 'GetDocumentCount'))
            after_identity = application_identity(app)
            require(result['document_count_after'] == 0 and after_identity == identity, 'oracle identity or idle state changed during metadata capture')
            result['identity_unchanged'] = True
        result['passed'] = True
    except Exception as error:
        result['error'] = repr(error)
    finally:
        if app is not None and owned:
            try:
                require(int(read(app, 'GetDocumentCount')) == 0, 'no exit requested because documents appeared in the owned session')
                require(int(read(app, 'GetProcessID')) == pid, 'no exit requested because COM process identity changed')
                result['cleanup']['exit_requested'] = True
                read(app, 'ExitApp')
            except Exception as error:
                result['cleanup']['error'] = repr(error)
            app = None
        if handle is not None:
            result['cleanup']['exit_confirmed'] = WaitForSingleObject(handle, 30000) == WAIT_OBJECT_0
            handle.Close()
        if launch_fresh:
            result['processes_after'] = sorted(application_pids())
            result['passed'] = bool(result['passed'] and result['cleanup']['exit_requested']
                                    and result['cleanup']['exit_confirmed'] and not result['processes_after']
                                    and 'error' not in result['cleanup'])
        pythoncom.CoUninitialize()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    return result


def main():
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--launch-fresh', action='store_true')
    modes.add_argument('--metadata-only', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = capture(args.output, args.launch_fresh)
    print(json.dumps({'passed': result['passed'], 'output_sha256': sha256(args.output.read_bytes()).hexdigest(),
                      'native_processes_started': result['native_processes_started'],
                      'model_documents_opened': 0, 'catalog_binding_ready': False}))
    raise SystemExit(0 if result['passed'] else 3)


if __name__ == '__main__':
    main()
