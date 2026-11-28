from dataclasses import asdict
from hashlib import sha256
import json

from convert.adapters.solidworks.Archive.Construction.Units.MakeUnitTable import MakeUnitTable
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Construction.Units.UnitVocabulary import KUnitClasses,KLengthCodes,KAngleCodes,KSystemCodes
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.Preparation.Revolve.Source.ReadRevUi import ReadRevUi
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren


def require(value,message):
    if not value:raise ValueError(message)


def canonical(value):
    if isinstance(value,ArchiveNode):return {'class':value.ClassValue.NameValue,'schema':value.ClassValue.SchemaValue,'fields':canonical(value.FieldsValue)}
    if isinstance(value,dict):return {key:canonical(item) for key,item in value.items()}
    if isinstance(value,(tuple,list)):return [canonical(item) for item in value]
    if isinstance(value,bytes):return {'bytes':len(value),'sha256':sha256(value).hexdigest()}
    return value


def own_hash(value):return sha256(json.dumps(canonical(value),sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()


def diff(actual,expected,path=''):
    actual,expected=canonical(actual),canonical(expected)
    if isinstance(actual,dict) and isinstance(expected,dict):
        return [result for key in sorted(set(actual)|set(expected)) for result in diff(actual.get(key,'__absent__'),expected.get(key,'__absent__'),path+'.'+key)]
    if isinstance(actual,list) and isinstance(expected,list):
        if len(actual)!=len(expected):return [{'path':path,'source_count':len(actual),'constructed_count':len(expected)}]
        return [result for index,(first,second) in enumerate(zip(actual,expected,strict=True)) for result in diff(first,second,path+'['+str(index)+']')]
    return [] if actual==expected else [{'path':path,'source':actual,'constructed':expected}]


def clocks(node):
    values=node.FieldsValue
    if 'f2a0' not in values or 'f2a4' not in values:return None
    ticks=(values['f2a0']&0xffffffff)|((values['f2a4']&0xffffffff)<<32)
    return {'filetime_ticks':ticks,'unix_seconds':ticks//10000000-11644473600,'subsecond_ticks':ticks%10000000}


def units(table):
    if table is None:return {'present':False}
    require(table.ClassValue.NameValue=='moUnitsTable_c','actual user units have another concrete owner')
    rows=tuple(row['o'] for row in table.FieldsValue['items'])
    require(table.FieldsValue['n']==len(rows)==16,'actual user units do not have the complete sixteen-class profile')
    require(tuple(node.ClassValue.NameValue for node in rows)==tuple(KUnitClasses.values()),'actual user-unit factory order differs')
    mapping={node.ClassValue.NameValue:node for node in rows}
    precision={node.FieldsValue['f0c'] for node in rows}
    values={'present':True,'class_order':[node.ClassValue.NameValue for node in rows],'precision_values':sorted(precision),'source_sha256':own_hash(table)}
    if len(precision)!=1:
        values['constructor_gap']='the existing UnitInput cannot preserve different per-kind precisions';return values
    inverse=lambda codes,value:next(key for key,number in codes.items() if number==value)
    input_value=UnitInput(inverse(KLengthCodes,mapping['moLengthUserUnits_c'].FieldsValue['fb0']),inverse(KAngleCodes,mapping['moAngleUserUnits_c'].FieldsValue['fb0']),inverse(KSystemCodes,mapping['moUnitSysUnits_c'].FieldsValue['fb0']),precision.pop())
    values['semantic_input']=asdict(input_value)
    differences=diff(table,MakeUnitTable(input_value),'moPart.f9b8')
    values['minimal_constructor_exact']=not differences
    values['minimal_constructor_differences']=differences
    return values


def styles(model):
    fields=model.FieldsValue['fae0']
    require(type(fields) is dict,'ordinary part detailing must retain its embedded concrete record')
    require(fields['n58']==len(fields['f58']) and fields['fb8']['n']==len(fields['fb8']['items'])==5,'source style text arrays are incomplete')
    return {'standard':fields['f10'],'font_name':fields['f90']['f08'],'font_height_m':fields['f90']['f10'],'line_style_name':fields['f13b0']['fe0']['fd0']['f08'],'print_widths_m':[fields['fb0']['f'+format(8+4*index,'x')] for index in range(8)],'exclusion_names':[row['s'] for row in fields['f58']],'task_labels':[row['s'] for row in fields['fb8']['items']],'cutlist_expressions':[fields[key] for key in ('f200','f208','f210')],'complete_embedded_graph_sha256':own_hash(fields),'complete_graph_preserved_as_writer_input':False,'complete_graph_generation_qualified':False}


def source_plan(archive,link,owner,definition,manager,header,history,biography,document):
    model=link.ConfigValue.RootValue
    config=manager.FieldsValue['f360']
    ui=ReadRevUi(definition)
    generated_ui=MakePartDef(ui.SettingsValue,ui.DensityValue)
    names=('fa58','fa5c','fa60','fa64','fad8_0','fad8_1','fa90','f1688')
    require(all(generated_ui.DocumentValue.FieldsValue[key]==definition.DocumentValue.FieldsValue[key] for key in names),'explicit source ui preferences changed through the proven generative boundary')
    require(generated_ui.DocumentValue.FieldsValue['fba8'].ClassValue==definition.DocumentValue.FieldsValue['fba8'].ClassValue,'source ui standard class was replaced')
    roots=link.ResolvedValue.RootsValue
    source_styles=styles(model)
    source_units=units(model.FieldsValue['f9b8'])
    source_analysis=units(model.FieldsValue['f9c0'])
    source_clocks={'header_f50':header.FieldsValue['f50'],'header_f70':header.FieldsValue['f70'],'header_f48':header.FieldsValue['f48'],'root_history_states':len(history.RootValue.FieldsValue['states']),'roots':[{'class':node.ClassValue.NameValue,'name':ReadNativeName(node),'time':clocks(node)} for node in roots],'model_log_owners':len(header.FieldsValue['f20'].FieldsValue['items'])}
    native_tree=document.metadata['solidworks.typed_resolved_semantics']['native_tree']
    require(native_tree['status']=='ordinary_default_profile' and len(native_tree['rows'])==25,'ordinary native source tree was not preserved through complete ownership checks')
    points=owner.ProfileGraph.LoopValue.PointsValue
    contour=[point.PositionValue for point in points.values()]
    feature=next(step for step in document.feature_timeline if step.id==f'sldprt:feature:{owner.NodeValue.FieldsValue["f08"]}')
    sketch=next(sketch for sketch in document.sketches if sketch.id==feature.sketch_id)
    parameter=next(parameter for parameter in document.parameters if parameter.id==feature.definition.AlongParameterId)
    require(parameter.owner_id==feature.id and parameter.name==owner.AngleValue.NameValue and len(sketch.entities)==5 and len(sketch.constraints)==4,'public source semantics do not bind the actual typed driver and construction axis')
    gaps=[]
    ui_differences=diff(definition.DocumentValue,generated_ui.DocumentValue,'uiPartDoc_c')
    if ui_differences:gaps.append({'owner':'uiPartDoc_c','reason':'complete source Definition contains additional presentation owners or state beyond the explicit preference projection'})
    if source_styles['standard']!=1:gaps.append({'owner':'moPart_c.fae0','reason':'complete source standard-zero detail graph exceeds the standard-one constructor; changing f10 alone is insufficient'})
    if not source_units.get('minimal_constructor_exact'):gaps.append({'owner':'moPart_c.f9b8','reason':'source unit-format rows differ beyond semantic unit codes and common precision'})
    if not source_analysis['present']:gaps.append({'owner':'moPart_c.f9c0','reason':'source analysis-unit owner is absent; current part composition always constructs one'})
    if manager.FieldsValue['f18'] is None:gaps.append({'owner':'moConfigurationMgr_c.f18','reason':'source manager is anonymous; current manager constructor requires a nonempty authored name'})
    stamp=history.RootValue.FieldsValue['states'][0]['st']['f08']
    if stamp['f18']!=header.FieldsValue['f70'] or header.FieldsValue['f50']<header.FieldsValue['f70']:
        gaps.append({'owner':'moHeader_c.f50/f70 and moVersionHistory_c.states','reason':'actual template, creation and history epochs cannot be conflated by the current fresh recipe'})
    if source_clocks['model_log_owners']!=1:gaps.append({'owner':'moHeader_c.f20','reason':'source has per-feature chronology; current fresh header emits one model log'})
    states=history.RootValue.FieldsValue['states']
    codes=[code['st']['f08'] for state in states for code in state['st']['f38'].FieldsValue['states']]
    if any(code>0xffffff for code in codes):gaps.append({'owner':'moVersionHistory_c.states.f38','reason':'source save-history flag bits exceed the fresh low twenty four bit profile and their complete semantics remain unqualified'})
    body,=document.bodies
    if body.name!=feature.name:gaps.append({'owner':'CadDocument.bodies[0].name','reason':'current public body label is a legacy projection; actual original native body-name equivalence is not independently recorded by this method'})
    selected=owner.ProfileGraph.AxisValue
    return {'schema':'kit.sw2026.ordinary-revolve-source-preparation.v1','model_name':ReadNativeName(model),'configuration':{'id':config.FieldsValue['f08'],'name':ReadNativeName(config),'manager_name_present':manager.FieldsValue['f18'] is not None},'geometry':{'live_lines':[{'id':entity.id,'start_mm':[entity.geometry.start.x,entity.geometry.start.y],'end_mm':[entity.geometry.end.x,entity.geometry.end.y],'construction':entity.construction,'fixed':entity.fixed} for entity in sketch.entities],'closed_profile_entity_ids':[list(loop) for loop in sketch.closed_profile_entity_ids],'feature_id':feature.id,'feature_name':feature.name,'sketch_id':sketch.id,'sketch_name':sketch.name,'parameter_id':parameter.id,'parameter_name':parameter.name,'positive_angle_rad':owner.AngleValue.RadiansValue,'reverse':owner.IsReverse,'contour_points_mm':contour,'axis_start_mm':list(owner.ProfileGraph.AxisPoints[selected.StartValue].PositionValue),'axis_end_mm':list(owner.ProfileGraph.AxisPoints[selected.EndValue].PositionValue),'selected_axis_array_index':owner.AxisValue.IndexValue,'selected_axis_permanent_mark':owner.AxisValue.MarkValue,'axis_constraints':0,'planar_constraints':[rule.kind for rule in sketch.constraints]},'ui_preferences':asdict(ui),'ui_generated_projection_fields':list(names)+['fba8','ffd8.f18.f08'],'complete_definition_reproduced':not ui_differences,'complete_definition_difference_paths':[value['path'] for value in ui_differences],'styles':source_styles,'document_units':source_units,'analysis_units':source_analysis,'chronology':source_clocks,'tree':[{'id':row['native_object_id'],'name':row['name'],'class':row['class'],'parent':row['parent'],'role':row['owner_role']} for row in native_tree['rows']],'configuration_helpers':[{'id':row['stored_node_id'],'class':row['class'],'owner_field':row['typed_archive_owner']['owner_field']} for row in native_tree['configuration_helpers']],'metadata_observation':{'version_states':len(states),'originating_codes':codes,'biography_records':len(biography.RootValue.FieldsValue['records']),'biography_is_readback_only':True,'fresh_generation_uses_empty_biography':True,'source_history_re_emission_is_readback_only':True},'constructor_gaps':gaps,'full_source_preparation_admitted':not gaps,'public_revolve_registration':False,'heldout_inputs_read':0}


def require_preparable(plan):
    require(not plan['constructor_gaps'],'ordinary revolve source preparation refuses: '+', '.join(row['owner'] for row in plan['constructor_gaps']))
