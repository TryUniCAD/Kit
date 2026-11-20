from __future__ import annotations

from Core import Obj
from Streams import StreamDoc
from defs.Visual import store_visual_states
from para.concentric.MakeDisplayTree import DisplayListIntent, action_rows, selected_config

from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import AssemblyState
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeExtFeature import MakeExtFeature
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeRefChain import MakeRefChain
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import CompRefFields
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey, ReadFileText
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, ReadRows, RequireNode, RequireRecord
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import ReadMemberTime


VERSION = 19000
STREAM = 'ThirdPtyStore/VisualStates'
DEFAULT_NAME = 'Display State-1'
DEFAULT_ALIAS = '<Default>_Display State 1'
UNSELECTED = {'f08': '', 'f10': -1}
CONTEXT_WORDS = {'f48': 0, 'f4c': 1, 'f50': 0, 'f54': 0, 'f58': 0, 'f60': 0, 'f70': 0, 'f78': -1}


def need(value, message):
    if not value:
        raise ValueError(message)


def physical_references(state, references):
    model = RequireNode(state.RootValue, 'moAssembly_c').FieldsValue
    table = RequireRecord(RequireRecord(model['f68'])['list'])
    refs = tuple(RequireNode(row['o'], 'moReference_c') for row in ReadRows(table['items']))
    need(FieldInt(table, 'n') == len(refs) == len(references) == 2
         and all(first is second for first, second in zip(refs, references, strict=True)), 'VisualStates requires two actual direct occurrences')
    directory = RequireNode(refs[0].FieldsValue['f3b0'], 'moExtObject_c')
    need(ReadFileKey(directory)[2] == 2 and all(row.FieldsValue['f3b0'] is directory for row in refs),
         'VisualStates requires one shared ordinary child part definition')
    result = {FieldInt(row.FieldsValue, 'f08'): row for row in refs}
    need(len(result) == len(refs) and all(key > 0 and node.FieldsValue['hidden'] == 0 for key, node in result.items()),
         'VisualStates requires distinct visible ordinary default occurrence owners')
    return result


def file_identity(state, header):
    file = RequireNode(RequireNode(header, 'moHeader_c').FieldsValue['f38'], 'moExtObject_c')
    owner = RequireRecord(file.FieldsValue['shared'])
    name, _, kind, _ = ReadFileKey(file)
    need(kind == 3 and name == ReadNodeName(state.RootValue), 'VisualStates requires the actual fresh assembly self-file identity')
    pooled = dict(owner)
    for key in ('h18', 'h10'):
        pooled[key] = Obj('moCStringHandle_c', {'f08': ReadFileText(owner[key])})
    for key in ('f38', 'f40', 'f50'):
        value = owner[key]
        need(type(value) is CStringValue and value.IsUnicode and not value.TextValue,
             'VisualStates requires ordinary empty Unicode self-file extension fields')
        pooled[key] = value.TextValue
    return owner, pooled


def context_rows(config, refs, owner, pooled):
    ordered = []
    own_configuration = {'f08': ReadNodeName(config), 'f10': FieldInt(config.FieldsValue, 'f08')}
    table = tuple(RequireNode(row['o'], 'moConfigObject_c') for row in ReadRows(config.FieldsValue['fce8']))
    need(len(table) == len(refs) + 1 and table[0].FieldsValue['f10'] is None, 'VisualStates requires the complete actual occurrence configuration order')
    for row in table[1:]:
        context = RequireNode(row.FieldsValue['f10'], 'moContextChainComponent_c').FieldsValue
        chain = RequireNode(context['f20'], 'moReferenceChain_c').FieldsValue
        targets = RequireNode(chain['f08'], 'moExtFeatureList_c').FieldsValue
        target_row, = ReadRows(targets['f08'])
        external = RequireNode(target_row['o'], 'moExtFeature_c').FieldsValue
        feature = FieldInt(external, 'f44')
        reference = refs.get(feature)
        need(reference is not None, 'VisualStates configuration has a foreign reference owner')
        ref = reference.FieldsValue
        back = RequireNode(ref['f4f8'], 'moExtFeature_c').FieldsValue
        actual_file = RequireNode(context['f40'], 'moExtObject_c').FieldsValue
        stamp = (101 + FieldInt(ref, 'f3f0')) & 0xFFFFFFFF
        need(actual_file.get('f58') == 0, 'VisualStates supports the ordinary context-file flag 0 branch only')
        need(context['owner'] is None and context['f30'] == stamp and context['f48'] == 0
             and actual_file == CONTEXT_WORDS | {'shared': owner, 'refcfg': own_configuration}
             and actual_file['shared'] is owner and external['f10'] is owner and back['f10'] is owner
             and back['f50'] is reference and back['f44'] == feature
             and row.FieldsValue['f28'] == ref['f3c0']
             and ReadFileText(external['f38']) == ReadNodeName(reference)
             and external['f50'] is None and external['f18'] == UNSELECTED and external['f40'] == 0 and external['f58'] == -1
             and targets['n'] == 1 and chain['f24'] == chain['f20'] == 0 and chain['f40'] == UNSELECTED,
             'VisualStates requires the measured fresh occurrence context and pooled parent identity')
        detached = dict(MakeExtFeature(reference, pooled, False).FieldsValue)
        detached['f38'] = Obj('moCStringHandle_c', {'f08': ReadNodeName(reference)})
        feature_node = Obj('moExtFeature_c', detached)
        path = dict(MakeRefChain(feature_node).FieldsValue)
        path['f24'] = 1
        path['f08'] = Obj('moExtFeatureList_c', dict(RequireNode(path['f08'], 'moExtFeatureList_c').FieldsValue))
        context_file = Obj('moExtObject_c', CONTEXT_WORDS | {'shared': pooled, 'refcfg': dict(UNSELECTED)})
        ordered.append((feature, Obj('moContextChainComponent_c', {'owner': None, 'f20': Obj('moReferenceChain_c', path),
                                                                   'f30': stamp, 'f40': context_file, 'f48': 0})))
    need(tuple(feature for feature, _ in ordered) == tuple(reversed(refs)), 'VisualStates requires reverse direct occurrence order')
    return tuple(ordered)


def plane_rows(state):
    known = tuple(state.PlaneValues.values())
    planes = tuple(row for row in state.FeatureValues if row.ClassValue.NameValue == 'moRefPlane_c')
    need(set(state.PlaneValues) == {'z', 'y', 'x'} and len(planes) == len(set(known)) == 3 and set(planes) == set(known),
         'VisualStates requires the three actual principal plane owners')
    unit = RequireNode(state.RootValue.FieldsValue['f990'], 'moUnitComponent_c')
    for plane in reversed(planes):
        fields = plane.FieldsValue
        need(fields['owner'] is state.RootValue and FieldInt(fields, 'f08') > 0 and FieldInt(fields, 'f2b0') == VERSION,
             'VisualStates plane lacks the actual ordinary model owner')
        clock = ReadMemberTime(plane)
        prefix = CompRefFields(unit)
        yield Obj('moCompFeature_c', prefix | {'f58': Obj('moUnitComponent_c', {'owner': None, 'has_ext': 0}),
                                              'ff0': {'f00': fields['f08'], 'f08': clock.SecondsValue}})


def visual_attribute(default, words):
    return Obj('visStateVisualStateAttribute_c', dict(zip(('f08', 'f10', 'f14', 'f18', 'f1c'), (default, *words), strict=True)))


def attribute_row(state_id, *objects):
    return {'key': state_id, 'k': len(objects), 'objs': [{'o': node} for node in objects]}


def visual_document(state: AssemblyState, header: ArchiveNode, references: tuple[ArchiveNode, ...], intent: DisplayListIntent) -> StreamDoc:
    config = selected_config(state)
    config_id = FieldInt(config.FieldsValue, 'f08')
    need(type(intent) is DisplayListIntent and type(intent.configuration_id) is int and intent.configuration_id == config_id >= 0,
         'VisualStates intent must select the actual generated configuration')
    need(type(intent.states) is tuple and 1 <= len(intent.states) <= 3, 'VisualStates supports one to three ordered display states')
    refs = physical_references(state, references)
    actions = action_rows(intent, tuple(refs))
    need(actions[0][0] == DEFAULT_NAME, 'VisualStates requires the measured initial display-state name')
    keys = tuple(range(1, len(actions) + 1))
    default = keys[0]
    values = tuple(dict(row.visibility) for row in intent.states)
    props = Obj('visStateVisualPropertiesAttribute_c', {'f08': default, 'f10': None})
    label = Obj('visStateDisplayStateAttribute_c', {'f08': default, 'f10': DEFAULT_ALIAS, 'f18': default})
    visibility = {enabled: visual_attribute(default, (int(enabled), 6, 0, 1)) for enabled in {x for row in values for x in row.values()}}
    plane_display = visual_attribute(default, (0, 6, 1, 0))
    owner, pooled = file_identity(state, header)
    components = []
    for feature, node in context_rows(config, refs, owner, pooled):
        attrs = [attribute_row(key, props, visibility[vector[feature]], label) for key, vector in zip(keys, values, strict=True)]
        components.append({'comp': node, 'm': len(attrs), 'attrs': attrs})
    planes = []
    for node in plane_rows(state):
        attrs = [attribute_row(key, props, plane_display) for key in keys]
        planes.append({'ref': node, 'm': len(attrs), 'attrs': attrs})
    states = [{'id': key, 'name': name, 'f384': 0, 'f394': 0, 'f38c': 0} for key, (name, _) in zip(keys, actions, strict=True)]
    association = [{'key': config_id, 'value': default, 'one': 1}]
    root = Obj('visStateKeyData_c', {'f15c': 5, 'f158': 0, 'n_ids': len(association), 'f118': association,
                                    'n_states': len(states), 'f0f0': states, 'n_comps': len(components), 'comps': components,
                                    'n_ents': len(planes), 'f78': planes, 'n_f88': 0, 'f88': [], 'n': 0, 'f08': []})
    return StreamDoc('visual_states', {'file_version': VERSION, 'shown': 0, 'root': root}, [root], b'')


def make_visual_store(state: AssemblyState, header: ArchiveNode, references: tuple[ArchiveNode, ...], intent: DisplayListIntent, registry) -> bytes:
    return store_visual_states(visual_document(state, header, references, intent), registry)
