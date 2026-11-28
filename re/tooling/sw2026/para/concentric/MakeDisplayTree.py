from __future__ import annotations

from dataclasses import dataclass
from re import compile as compile_pattern
from xml.etree.ElementTree import Element, SubElement, tostring

from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import AssemblyState
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.MakeAsmTree import MakeAsmTree
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import PartCandidate
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.Assembly import XmlRoot
from convert.adapters.solidworks.Assembly.Display.ReadDisplayXml import ReadDispMember
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, ReadRows, RequireNode, RequireRecord


NAMESPACE = 'http://www.solidworks.com/sw2003/schema'
PREFIX = f'{{{NAMESPACE}}}'
XML_TEXT = compile_pattern(r'[\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]+')


@dataclass(frozen=True, slots=True)
class DisplayStateIntent:
    name: str
    visibility: tuple[tuple[int, bool], ...]


@dataclass(frozen=True, slots=True)
class DisplayListIntent:
    configuration_id: int
    states: tuple[DisplayStateIntent, ...]


def selected_config(state: AssemblyState) -> ArchiveNode:
    manager = RequireNode(state.ManagerValue, 'moConfigurationMgr_c').FieldsValue
    config = RequireNode(state.CurrentConfig, 'moConfiguration_c')
    table = RequireRecord(manager['f370'])
    rows = ReadRows(table['items'])
    if FieldInt(table, 'n') != 1 or len(rows) != 1 or any(value is not config for value in (manager['f360'], manager['f368'], rows[0]['o'])):
        raise ValueError('display intent requires one actual selected assembly configuration')
    return config


def occurrence_ids(state: AssemblyState, references: tuple[ArchiveNode, ...], xml_rows: tuple[Element, ...]) -> tuple[int, ...]:
    owner = RequireNode(state.RootValue, 'moAssembly_c').FieldsValue
    table = RequireRecord(RequireRecord(owner['f68'])['list'])
    actual = tuple(RequireNode(row['o'], 'moReference_c') for row in ReadRows(table['items']))
    count = len(references)
    if count not in (2, 3) or FieldInt(table, 'n') != count or len(actual) != count or len(xml_rows) != count:
        raise ValueError('display intent requires two or three actual direct occurrences')
    if any(left is not right for left, right in zip(actual, references, strict=True)):
        raise ValueError('display intent references must belong to the actual generated assembly')
    ordered = []
    for reference, row in zip(actual, xml_rows, strict=True):
        fields = reference.FieldsValue
        external = RequireNode(fields['f4f8'], 'moExtFeature_c').FieldsValue
        member = ReadDispMember(row)
        if (member.FeatureId != FieldInt(fields, 'f08') or member.FeatureId != FieldInt(external, 'f44')
                or member.NativeName != ReadNodeName(reference) or external['f50'] is not reference
                or FieldInt(fields, 'hidden') != 0 or row.get('swFlexible') != 'NO' or row.get('swIsVirtualComponent') != 'NO'):
            raise ValueError('display member requires the actual visible rigid occurrence owner')
        ordered.append(member.FeatureId)
    if len(set(ordered)) != len(ordered):
        raise ValueError('display member occurrence identities are ambiguous')
    return tuple(ordered)


def action_rows(intent: DisplayListIntent, ordered: tuple[int, ...]) -> tuple[tuple[str, str], ...]:
    if type(intent.states) is not tuple or not intent.states:
        raise ValueError('display intent requires one or more ordered authored states')
    if len(ordered) == 3 and len(intent.states) != 1:
        raise ValueError('three direct occurrences require a single all-visible display state')
    names = set()
    output = []
    expected = set(ordered)
    for state in intent.states:
        if type(state) is not DisplayStateIntent or type(state.name) is not str or not state.name.strip() or XML_TEXT.fullmatch(state.name) is None:
            raise ValueError('each display state requires an XML-safe authored name')
        identity = state.name.casefold()
        if identity in names:
            raise ValueError('display state names must be distinct')
        names.add(identity)
        if type(state.visibility) is not tuple or any(
                type(row) is not tuple or len(row) != 2 or type(row[0]) is not int or type(row[1]) is not bool
                for row in state.visibility):
            raise ValueError('display visibility requires persistent occurrence IDs and explicit booleans')
        visibility = dict(state.visibility)
        if len(visibility) != len(state.visibility) or visibility.keys() != expected:
            raise ValueError('each state must bind all and only the actual occurrences exactly once')
        if not output and not all(visibility.values()):
            raise ValueError('the first state must match the generated all-visible default')
        output.append((state.name, ''.join('Yes,' if visibility[feature] else 'No,' for feature in ordered)))
    return tuple(output)


def append_display_list(root: Element, state: AssemblyState, references: tuple[ArchiveNode, ...], intent: DisplayListIntent) -> None:
    if root.tag == f'{PREFIX}swSolidWorks':
        prefix = PREFIX
    elif root.tag == 'swSolidWorks' and root.get('xmlns') == NAMESPACE:
        prefix = ''
    else:
        raise ValueError('display intent requires the ordinary assembly instance namespace')
    if (root.get('swVersion') != '19000' or type(intent) is not DisplayListIntent
            or type(intent.configuration_id) is not int or intent.configuration_id < 0):
        raise ValueError('display intent requires a typed version 19000 configuration selection')
    config = selected_config(state)
    if FieldInt(config.FieldsValue, 'f08') != intent.configuration_id:
        raise ValueError('display intent selects a foreign persistent configuration ID')
    (config_list,) = root.findall(f'{prefix}swConfigurationList')
    (config_row,) = config_list.findall(f'{prefix}swConfiguration')
    (models,) = root.findall(f'{prefix}swModelList')
    (model,) = (row for row in models if row.get('id') == config_row.get('swModelRef'))
    if (config_row.get('swID') != str(intent.configuration_id) or config_row.get('swName') != ReadNodeName(config)
            or config_row.get('swReference') != ReadNodeName(state.RootValue) or config_row.get('swMostRecentConfiguration') != 'YES'
            or model.tag != f'{prefix}swModel'):
        raise ValueError('display XML configuration and root model must match generated owners')
    xml_rows = tuple(model.findall(f'{prefix}swReference'))
    if tuple(root.iter(f'{prefix}swReference')) != xml_rows:
        raise ValueError('display intent requires one flat assembly occurrence scope')
    ordered = occurrence_ids(state, references, xml_rows)
    if any(next(root.iter(f'{prefix}{role}'), None) is not None for role in ('swDisplayStateList', 'swDisplayState')):
        raise ValueError('the generated XML already has a display-state owner')
    ids = sorted((node.attrib['id'] for node in root.iter() if 'id' in node.attrib), key=int)
    if root.get('swObjCount') != str(len(ids)) or ids != [str(index) for index in range(1, len(ids) + 1)]:
        raise ValueError('ordinary display allocation requires a complete XML-local ID sequence')
    actions = action_rows(intent, ordered)
    next_id = len(ids) + 1
    listing = SubElement(config_row, f'{prefix}swDisplayStateList', {'id': str(next_id), 'swCompNameList': ''.join(f'{value},' for value in ordered)})
    for leaf_id, (name, show) in enumerate(actions, next_id + 1):
        SubElement(listing, f'{prefix}swDisplayState', {'id': str(leaf_id), 'swDisplayStateName': name, 'swShowState': show})
    root.set('swObjCount', str(next_id + len(actions)))


def frame_tree(root: Element) -> bytes:
    for node in root.iter():
        if not node.tag.startswith(PREFIX):
            raise ValueError('generated assembly contains an unexpected XML namespace')
        node.tag = node.tag[len(PREFIX):]
    root.attrib = {'xmlns': NAMESPACE, **root.attrib}
    return b'<?xml version="1.0" encoding="UTF-8"?>\r\n' + tostring(root, encoding='utf-8').replace(b' />', b'/>') + b'\r\n'


def make_display_tree(state: AssemblyState, header: ArchiveNode, child: PartCandidate,
                      references: tuple[ArchiveNode, ...], intent: DisplayListIntent | None = None) -> bytes:
    baseline = MakeAsmTree(state, header, child, references)
    if intent is None:
        return baseline
    root = XmlRoot(baseline)
    append_display_list(root, state, references, intent)
    return frame_tree(root)
