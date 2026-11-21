import argparse
import base64
import codecs
from dataclasses import asdict
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--mode', choices=('source', 'graph', 'build', 'reject'), required=True)
    args = parser.parse_args()
    row = json.loads(sys.stdin.read())
    source = Path(row['path']).read_bytes() if args.mode == 'source' else None
    if source is not None:
        require(sha256(source).hexdigest() == row['sha256'] and row['disclosed'] is True, 'disclosed source custody differs')
    sys.path[:0] = [str(args.sdk / 'src'), str(Path(__file__).resolve().parent)]
    from convert import open_document
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.Construction.Configuration.ConfigSpec import ConfigSpec
    from convert.adapters.solidworks.Archive.Construction.Configuration.ManagerInput import ManagerInput
    from convert.adapters.solidworks.Archive.Construction.Configuration.MakePartConfig import MakePartConfig
    from convert.adapters.solidworks.Archive.Construction.Configuration.ReadMgrIntent import ReadMgrIntent
    from convert.adapters.solidworks.Archive.Construction.Configuration.ReadMgrName import ReadMgrName
    from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import InitNodeMut
    from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
    from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ProjectRevolve import ProjectRevolve
    from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevPart import MakeRevPart
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from ManagerModel01 import compose, make_system
    from MakeRevolveRequest01 import make_request
    for encoding in ('ascii', 'utf-8', 'utf-8-sig', 'utf-16-le', 'utf-16-be', 'latin-1'):
        codecs.lookup(encoding)
    for name in ('interchange.brep.Validation.BrepValidate', 'interchange.document.Models.DocumentProvenance', 'interchange.document.Behavior.DocumentIo', 'interchange.document.Validation.AngleRevValidate', 'interchange.document.Validation.DocumentAssemblyValidate', 'interchange.document.Validation.DocumentFeatureValidate', 'interchange.document.Validation.DocumentReferenceValidate', 'interchange.document.Validation.PlaneRevValidate', 'interchange.document.Validation.DistExtValidate'):
        import_module(name)
    state = {'enabled': False, 'attempts': []}

    def audit(event, arguments):
        if state['enabled'] and (event == 'open' or event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.fork', 'os.posix_spawn', 'ctypes.dlopen')):
            state['attempts'].append(event)
            raise RuntimeError('manager proof attempted external runtime access')

    def encode_intent(value):
        return asdict(value)

    def check_graph(manager):
        data = WriteCmgrMut(manager, 19000)
        decoded = ReadCmgrMut(data, 19000)
        require(WriteCmgrMut(decoded.RootValue, 19000) == data, 'manager graph failed exact wire round trip')
        require(decoded.ReportValue['completed'] and not decoded.ReportValue['missing_schemas'] and not decoded.ReportValue['provisional_schemas'], 'manager crossed unqualified typed schema')
        intent = ReadMgrIntent(decoded.RootValue)
        fields = decoded.RootValue.FieldsValue
        rows = fields['f370']['items']
        require(fields['f08'] == -1 and fields['f360'] is rows[intent.CurrentIndex]['o'] and fields['f368'] is fields['f360'], 'actual selected configuration aliases or manager identity differ')
        require([entry['o'].FieldsValue['f08'] for entry in rows] == list(range(len(rows))), 'configuration local identifiers differ')
        return {'bytes': len(data), 'sha256': sha256(data).hexdigest(), 'map_counter': decoded.MapValue.CounterValue, 'map_entries': len(decoded.MapValue.EntriesValue), 'wire_byte_identity': True, 'actual_selector_aliases': True, 'manager_global_id': fields['f08'], 'intent': encode_intent(intent)}, data, decoded.RootValue

    sys.addaudithook(audit)
    result = {'schema': 'kit.sw2026.optional-manager-process.v1', 'passed': False, 'mode': args.mode, 'heldout_inputs_read': 0, 'native_processes': 0, 'full_original_source_preparation_admitted': False, 'public_unnamed_manager_preparation_enabled': False}
    state['enabled'] = True
    try:
        if args.mode == 'source':
            archive = SldprtArchive.from_bytes(source)
            data = archive.require('Contents/CMgr')
            decoded = ReadCmgrMut(data, 19000)
            proof, emitted, manager = check_graph(decoded.RootValue)
            require(emitted == data, 'original manager bytes changed')
            require(ReadMgrName(manager) is None and proof['intent']['NameValue'] is None, 'disclosed manager absent-name observation differs')
            result.update(case=row['name'], source_sha256=row['sha256'], cmgr=proof, optional_name_absent=True)
        else:
            document, settings = make_request(row['spec'])
            plan = ProjectRevolve(document)
            if args.mode == 'build':
                baseline = MakeRevPart(document, settings)
                require(sha256(baseline.BytesValue).hexdigest() == row['sha256'], 'existing four native-qualified generated hashes changed')
                named = compose(document, settings, settings.ManagerName)
                require(named.BytesValue == baseline.BytesValue, 'explicit lower factory changed existing named output')
                first, second = compose(document, settings, None), compose(document, settings, None)
                require(first.BytesValue == second.BytesValue, 'unnamed manager build is not deterministic')
                changed = [name for name in baseline.StreamsValue if baseline.StreamsValue[name] != first.StreamsValue[name]]
                require(changed == ['Contents/CMgr'], 'optional manager presence changed an unrelated stream')
                require(not any('partition' in name.casefold() or 'delta' in name.casefold() for name in first.StreamsValue), 'manager proof transmitted a geometry cache')
                proof, data, manager = check_graph(first.SystemValue.ManagerValue)
                require(data == first.StreamsValue['Contents/CMgr'] and ReadMgrIntent(manager).NameValue is None, 'actual constructor did not emit absence')
                modes = {}
                for mode, options in (('history', {'include_brep': False, 'include_tessellation': False}), ('default', {})):
                    before = open_document(baseline.BytesValue, source_format='solidworks.sldprt', strict=True, **options)
                    after = open_document(first.BytesValue, source_format='solidworks.sldprt', strict=True, **options)
                    after.assert_valid()
                    require((after.feature_timeline, after.sketches, after.parameters, after.bodies, after.brep, after.brep_payloads, after.support_planes, after.selections) == (before.feature_timeline, before.sketches, before.parameters, before.bodies, before.brep, before.brep_payloads, before.support_planes, before.selections), 'manager optional name changed part semantics')
                    if mode == 'default':
                        require(after.brep is not None and not after.brep.validate(frozenset(body.id for body in after.bodies)), 'cacheless default geometry no longer validates')
                    modes[mode] = {'semantics_identical': True, 'body_count': len(after.bodies), 'brep_count': len(after.brep.bodies) if after.brep else 0, 'native_payload_count': len(after.brep_payloads)}
                result.update(previous_sha256=row['sha256'], sha256=sha256(first.BytesValue).hexdigest(), previous_named_bytes_preserved=True, deterministic_two_builds=True, changed_streams=changed, cmgr=proof, modes=modes, artifact_base64=base64.b64encode(first.BytesValue).decode(), streams={name:{'bytes':len(data),'sha256':sha256(data).hexdigest()} for name,data in first.StreamsValue.items()})
            else:
                specs = tuple(ConfigSpec(item['name'], item['description'], item['updated_at']) for item in row.get('configs', [{'name':'Default', 'description':'', 'updated_at':settings.HeaderValue.ModifiedAt}]))
                manager_input = ManagerInput(row.get('manager_name', None), specs, row.get('current_index', 0))
                allocator = PersistentIds()
                system = make_system(settings, plan, manager_input, allocator)
                if args.mode == 'graph':
                    before = allocator.NextValue
                    proof, data, decoded = check_graph(system.ManagerValue)
                    require(ReadMgrIntent(decoded) == manager_input and allocator.NextValue == before, 'manager local graph changed explicit intent or consumed global IDs')
                    other_allocator = PersistentIds()
                    other = make_system(settings, plan, manager_input, other_allocator)
                    require(WriteCmgrMut(other.ManagerValue, 19000) == data and before == other_allocator.NextValue, 'fresh manager construction is not deterministic')
                    result.update(cmgr=proof, deterministic_two_builds=True, global_allocator_next=before, local_ids_independent=True)
                else:
                    fault = row['fault']
                    manager = ReadCmgrMut(WriteCmgrMut(system.ManagerValue, 19000), 19000).RootValue
                    fields = manager.FieldsValue
                    configs = fields['f370']['items']
                    operation = None
                    if fault == 'empty_name': operation=lambda:ManagerInput('',specs,0)
                    elif fault == 'nul_name': operation=lambda:ManagerInput('bad\x00name',specs,0)
                    elif fault == 'boolean_name': operation=lambda:ManagerInput(True,specs,0)
                    elif fault == 'empty_configs': operation=lambda:ManagerInput(None,(),0)
                    elif fault == 'list_configs': operation=lambda:ManagerInput(None,list(specs),0)
                    elif fault == 'duplicate_configs': operation=lambda:ManagerInput(None,(specs[0],specs[0]),0)
                    elif fault == 'boolean_selector': operation=lambda:ManagerInput(None,specs,True)
                    elif fault == 'negative_selector': operation=lambda:ManagerInput(None,specs,-1)
                    elif fault == 'range_selector': operation=lambda:ManagerInput(None,specs,len(specs))
                    elif fault == 'none_current': fields['f360']=None
                    elif fault == 'distinct_selectors': fields['f368']=MakePartConfig(specs[0],system.RootValue,0,settings.TargetValue)
                    elif fault == 'foreign_current': fields['f360']=fields['f368']=MakePartConfig(specs[0],system.RootValue,0,settings.TargetValue)
                    elif fault == 'wrong_config_class': configs[0]['o'].ClassValue=RuntimeClass('moConfiguration_c',1)
                    elif fault == 'wrong_local_id': configs[0]['o'].FieldsValue['f08']=7
                    elif fault == 'allocation_count': fields['f40c']+=1
                    elif fault == 'directory_count': fields['f370']['n']+=1
                    elif fault == 'empty_directory': fields['f370']={'n':0,'items':[]};fields['f40c']=0
                    elif fault == 'missing_name': del fields['f18']
                    elif fault == 'empty_name_object': fields['f18']=ArchiveNode(RuntimeClass('moNodeName_c',1),{'f08':''})
                    elif fault == 'wrong_name_class': fields['f18']=ArchiveNode(RuntimeClass('moConfiguration_c',1),{'f08':'manager'})
                    elif fault == 'wrong_name_schema': fields['f18']=ArchiveNode(RuntimeClass('moNodeName_c',2),{'f08':'manager'})
                    elif fault == 'allocated_null_manager': operation=lambda:InitNodeMut(ArchiveNode(RuntimeClass('moConfigurationMgr_c',1),{}),None,PersistentIds())
                    elif fault == 'unnamed_other_node': operation=lambda:InitNodeMut(ArchiveNode(RuntimeClass('moPart_c',1),{}),None)
                    else: raise ValueError('unknown negative fixture')
                    if operation is None:
                        operation=lambda:ReadMgrIntent(manager)
                    try:
                        operation()
                    except (TypeError, ValueError) as error:
                        result.update(fault=fault, rejection=type(error).__name__, message=str(error), rejected=True)
                    else:
                        raise ValueError('malformed manager intent was accepted: '+fault)
        result['passed'] = True
    finally:
        state['enabled'] = False
    result['runtime_external_attempts'] = state['attempts']
    result['sdk_modules'] = sorted({module.__file__ for name,module in sys.modules.items() if (name=='convert' or name.startswith(('convert.','interchange.'))) and getattr(module,'__file__',None)})
    print(json.dumps(result,allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
