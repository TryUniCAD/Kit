from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import json
from pathlib import Path, PureWindowsPath
from struct import unpack
import sys
from xml.etree.ElementTree import register_namespace, tostring


SW2026 = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SW2026))

from para.concentric.AuditConcentricDisplayState import (
    COMP_CLASS, INSTANCE, KEYWORDS, LocalName, PLANE_CLASS, REPO, VISUAL, ArchiveNode,
    FieldInt, ParseKeywords, ReadCmgrMut, ReadMemberTime, ReadNodeName, RequireNode,
    SldprtArchive, XmlRoot, checked, children, compare_typed, csv_field, ctext, digest,
    file_signature, load_visual_states, model_inputs, record_text, registry, require,
    store_visual_states, xml_owner,
)
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey


PACKET = 'ConcentricDisplayVisibility04'
PINS = {
    'trial': ('Trial.json', 'eace2beb513a3f02ba7a053a6622a1d793f12f55f288e9cc9a675c9b41daa048'),
    'preflight': ('Inspection/Preflight/Record.json', 'e80c5a76a31c645e9b9103e5167a1ea8b0bfbe1056d587a6f2e47f8c601d3319'),
    'control_before': ('Inspection/ControlBefore/Record.json', 'd123ae97f9765921ddd6478158958d44c999f730c76972d918c5834f6cc8108d'),
    'author': ('Inspection/Author/Record.json', '8f550dd1a668f917d3186955f5cd242cb8cf0a08f0ffd97c98e9e527617af1ed'),
    'observe': ('Inspection/Observe/Record.json', 'e3b0725fceaad92df876ac1d03da32627be0fa300a3dae7201b03015b0afb877'),
    'control_after': ('Inspection/ControlAfter/Record.json', '7ff33914f82a5ab817271b33b0c317e601ba29648853d3fb8458e12306303d0e'),
    'summary': ('Result.json', 'de275b71e12453fcd4a3454a49806ac50865634d2cbbe6662071ff0c6f4de19f'),
    'before': ('Inspection/Author/Before.SLDASM', '281b0adf91dbd0942658baa5ac1d6a285f7370df35cf9199c7651ec56d6f33ba'),
    'after': ('Working/ConcentricD01AlignedFree.SLDASM', 'cb64a55e4cc1da4ebc1f1c0b0a9d22db286c13a082ffd16dea273360fa2a3c72'),
    'child': ('Working/ConcentricD01Child.SLDPRT', '92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa'),
}
IDS = (24, 25)
ATTRIBUTE_CLASSES = ('visStateVisualPropertiesAttribute_c', 'visStateVisualStateAttribute_c', 'visStateDisplayStateAttribute_c')


def native_receipt(payloads):
    trial = json.loads(payloads['trial'])
    summary = json.loads(payloads['summary'])
    require(summary['packet_sha256'] == PINS['trial'][1] and summary['controls_healthy']
            and summary['distinct_native_processes'] == 4 and summary['heldout_inputs_read'] == 0
            and summary['passed'] is False and summary['stream_precedence_measured'] is False, 'scope of measured batch differs')
    phases = {}
    for key, role in (('preflight', 'Preflight'), ('control_before', 'ControlBefore'), ('author', 'Author'),
                      ('observe', 'Observe'), ('control_after', 'ControlAfter')):
        record = json.loads(payloads[key])
        require(record['job'] == {'phase': role, 'packet_sha256': PINS['trial'][1]}, 'receipt is not packet-bound')
        if key != 'preflight':
            require(record['result'] == summary['phases'][role]
                    and record['result']['oracle_identity']['sha256'] == trial['oracle_sha256'], 'native phase binding differs')
        phases[key] = record
    author, observe = (phases[key]['result'] for key in ('author', 'observe'))
    require(all(phases[key]['passed'] for key in ('preflight', 'control_before', 'author', 'control_after'))
            and not observe['passed'] and author['link_display_states_to_configurations'] is False,
            'measured controls, author success or observer failure differ')
    for key in ('control_before', 'author', 'control_after'):
        require(phases[key]['result']['open_status'] == [0, 0], 'a healthy phase reported an open warning')
    for field, side in (('before_authoring', 'before'), ('saved', 'after')):
        require(author[field]['status'] == [True, 0, 0] and author[field]['files_sha256'] ==
                {'parent': PINS[side][1], 'child': PINS['child'][1]}, 'before or after native save is not pinned')
    require(observe['files_on_open'] == author['saved']['files_sha256'] and observe['open_status'] == [0, 32]
            and not any(row['method'] in ('GetPathName', 'GetDisplayStates', 'GetDisplayStateComponentVisibility')
                        for row in phases['observe']['api_calls']), 'cold observe reached a different control or gate')
    opens = [row['result'] for row in phases['observe']['api_calls'] if row['method'] == 'open exact linked pair']
    require(opens == [[{'returned_object': 'CDispatch'}, 0, 32]], 'cold observer returned document evidence differs')
    unc = PureWindowsPath(author['stored_child_reference'])
    mapped = PureWindowsPath(observe['stored_child_reference'])
    require(unc.drive.startswith('\\\\') and mapped.drive.casefold() == 'z:' and unc.parts[1:] == mapped.parts[1:],
            'actual path alias did not preserve the owned child suffix')
    order = tuple((row['name'], tuple(row['visibility'])) for row in trial['states'])
    names = author['observed']['named']
    for label, expected in order:
        named = {row['native_id']: row['visible'] for row in names[label].values()}
        live = {row['native_id']: row['visible'] for row in author['observed']['activated'][label]['live'].values()}
        require(named == live and tuple(named[key] for key in IDS) == expected, 'authored native occurrence vector differs')
    actual = {'oracle_build': author['oracle_identity']['file_version'], 'preflight': True, 'native_processes': 4,
              'bracket_open_status': [[0, 0], [0, 0]], 'author_open_status': [0, 0], 'author_save_status': [True, 0, 0],
              'link_display_states_to_configurations': False, 'author_named_visibility': dict(order),
              'cold_open_status': [0, 32], 'cold_returned_document': True, 'cold_visibility_queried': False,
              'clean_lifecycle_passed': False, 'author_child_locator': 'UNC', 'observer_child_locator': 'Z:',
              'same_owned_child_suffix': True, 'pinned_job_preparation_head': trial['preparation_head'],
              'numeric_checks_per_phase': {key: phases[key]['result']['numeric_checks']
                                           for key in ('control_before', 'author', 'observe', 'control_after')}}
    return actual, order, mapped


def xml_bytes(tree):
    register_namespace('', 'http://www.solidworks.com/sw2003/schema')
    return b'<?xml version="1.0" encoding="UTF-8"?>\r\n' + tostring(tree, encoding='utf-8').replace(b' />', b'/>') + b'\r\n'


def index_graph(tree, refs, config, name, states):
    owner, = children(children(tree, 'swConfigurationList')[0], 'swConfiguration')
    listing, = children(owner, 'swDisplayStateList')
    leaves = children(listing, 'swDisplayState')
    ids = tuple(int(row.attrib['id']) for row in tree.iter() if 'id' in row.attrib)
    require(sorted(ids) == list(range(1, int(tree.attrib['swObjCount']) + 1)) and tuple(listing) == leaves
            and len(leaves) == len(states) and int(listing.attrib['id']) == 8, 'unexpected display XML owners')
    recorded = {}
    for offset, (leaf, (label, vector)) in enumerate(zip(leaves, states, strict=True), 9):
        tokens = tuple('Yes' if value else 'No' for value in vector)
        require(leaf.attrib == {'id': str(offset), 'swDisplayStateName': label, 'swShowState': ','.join(tokens) + ','}
                and len(leaf) == 0 and csv_field(leaf.attrib['swShowState']) == tokens, 'unexpected named XML state or polarity')
        recorded[label] = {'xml_id': offset, 'show_tokens': tokens, 'visibility': vector}
    default_graph = deepcopy(tree)
    projected, = (row for row in default_graph.iter() if LocalName(row) == 'swDisplayStateList')
    removed = list(projected)[1:]
    leaf_bytes = {}
    size = len(xml_bytes(default_graph))
    for leaf in reversed(removed):
        projected.remove(leaf)
        prior_size = size
        size = len(xml_bytes(default_graph))
        leaf_bytes[leaf.attrib['swDisplayStateName']] = prior_size - size
    default_graph.set('swObjCount', str(len(ids) - len(removed)))
    default_index = xml_owner(default_graph, refs, config, name, True)
    require(tuple(row['feature_id'] for row in default_index['occurrences']) == IDS
            and len(tuple(tree.iter())) - len(tuple(default_graph.iter())) == len(removed), 'actual direct occurrence inventory differs')
    return default_graph, default_index | {'states': recorded, 'actual_xml_object_count': len(ids)}, leaf_bytes


def archive_stamps(archive, header):
    fields = header.FieldsValue
    words = unpack('<III', archive.require('ModelStamps'))
    require(words == tuple(fields[key] for key in ('f70', 'f40', 'f44')), 'persisted ModelStamps and ModelHeader disagree')
    return {'creation_seconds': words[0], 'update_stamp': words[1], 'body_stamp': words[2], 'save_seconds': fields['f48']}


def file_owners(tree, index, refs, header, child_header, native_child):
    model, = (row for row in tree.iter() if LocalName(row) == 'swModel' and int(row.attrib['id']) == index['root_model_id'])
    links = children(model, 'swReference')
    foreign_ref = {row.attrib['swModelRef'] for row in links}
    child, = (row for row in tree.iter() if LocalName(row) == 'swModel' and row.attrib['id'] in foreign_ref)
    files = {row.attrib['id']: row.attrib for row in tree.iter() if LocalName(row) == 'swFile'}
    parent_file, child_file = (files[row.attrib['swFileRef']] for row in (model, child))
    parent_key = ReadFileKey(header.FieldsValue['f38'])
    child_key = ReadFileKey(child_header.FieldsValue['f38'])
    fields = tuple(row.FieldsValue for row in refs.values())
    external = fields[0]['f3b0']
    directory = ReadFileKey(external)
    require(all(row['f3b0'] is external for row in fields) and len(foreign_ref) == 1
            and directory[:1] + directory[2:] == child_key[:1] + child_key[2:]
            and PureWindowsPath(directory[1]) == native_child and child_file['swPath'] == directory[1]
            and PureWindowsPath(child_key[1]).drive.startswith('\\\\') and child_key[1] != directory[1]
            and parent_file['swPath'] == parent_key[1]
            and int(parent_file['swCreationTime']) == parent_key[3] and int(child_file['swCreationTime']) == child_key[3],
            'both direct child references must own the copied child and the actual stored locator')
    child_stamp, = {FieldInt(row, 'f3e0') for row in fields}
    config_owner = (int(child.attrib['swConfigurationId']), child.attrib['swConfigurationName'])
    require(all((row['f3c0']['f10'], row['f3c0']['f08']) == config_owner and row['hidden'] == 0 for row in fields)
            and all((int(row.attrib['swConfigurationId']), row.attrib['swConfigurationName']) == config_owner for row in links)
            and child_stamp == int(child.attrib['swLastModifiedStamp'])
            and int(model.attrib['swLastModifiedStamp']) == header.FieldsValue['f40'], 'owner stamp, configuration or default visibility differs')
    return {'parent_xml_model': int(model.attrib['id']), 'parent_xml_file': int(parent_file['id']),
            'child_xml_model': int(child.attrib['id']), 'child_xml_file': int(child_file['id']),
            'child_configuration': config_owner, 'root_stamp': int(model.attrib['swLastModifiedStamp']),
            'child_reference_stamp': child_stamp, 'child_file_signature': list(directory[2:]),
            'binary_occurrence_reference_words': {key: [row[key] for row in fields]
                                                  for key in ('f3e0', 'f3e8', 'f3f0', 'f3f4', 'f3f8', 'hidden')},
            'parent_path_sha256': digest(parent_key[1].encode()), 'child_path_sha256': digest(directory[1].encode()),
            'child_file_header_path_sha256': digest(child_key[1].encode()), 'child_path_class': 'Z:',
            'child_file_header_path_class': 'UNC', 'shared_child_directory': True}


def display_groups(rows, state_keys, classes, role, owner, usage):
    require(tuple(row['key'] for row in rows) == state_keys, 'outer visual keys differ from the named states')
    result = {}
    for row in rows:
        key = row['key']
        attrs = tuple(record['o'] for record in row['objs'])
        require(row['k'] == len(attrs) == len(classes) and tuple(item.cls for item in attrs) == classes
                and attrs[0].f['f10'] is None and all(item.f['f08'] == 1 for item in attrs), 'default attribute ownership differs')
        words = tuple(FieldInt(attrs[1].f, field) for field in ('f10', 'f14', 'f18', 'f1c'))
        for item in attrs:
            usage[item].append((role, owner, key))
        result[key] = words
        if len(attrs) == 3:
            require(attrs[2].f['f18'] == 1 and attrs[2].f['f10'] == '<Default>_Display State 1', 'internal display alias differs')
    return result


def visual_graph(data, reg, source, config, refs, planes, header, states):
    with reg.track_usage('load', VISUAL, sources=source.streams) as load:
        doc, ar = load_visual_states(data, reg)
    with reg.track_usage('store', VISUAL) as store:
        output = store_visual_states(doc, reg)
    audits = [event.snapshot() for event in (load, store)]
    require(output == data and not doc.tail and all(event['completed'] and not event['missing_schemas']
            and not event['raw_operations'] for event in audits), 'visual replay has a gap or an opaque field')
    f = RequireNode(doc.head['root'], 'visStateKeyData_c').FieldsValue
    keys = tuple(range(1, len(states) + 1))
    expected = {key: dict(zip(IDS, vector, strict=True)) for key, (_, vector) in zip(keys, states, strict=True)}
    require(doc.head['file_version'] == 19000 and doc.head['shown'] == 0 and (f['f15c'], f['f158']) == (5, 0)
            and f['n_ids'] == 1 and f['f118'] == [{'key': config, 'value': 1, 'one': 1}]
            and f['n_states'] == len(f['f0f0']) == len(states) and f['n_comps'] == len(f['comps']) == 2
            and f['n_ents'] == len(f['f78']) == 3 and f['n_f88'] == len(f['f88']) == f['n'] == len(f['f08']) == 0,
            'unexpected independent visual-state structure')
    for key, (label, _), row in zip(keys, states, f['f0f0'], strict=True):
        require(row == {'id': key, 'name': label, 'f384': 0, 'f394': 0, 'f38c': 0}, 'visual state ID, name or metadata differs')
    head = RequireNode(header.FieldsValue['f38'], 'moExtObject_c').FieldsValue['shared']
    usage = defaultdict(list)
    components, visuals, files = [], {}, {}
    for row in f['comps']:
        context = RequireNode(row['comp'], COMP_CLASS).FieldsValue
        chain = RequireNode(context['f20'], 'moReferenceChain_c').FieldsValue
        container = RequireNode(chain['f08'], 'moExtFeatureList_c').FieldsValue
        own, = container['f08']
        feature = RequireNode(own['o'], 'moExtFeature_c').FieldsValue
        occurrence = FieldInt(feature, 'f44')
        ordinary = refs[occurrence]
        actual = RequireNode(ordinary.FieldsValue['f4f8'], 'moExtFeature_c').FieldsValue
        require(chain['f24'] == container['n'] == 1 and actual['f50'] is ordinary and actual['f44'] == occurrence
                and feature['f50'] is None and ctext(feature['f38']) == ReadNodeName(ordinary), 'visual occurrence join differs')
        components.append(occurrence)
        main = feature['f10']
        contextual = RequireNode(context['f40'], 'moExtObject_c').FieldsValue['shared']
        require(file_signature(main) == file_signature(contextual) == file_signature(head)
                and main['h18'] is contextual['h18'] and ctext(main['h18']) == '' and ctext(head['h18'])
                and main['h10'] is not contextual['h10'] and ctext(main['h10']) == ctext(head['h10'])
                and ctext(contextual['h10']) == 'Assem1' and row['m'] == len(keys), 'local file-handle aliases differ')
        files[occurrence] = {'shared_empty_path': record_text(main['h18']), 'external_title': record_text(main['h10']),
                             'historical_context_title': record_text(contextual['h10']), 'context_word': context['f30']}
        attrs = display_groups(row['attrs'], keys, ATTRIBUTE_CLASSES, 'occurrence', occurrence, usage)
        require(all(words == (expected[key][occurrence], 6, 0, 1) for key, words in attrs.items()),
                'the saved visibility word and native authored vector disagree')
        visuals[occurrence] = attrs
    plane_words = {}
    for row in f['f78']:
        ref = RequireNode(row['ref'], 'moCompFeature_c').FieldsValue['ff0']
        plane = RequireNode(planes[ref['f00']], PLANE_CLASS)
        require(ref['f08'] == ReadMemberTime(plane).SecondsValue and row['m'] == len(keys), 'visual plane owner differs')
        attrs = display_groups(row['attrs'], keys, ATTRIBUTE_CLASSES[:2], 'plane', ref['f00'], usage)
        require(all(words == (0, 6, 1, 0) for words in attrs.values()), 'plane visual values differ')
        plane_words[ref['f00']] = {'name': ReadNodeName(plane), 'attributes': attrs}
    require(tuple(components) == tuple(reversed(IDS)) and set(plane_words) == set(planes), 'VisualStates owner inventory differs')
    classes = Counter(entry.EntryValue.ClassValue.NameValue for entry in ar.map_state().state.EntriesValue
                      if isinstance(entry.EntryValue, ArchiveNode))
    aliases = [{'slot': item.IndexValue, 'class': item.cls, 'wire_bytes': item.EndOffset - item.StartOffset,
                'inner_owner_id': item.f['f08'], 'users': users} for item, users in sorted(usage.items(), key=lambda row: row[0].IndexValue)]
    facts = {'bytes': len(data), 'sha256': digest(data), 'typed_bytes': len(data), 'opaque_bytes': 0, 'byte_identity': True,
             'map_counter': ar.count, 'class_counts': dict(classes), 'configuration_association': f['f118'],
             'states': f['f0f0'], 'occurrence_order': components, 'occurrence_attributes': visuals,
             'plane_attributes': plane_words, 'aliases': aliases, 'parent_file_handle_aliases': files,
             'provisional_schemas': sorted({name for event in audits for name in event['provisional_schemas']})}
    return doc, facts


def isolate_visual(old, new, doc, reg, left, right):
    def filtered(state_count, component_count, plane_count):
        model = deepcopy(doc)
        fields = model.head['root'].f
        fields['f0f0'] = fields['f0f0'][:state_count]
        fields['n_states'] = state_count
        for rows, count in ((fields['comps'], component_count), (fields['f78'], plane_count)):
            for row in rows:
                row['attrs'] = row['attrs'][:count]
                row['m'] = count
        return store_visual_states(model, reg)

    require(filtered(1, 1, 1) == old and filtered(3, 3, 3) == new, 'pruned after-save visual graph does not recover the exact baseline')
    stages = [len(old), len(filtered(3, 1, 1)), len(filtered(3, 3, 1)), len(new)]
    counts = [b - a for a, b in zip(stages, stages[1:])]
    classes = Counter(right['class_counts']) - Counter(left['class_counts'])
    hidden, = (row for row in right['aliases'] if row['users'] == [('occurrence', 25, 2), ('occurrence', 24, 3)])
    require(counts == [118, 76, 72] and hidden['wire_bytes'] == 22 and right['map_counter'] - left['map_counter'] == 1
            and classes == {ATTRIBUTE_CLASSES[1]: 1} and right['parent_file_handle_aliases'] == left['parent_file_handle_aliases'],
            'unexpected visual addition or locator alias change')
    return {'bytes_added': len(new) - len(old), 'byte_exact_after_pruning': True, 'states_table_bytes': counts[0],
            'component_map_entries_bytes': counts[1] - (hidden['wire_bytes'] - 2),
            'new_shared_hidden_attribute_body_bytes': hidden['wire_bytes'] - 2, 'plane_map_entries_bytes': counts[2],
            'file_handle_alias_byte_growth': 0, 'map_counter_delta': 1, 'added_object_classes': dict(classes)}


def audit(packet):
    require(packet.name == PACKET, 'use the exact disclosed packet 04')
    payloads = {key: checked(packet / path, expected) for key, (path, expected) in PINS.items()}
    native, states, mapped = native_receipt(payloads)
    archives = {side: SldprtArchive.from_bytes(payloads[side]) for side in ('before', 'after', 'child')}
    child_header = ReadHeaderGraph(archives['child'].require('Contents/Config-0-ModelHeader'), 19000)
    child = archive_stamps(archives['child'], child_header)
    reg = registry()
    cases, xmls, managers, additions = {}, {}, {}, {}
    for side, scoped in (('before', states[:1]), ('after', states)):
        archive = archives[side]
        refs, config, config_name, planes, header = model_inputs(archive)
        raw = archive.require(INSTANCE)
        tree = XmlRoot(raw)
        require(xml_bytes(tree) == raw, 'component XML reserialization differed')
        xmls[side], index, additions[side] = index_graph(tree, refs, config, config_name, scoped)
        owner = file_owners(tree, index, refs, header, child_header, mapped)
        require(digest(str(mapped).encode()) == owner['child_path_sha256'],
                'the stored same-destination child locator differs from the observed native alias')
        stamps = archive_stamps(archive, header)
        manager_data = archive.require('Contents/CMgr')
        manager = ReadCmgrMut(manager_data, 19000).RootValue
        require(WriteCmgrMut(manager, 19000) == manager_data and manager.FieldsValue['f360'].FieldsValue['f860'] == stamps['update_stamp'],
                'configuration manager byte replay or root update stamp differs')
        managers[side] = manager
        doc, visual = visual_graph(archive.require(VISUAL), reg, archive, config, refs, planes, header, scoped)
        _, keywords = ParseKeywords(archive.require(KEYWORDS))
        require(not any(row.kind in ('DisplayState', 'Display State') or row.name in index['states'] for row in keywords),
                'unexpected KeyWords display state owner')
        cases[side] = {'native_bytes': len(payloads[side]), 'xml': index | {'bytes': len(raw), 'typed_bytes': len(raw),
                       'opaque_bytes': 0, 'sha256': digest(raw), 'byte_identity': True}, 'visual': visual,
                       'linked_files': owner, 'parent_stamps': stamps, 'cmgr_bytes': len(manager_data)}
    left, right = (cases[key] for key in ('before', 'after'))
    ref_stamps = [row['linked_files']['child_reference_stamp'] for row in (left, right)]
    require(ref_stamps == [148, 162] and child['update_stamp'] == 134, 'expected persisted child-vs-parent stamp discrepancy differs')
    count_growth = len(str(right['xml']['actual_xml_object_count'])) - len(str(left['xml']['actual_xml_object_count']))
    require(right['xml']['bytes'] - left['xml']['bytes'] == count_growth + sum(additions['after'].values()),
            'new leaf frames and object count do not explain the XML growth')
    for node in xmls['after'].iter():
        if LocalName(node) == 'swModel':
            node.set('swLastModifiedStamp', str(left['linked_files']['root_stamp'] if node.attrib['id'] == '2' else ref_stamps[0]))
    require(xml_bytes(xmls['after']) == archives['before'].require(INSTANCE), 'XML changed outside direct display leaves, count and two stamps')
    old, new = (archives[side].require(VISUAL) for side in ('before', 'after'))
    visual_delta = isolate_visual(old, new, doc, reg, left['visual'], right['visual'])
    cmgr, aliases = compare_typed(managers['before'], managers['after'])
    _, reverse_aliases = compare_typed(managers['after'], managers['before'])
    locator = managers['after'].FieldsValue['f1f8']
    expected = {'f1f8': ['', locator], 'f860': [106, 114], 'f18': [109, 111]}
    require(not aliases and not reverse_aliases and {key.rsplit('/', 1)[1]: values for key, values in cmgr.items()} == expected
            and len(cmgr) == 3 and digest(locator.encode()) == right['linked_files']['parent_path_sha256']
            and right['cmgr_bytes'] - left['cmgr_bytes'] == len(locator.encode('utf-16le')), 'configuration manager delta differs')
    cmgr_delta = {key: (values if key.rsplit('/', 1)[1] != 'f1f8' else [len(value) for value in values]) for key, values in cmgr.items()}
    before, after = (archives[side].streams for side in ('before', 'after'))
    changed_streams = {name: [len(before.get(name, b'')), len(after.get(name, b''))] for name in sorted(before.keys() | after.keys())
                       if before.get(name) != after.get(name)}
    sources = (Path(__file__), SW2026 / 'para/concentric/AuditConcentricDisplayState.py',
               SW2026 / 'serial/defs/Visual.py', SW2026 / 'serial/defs/VisualRefs.py')
    return {'schema': 'kit.sw2026.concentric-display-authoring-audit.v1', 'evidence_sha256': {key: value[1] for key, value in PINS.items()},
            'reader_sources_sha256': {str(path.relative_to(REPO)): digest(path.read_bytes()) for path in sources},
            'native_observations': native, 'archives': cases, 'child_file_stamps': child, 'child_reference_stamps': ref_stamps,
            'child_stamp_discrepancies': [stamp - child['update_stamp'] for stamp in ref_stamps],
            'xml_delta': {'bytes_added': right['xml']['bytes'] - left['xml']['bytes'], 'added_leaf_bytes': additions['after'],
                          'object_count_byte_growth': count_growth, 'exact_after_reverting_leaves_count_stamps': True},
            'visual_delta': visual_delta, 'cmgr_delta': {'bytes_added': right['cmgr_bytes'] - left['cmgr_bytes'], 'field_changes': cmgr_delta},
            'changed_stream_sizes': changed_streams, 'precedence_measured': False, 'cache_omission_qualified': False,
            'heldout_inputs_read': 0, 'native_processes_started_by_audit': 0, 'cad_outputs_written': 0, 'audit_passed': True}


def main():
    parser = argparse.ArgumentParser(description='Replay the disclosed packet 04 display-state archive audit')
    parser.add_argument('packet', type=Path)
    parser.add_argument('receipt', type=Path)
    args = parser.parse_args()
    result = audit(args.packet.resolve())
    with args.receipt.open('x') as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
