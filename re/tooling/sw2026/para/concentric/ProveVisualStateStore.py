from __future__ import annotations

import argparse
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


SW2026 = Path(__file__).resolve().parents[2]
REPO = SW2026.parents[2]
sys.path[:0] = [str(REPO), str(REPO / 'src'), str(SW2026), str(SW2026 / 'serial')]

from Classes import registry
from defs.Visual import load_visual_states, store_visual_states
from para.concentric.AuditConcentricDisplayState import ctext, checked, D01_LOCKED, file_signature, model_inputs, PUBLISHED_MANIFEST, published_cases, ReadCmgrMut
from para.concentric.MakeDisplayTree import DisplayListIntent, DisplayStateIntent, make_display_tree
from para.concentric.MakeVisualStateStore import CONTEXT_WORDS, DEFAULT_ALIAS, DEFAULT_NAME, STREAM, UNSELECTED, feature_log, make_visual_store, need
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import CompRefFields
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import ReadMemberTime
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


NATIVE_RECEIPT = 'e14c77749cd68ed554bbbdbf014d1360df9fa58a1524976329d93976b48e5d71'
AUTHOR_RECEIPT = '1b008f32adcaaadd61a1d072ae3a012f8136418a5a6a9fe51b8fc65c2228587a'
PARENT = '1b5f9a87c6db9b6c22c9fd445338cd1d478045e1e3fbccbd2c8ac17ccb7f7ceb'
CHILD = '8dd479a4f05a1baf8d0a4166e1f4247e82f3f125933173e0de964dc64e74ab22'
STALE_CHILD = '92b83376b42ca55aa3b32a350635585c788ea0f968cc6e54f1730fdeb3c99caa'
STRUCTURAL_REVISION = '38dc82ee2e6e78a43078b63876eb8649020c9e2e'
STRUCTURAL_RECEIPT = 'adb6a793fe3e0489d5d081e15a6c0fcd35fa574f8b6ac9f42939330df3f88753'


def digest(data):
    return sha256(data).hexdigest()


def detached_context(node):
    fields = node.FieldsValue
    chain = fields['f20'].FieldsValue
    target, = chain['f08'].FieldsValue['f08']
    feature = target['o'].FieldsValue
    return feature['f44'], fields, chain, feature, fields['f40'].FieldsValue


def show_words(node):
    return tuple(node.f[key] for key in ('f08', 'f10', 'f14', 'f18', 'f1c'))


def replay(archive, reg):
    data = archive.require(STREAM)
    with reg.track_usage('load', STREAM, sources=archive.streams) as load:
        doc, reader = load_visual_states(data, reg)
    with reg.track_usage('store', STREAM) as write:
        same = store_visual_states(doc, reg) == data
    usage = [load.snapshot(), write.snapshot()]
    need(same and not doc.tail and all(row['completed'] and not row['raw_operations'] and not row['missing_schemas'] for row in usage),
         'typed VisualStates replay differs or contains opaque data')
    summary = {'bytes': len(data), 'sha256': digest(data), 'terminal_map': reader.count, 'byte_identity': same,
               'opaque_bytes': 0, 'provisional_schemas': sorted({name for row in usage for name in row['provisional_schemas']})}
    return doc, summary


def member_seconds(node):
    fields = node.FieldsValue
    return None if fields['f2a0'] == fields['f2a4'] == 0 else ReadMemberTime(node).SecondsValue


def owner_clocks(archive, doc):
    link = ReadNativeLink(archive, 0)
    header = link.ConfigValue.HeaderValue
    top_header = ReadHeaderGraph(archive.require('Header2'), 19000)
    features = {row.FieldsValue['f08']: row for row in link.ResolvedValue.RootsValue}
    rows = []
    for row in doc.head['root'].f['f78']:
        reference = row['ref'].FieldsValue.get('ff0')
        if reference is None:
            continue
        feature_id = reference['f00']
        actual = features[feature_id]
        count = []
        for owner in (header, top_header):
            log = feature_log(owner, feature_id)
            count.append(None if log is None else len(log[1]))
        left, right = (DatumTime(owner, feature_id) for owner in (header, top_header))
        need(left == right == reference['f08'], 'VisualStates feature time disagrees with actual ordered header logs')
        rows.append({'feature_id': feature_id, 'class': actual.ClassValue.NameValue, 'visual_seconds': reference['f08'],
                     'resolved_filetime_seconds': member_seconds(actual), 'config_creation_seconds': left,
                     'header2_creation_seconds': right, 'log_event_counts': count})
    return link, rows


def parent_locator(archive, header):
    data = archive.require('Contents/CMgr')
    manager = ReadCmgrMut(data, 19000).RootValue
    locator = manager.FieldsValue['f1f8']
    current = ctext(header.FieldsValue['f38'].FieldsValue['shared']['h18'])
    need(WriteCmgrMut(manager, 19000) == data and (not locator or locator == current), 'CMgr inherited locator does not replay or match the actual Header')
    return {'codepoints': len(locator), 'header_codepoints': len(current), 'matches_header': locator == current,
            'cmgr_bytes': len(data), 'cmgr_byte_identity': True}


def pinned_clock_contrasts(root, reg):
    d01 = root.parent / 'ConcentricMateSourcePacket02/Disclosed/D01/Native'
    visibility = root.parent / 'ConcentricDisplayVisibility04'
    author = json.loads(checked(REPO / 're/solidworks/measurements/2026/ConcentricDisplayAuthoring04.json', AUTHOR_RECEIPT))
    extra = {f'D01{role}': (d01 / role / 'ConcentricD01AlignedFree.SLDASM', pins[0]) for role, pins in D01_LOCKED.items()}
    extra.update({'D01BeforeNamed': (visibility / 'Inspection/Author/Before.SLDASM', author['evidence_sha256']['before']),
                  'D01AfterNamed': (visibility / 'Working/ConcentricD01AlignedFree.SLDASM', author['evidence_sha256']['after'])})
    parents = {}
    for name, (path, pin) in extra.items():
        archive = SldprtArchive.from_bytes(checked(path, pin))
        doc, replay_proof = replay(archive, reg)
        link, clocks = owner_clocks(archive, doc)
        parents[name] = replay_proof | {'native_parent_sha256': pin, 'plane_clocks': clocks,
                                        'cmgr_locator': parent_locator(archive, link.ConfigValue.HeaderValue)}
    children = {f'D01{role}': (d01 / role / 'ConcentricD01Child.SLDPRT', pins[1]) for role, pins in D01_LOCKED.items()}
    children.update({'D01Synchronized': (root / 'Revisions/Synchronized/ConcentricD01Child.SLDPRT', CHILD),
                     'D01Stale': (root / 'Revisions/Stale/ConcentricD01Child.SLDPRT', STALE_CHILD)})
    corpus = REPO / 're/solidworks/v2026/corpus/assembly-synchronized'
    manifest = json.loads(checked(corpus / 'Manifest.json', PUBLISHED_MANIFEST))
    need(manifest['heldout_payloads_read'] is False, 'synchronized part controls must be disclosed')
    for row in manifest['records']:
        if row['role'] == 'child':
            children[row['name']] = (corpus / row['file'], row['sha256'])
    child_proofs = {}
    for name, (path, pin) in children.items():
        archive = SldprtArchive.from_bytes(checked(path, pin))
        doc, replay_proof = replay(archive, reg)
        link, clocks = owner_clocks(archive, doc)
        fields = doc.head['root'].f
        holder, *entities = fields['f78']
        config = ReadCmgrMut(archive.require('Contents/CMgr'), 19000).RootValue.FieldsValue['f360']
        model = link.ConfigValue.RootValue.FieldsValue
        properties = holder['attrs'][0]['objs'][0]['o'].f['f10']
        need(fields['n_comps'] == 0 and fields['n_ents'] == 6 and holder['ref'].cls == 'moCompHolder_c'
             and properties.cls == 'moVisualProperties_c' and fields['f0f0'][0]['name'] == DEFAULT_ALIAS
             and len(clocks) == len(entities) == 5 and all(v['log_event_counts'] == [2, 2] and v['visual_seconds'] != v['resolved_filetime_seconds'] for v in clocks),
             'independent child appearance or creation-log contrast differs')
        root_rv, selected_rv, holder_rv = (row.FieldsValue['f20']['f90'] for row in (model['f78'], config.FieldsValue['f78'], properties))
        need(root_rv == selected_rv and root_rv['f00'] != holder_rv['f00'] and root_rv['f68'] != holder_rv['f68'],
             'child appearance holder must remain distinct from its actual model/config visual owner')
        child_proofs[name] = replay_proof | {'native_child_sha256': pin, 'feature_clocks': clocks, 'entity_rows': 6,
            'holder_appearance_present': True, 'holder_rv_record_id': holder_rv['f00'], 'model_rv_record_id': root_rv['f00'],
            'holder_rv_locator_codepoints': len(holder_rv['f68']), 'model_rv_locator_codepoints': len(root_rv['f68'])}
    need(len(child_proofs) == 6 and child_proofs['D01Stale']['sha256'] == child_proofs['D01Synchronized']['sha256'],
         'child creation-log controls or the warning-clearing sync comparison differ')
    return parents, child_proofs


def source_evidence(root, reg):
    native = json.loads(checked(REPO / 're/solidworks/measurements/2026/ConcentricDisplaySyncNative01.json', NATIVE_RECEIPT))
    clean = native['paired_cold_opens']['Synchronized']
    need(native['native_authored_parent_sha256'] == PARENT and clean['child_sha256'] == CHILD and native['controls_healthy']
         and clean['open_warning'] == clean['open_error'] == 0 and clean['named_and_live_visibility_match']
         and native['paired_cold_opens']['Stale']['child_sha256'] == STALE_CHILD, 'pinned synchronized native receipt differs')
    cases = [('D01Sync', root / 'Revisions/ConcentricD01AlignedFree.SLDASM', PARENT)]
    cases += [(name, path, wanted) for name, path, wanted, *_ in published_cases()]
    result = {}
    for name, path, wanted in cases:
        archive = SldprtArchive.from_bytes(checked(path, wanted))
        doc, proof = replay(archive, reg)
        link, clocks = owner_clocks(archive, doc)
        model = link.ConfigValue.RootValue
        refs, config, cname, planes, header = model_inputs(archive)
        parent = header.FieldsValue['f38'].FieldsValue['shared']
        fields = doc.head['root'].f
        ids = tuple(state['id'] for state in fields['f0f0'])
        names = tuple(state['name'] for state in fields['f0f0'])
        vectors = clean['native_default_and_mixed_visibility'] if name == 'D01Sync' else {DEFAULT_NAME: (1,) * len(refs)}
        need(doc.head['file_version'] == 19000 and doc.head['shown'] == fields['f158'] == fields['n_f88'] == fields['n'] == 0
             and fields['f15c'] == 5 and fields['f118'] == [{'key': config, 'value': 1, 'one': 1}]
             and ids == tuple(range(1, len(names) + 1)) and names == tuple(vectors)
             and all(row[k] == 0 for row in fields['f0f0'] for k in ('f384', 'f394', 'f38c')), 'native VisualStates header profile differs')
        prefix = CompRefFields(model.FieldsValue['f990'])
        plane_ids = []
        appearances = set()
        for row in fields['f78']:
            feature = row['ref'].FieldsValue
            identity = feature['ff0']
            need(all(feature[key] == value for key, value in prefix.items() if key != 'f58')
                 and feature['f58'].FieldsValue == {'owner': None, 'has_ext': 0}, 'native plane owner or shared constructor fields differ')
            need(tuple(item['key'] for item in row['attrs']) == ids, 'native plane state map keys differ')
            for item in row['attrs']:
                props, plane_display = (entry['o'] for entry in item['objs'])
                need(props.f == {'f08': 1, 'f10': None} and show_words(plane_display) == (1, 0, 6, 1, 0), 'native plane display attribute words differ')
                appearances.add(props)
            plane_ids.append(identity['f00'])
        need(tuple(plane_ids) == tuple(reversed(planes)), 'native persistent plane order differs')
        selected = ReadCmgrMut(archive.require('Contents/CMgr'), 19000).RootValue.FieldsValue['f360'].FieldsValue
        manager_contexts = {key: (ctx, path, file) for key, ctx, path, _, file in (
            detached_context(row['o'].FieldsValue['f10']) for row in selected['fce8'] if row['o'].FieldsValue['f10'] is not None)}
        contexts = []
        for row in fields['comps']:
            identity, ctx, chain, ext, file = detached_context(row['comp'])
            flag = file['f58']
            actual_context, actual_chain, actual_file = manager_contexts[identity]
            need(flag == (8 if name == 'D01Sync' else 0) and ctx['owner'] is None and ctx['f48'] == 0
                 and chain['f24'] == 1 and chain['f20'] == 0 and chain['f40'] == UNSELECTED
                 and ext['f50'] is None and ext['f18'] == UNSELECTED and ext['f40'] == 0 and ext['f58'] == -1
                 and ReadFileText(ext['f38']) == ReadNodeName(refs[identity])
                 and file['refcfg'] == UNSELECTED and flag == actual_file['f58'] and actual_chain['f24'] == 0
                 and actual_file['refcfg'] == {'f08': cname, 'f10': config}
                 and file_signature(ext['f10']) == file_signature(file['shared']) == file_signature(parent)
                 and all(file[k] == value for k, value in CONTEXT_WORDS.items() if k != 'f58')
                 and tuple(item['key'] for item in row['attrs']) == ids,
                 'native occurrence reference fields or attribute ownership differ')
            for state_name, item in zip(names, row['attrs'], strict=True):
                props, visible, label = (entry['o'] for entry in item['objs'])
                expected = vectors[state_name][tuple(refs).index(identity)]
                need(props.f == {'f08': 1, 'f10': None} and show_words(visible) == (1, expected, 6, 0, 1)
                     and label.f == {'f08': 1, 'f10': DEFAULT_ALIAS, 'f18': 1}, 'native visibility or label action differs')
                appearances.add(props)
            derived = (101 + refs[identity].FieldsValue['f3f0']) & 0xFFFFFFFF
            path_alias = ext['f10']['h18'] is file['shared']['h18']
            title_alias = ext['f10']['h10'] is file['shared']['h10']
            need(path_alias and title_alias == (flag == 0), 'native path/title alias contrast differs')
            need((ctx['f30'], actual_context['f30']) == ((derived, derived) if flag == 0 else (101, 203)),
                 'native context stamp contrast differs')
            contexts.append({'feature': identity, 'chain_mode': chain['f24'], 'chain_stamp': ctx['f30'],
                             'cmgr_chain_mode': actual_chain['f24'], 'cmgr_chain_stamp': actual_context['f30'], 'file_flag': flag,
                             'path_alias': path_alias, 'title_alias': title_alias})
        need(tuple(row['feature'] for row in contexts) == tuple(reversed(refs)) and len(appearances) == 1, 'native occurrence cache order or null appearance alias differs')
        result[name] = proof | {'native_parent_sha256': wanted, 'configuration': [config, cname], 'plane_order': plane_ids,
                                'state_count': fields['n_states'], 'contexts': contexts, 'plane_clocks': clocks,
                                'cmgr_locator': parent_locator(archive, header)}
    need(result['D01Sync']['sha256'] == native['unchanged_display_streams'][STREAM], 'native synchronized store digest differs')
    extra, children = pinned_clock_contrasts(root, reg)
    parents = result | extra
    need(len(parents) == 8 and all(len(case['plane_clocks']) == 3 and all(v['log_event_counts'] == [2, 2]
         and v['visual_seconds'] == v['resolved_filetime_seconds'] for v in case['plane_clocks']) for case in parents.values()),
         'pinned parent archive clock congruence differs')
    return {'sync_receipt_sha256': NATIVE_RECEIPT, 'author_receipt_sha256': AUTHOR_RECEIPT, 'parents': parents, 'children': children,
            'parent_plane_rows_matching_both_representations': 24, 'child_feature_rows_matching_creation_log': 30,
            'child_feature_rows_matching_resolved_filetime': 0}


def generated_proof(reg, audit):
    from SdkAssemblySettings import assembly_settings, mate_settings, occurrence_settings
    from SdkBlindPartSettings import settings
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import MakeAsmCase
    from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmInput import CheckAsmInput
    from convert.adapters.solidworks.Archive.Construction.Assembly.EmitAsmStreams import EmitAsmStreams
    from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.MakeAsmHeaders import MakeAsmHeaders
    from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmBase import MakeAsmBase
    from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAsmMateMut import MakeAsmMateMut
    from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAssembly import MakeAssembly
    from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.PutOccsMut import PutOccsMut
    from convert.adapters.solidworks.Archive.Construction.Header.MakeRootLog import MakeRootLog
    from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTime import FeatureTime
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
    from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
    from convert.adapters.solidworks.Container.Container import BuildSldprt
    from convert.adapters.solidworks.Container.Format import KComponentTreeStream
    import interchange.document.Validation.DocumentAssemblyValidate
    import interchange.document.Validation.DocumentFeatureValidate
    import interchange.document.Validation.DocumentReferenceValidate
    from interchange.serialization.Deserialize import FromData

    for encoding in ('utf-16-le', 'utf-16-be', 'cp1252', 'utf-8', 'latin-1'):
        lookup(encoding)
    audit.BeginBuild()

    def construct(child, inputs, poses, mate_input, epochs, member_times):
        CheckAsmInput(child, inputs, poses, mate_input)
        state = MakeAsmBase(inputs)
        for axis, seconds in member_times.items():
            state.PlaneValues[axis].FieldsValue.update(FeatureTime(seconds))
        headers = MakeAsmHeaders(state, inputs)
        for header in headers:
            log_list = header.FieldsValue['f20'].FieldsValue
            log_list['items'] = (*log_list['items'], *(MakeRootLog(state.PlaneValues[axis], replace(inputs.HeaderValue, CreatedAt=seconds))
                                                       for axis, seconds in epochs.items()))
        refs = PutOccsMut(state, child, inputs, poses, headers)
        mate = MakeAsmMateMut(state, child, inputs, mate_input, refs, headers)
        return state, headers, refs, EmitAsmStreams(state, child, inputs, headers, refs, mate).StreamsValue

    def check_store(archive, state, header, refs, intent, epochs):
        doc, proof = replay(archive, reg)
        link, clocks = owner_clocks(archive, doc)
        fields = doc.head['root'].f
        ids = tuple(row.FieldsValue['f08'] for row in refs)
        parent = header.FieldsValue['f38'].FieldsValue['shared']
        wanted_states = [(index, row.name) for index, row in enumerate(intent.states, 1)]
        need(fields['f118'] == [{'key': intent.configuration_id, 'value': 1, 'one': 1}]
             and [(row['id'], row['name']) for row in fields['f0f0']] == wanted_states
             and fields['n_comps'] == 2 and fields['n_ents'] == 3, 'new typed store loses actual configuration, order or counts')
        aliases = {'properties': set(), 'label': set(), 'visible': set(), 'hidden': set(), 'plane': set(), 'detached_plane_components': set()}
        owners = {'h10': set(), 'h18': set()}
        context_info = []
        visibility_by_id = {identity: [] for identity in ids}
        for row in fields['comps']:
            identity, ctx, chain, ext, file = detached_context(row['comp'])
            need(file['f58'] == 0 and file['refcfg'] == UNSELECTED and chain['f24'] == 1 and chain['f40'] == UNSELECTED
                 and ext['f50'] is None and ctx['f30'] == (101 + next(ref.FieldsValue['f3f0'] for ref in refs if ref.FieldsValue['f08'] == identity))
                 and ReadFileText(ext['f38']) == ReadNodeName(refs[ids.index(identity)]), 'new Visual occurrence lost the generated typed owner')
            for key in owners:
                need(ext['f10'][key] is file['shared'][key] and ReadFileText(ext['f10'][key]) == ReadFileText(parent[key]), 'new owner file alias differs')
                owners[key].add(ext['f10'][key])
            context_info.append([identity, ctx['f30'], chain['f24'], file['f58']])
            for stored, authored, (key, _) in zip(row['attrs'], intent.states, wanted_states, strict=True):
                props, visual, label = (item['o'] for item in stored['objs'])
                visible = dict(authored.visibility)[identity]
                need(stored['key'] == key and stored['k'] == 3 and props.f == {'f08': 1, 'f10': None}
                     and label.f == {'f08': 1, 'f10': DEFAULT_ALIAS, 'f18': 1}
                     and show_words(visual) == (1, int(visible), 6, 0, 1), 'new typed state action or attribute tuple differs')
                visibility_by_id[identity].append(int(visible))
                aliases['properties'].add(props)
                aliases['label'].add(label)
                aliases['visible' if visible else 'hidden'].add(visual)
        need(tuple(row[0] for row in context_info) == tuple(reversed(ids)) and all(len(items) == 1 for items in owners.values()),
             'common parent path/title handles or generated occurrence order differ')
        owner_kind = 'moRefPlane_c'
        resolved = {row.FieldsValue['f08']: row for row in link.ResolvedValue.RootsValue if row.ClassValue.NameValue == owner_kind}
        config_planes = {row.EntryValue.FieldsValue['f08']: row.EntryValue for row in link.ConfigValue.MapValue.EntriesValue
                         if isinstance(row.EntryValue, ArchiveNode) and row.EntryValue.ClassValue.NameValue == owner_kind}
        authored = {node.FieldsValue['f08']: (epochs[axis] if epochs else 2592000) for axis, node in state.PlaneValues.items()}
        plane_ids = []
        for row in fields['f78']:
            handle = row['ref'].f
            identity, seconds = (handle['ff0'][key] for key in ('f00', 'f08'))
            need(seconds == authored[identity] and handle['f58'].f == {'owner': None, 'has_ext': 0},
                 'generated plane wire disagrees with the actual authored creation log')
            if identity in config_planes:
                need(config_planes[identity] is resolved[identity], 'Config plane alias and Resolved feature owner disagree')
            for stored, (key, _) in zip(row['attrs'], wanted_states, strict=True):
                props, visual = (item['o'] for item in stored['objs'])
                need(stored['key'] == key and stored['k'] == 2 and props.f == {'f08': 1, 'f10': None}
                     and show_words(visual) == (1, 0, 6, 1, 0), 'generated plane attribute tuple differs')
                aliases['properties'].add(props)
                aliases['plane'].add(visual)
            aliases['detached_plane_components'].add(handle['f58'])
            plane_ids.append(identity)
        sizes = {name: len(items) for name, items in aliases.items()}
        need(set(authored) == set(resolved) and tuple(plane_ids) == tuple(reversed(tuple(authored)))
             and sizes == {'properties': 1, 'label': 1, 'visible': 1, 'hidden': int(len(intent.states) > 1),
                           'plane': 1, 'detached_plane_components': 3}, 'generated alias groups or complete plane identities differ')
        return proof | {'contexts': context_info, 'plane_ids': plane_ids, 'authored_creation_seconds': authored,
                        'plane_clocks': clocks, 'config_inline_plane_ids': list(config_planes),
                        'state_names': [name for _, name in wanted_states], 'state_keys': [key for key, _ in wanted_states],
                        'visibility_by_occurrence': visibility_by_id, 'alias_object_counts': sizes,
                        'counts': {'states': fields['n_states'], 'occurrences': fields['n_comps'], 'planes': fields['n_ents']}}

    def stream_changes(first, second):
        need(set(first) == set(second), 'clock contrast added or removed a structural stream')
        return sorted(key for key, value in first.items() if value != second[key])

    results, refusals = [], {}
    for variant in (False, True):
        request = MakeAsmCase('coincident', 'x', variant)
        child = MakeBlindPart(FromData(request['child']['document']), settings(request['child']['settings']))
        inputs = assembly_settings(request['assembly'] | {'configuration_name': 'Display fixture' if variant else 'Default'})
        created = inputs.HeaderValue.CreatedAt
        inputs = replace(inputs, HeaderValue=replace(inputs.HeaderValue, ModifiedAt=created + 60, UpdatedAt=created + 61))
        if variant:
            inputs = replace(inputs, SystemValue=replace(inputs.SystemValue, HasEmptyExplodedView=True))
        poses, mate = occurrence_settings(request['occurrences']), mate_settings(request['mate'])
        baseline = MakeAssembly(child, inputs, poses, mate)
        first, second = (row.FieldsValue['f08'] for row in baseline.OccurrenceValues)
        states = [DisplayStateIntent(DEFAULT_NAME, ((second, True), (first, True)))]
        if variant:
            states += [DisplayStateIntent('Gauge seat', ((second, False), (first, True))),
                       DisplayStateIntent('Tool change', ((first, False), (second, True)))]
        intent = DisplayListIntent(baseline.StateValue.CurrentConfig.FieldsValue['f08'], tuple(states))
        axes = ('z', 'y', 'x')
        epochs = dict(zip(axes, (created + n for n in ((7, 11, 13) if variant else (1, 3, 5))), strict=True))
        filetimes = dict(zip(axes, (created + n for n in ((41, 43, 47) if variant else (29, 31, 37))), strict=True))
        state, headers, refs, stream_data = construct(child, inputs, poses, mate, epochs, {})
        repeated = construct(child, inputs, poses, mate, epochs, {})
        varied = construct(child, inputs, poses, mate, epochs, filetimes)
        header = headers[0]
        with reg.track_usage('store', STREAM) as use:
            visual = make_visual_store(state, headers, refs, intent, reg)
        need(visual == make_visual_store(*repeated[:3], intent, reg) == make_visual_store(*varied[:3], intent, reg)
             and stream_data == repeated[3] and not use.snapshot()['raw_operations'], 'neutral repeat or independent FILETIME changed the VisualStates archive')
        xml = make_display_tree(state, header, child, refs, intent)
        payload = BuildSldprt(dict(stream_data) | {STREAM: visual, KComponentTreeStream: xml}, FormatVersion=4)
        archive = SldprtArchive.from_bytes(payload)
        proof = check_store(archive, state, header, refs, intent, epochs)
        changed_archive = SldprtArchive.from_bytes(BuildSldprt(dict(varied[3]) | {STREAM: visual, KComponentTreeStream: xml}, FormatVersion=4))
        changed = check_store(changed_archive, varied[0], varied[1][0], varied[2], intent, epochs)
        base_headers = (baseline.HeaderValue, baseline.TopHeader)
        sentinel = make_visual_store(baseline.StateValue, base_headers, baseline.OccurrenceValues, intent, reg)
        sentinel_archive = SldprtArchive.from_bytes(BuildSldprt(dict(baseline.StreamsValue) | {STREAM: sentinel, KComponentTreeStream: xml}, FormatVersion=4))
        blank = check_store(sentinel_archive, baseline.StateValue, base_headers[0], baseline.OccurrenceValues, intent, {})
        opened = DecodeNativeAsm(archive)
        expected = [(row.name, ''.join('Yes,' if dict(row.visibility)[k] else 'No,' for k in (first, second))) for row in intent.states]
        need([(row.name, dict(row.attributes)['swShowState']) for row in opened.display_states] == expected
             and not child.StreamsValue.get(STREAM), 'the XML or independent generated child scope differs')
        log_deltas = stream_changes(baseline.StreamsValue, stream_data)
        filetime_deltas = stream_changes(stream_data, varied[3])
        expected_filetimes = {node.FieldsValue['f08']: filetimes[axis] for axis, node in varied[0].PlaneValues.items()}
        need(log_deltas == ['Contents/Config-0-ModelHeader', 'Header2'] and filetime_deltas == ['Contents/Config-0-ResolvedFeatures']
             and not proof['config_inline_plane_ids'] and not changed['config_inline_plane_ids'] and not blank['config_inline_plane_ids']
             and all(row['resolved_filetime_seconds'] is None and row['log_event_counts'] == [1, 1] for row in proof['plane_clocks'])
             and all(row['resolved_filetime_seconds'] == expected_filetimes[row['feature_id']] for row in changed['plane_clocks'])
             and all(row['log_event_counts'] == [None, None] and row['visual_seconds'] == 2592000 for row in blank['plane_clocks'])
             and visual != sentinel, 'the two clock owners or absent-log control are not independent')
        need(set(archive.streams) == set(stream_data) | {STREAM} and all(archive.require(key) == data for key, data in stream_data.items()
             if key != KComponentTreeStream), 'parent store construction rewrote another model stream')
        results.append(proof | {'configuration_name': ReadNodeName(state.CurrentConfig), 'configuration_id': intent.configuration_id,
                               'occurrence_feature_ids': [first, second], 'explicit_log_stream_deltas': log_deltas,
                               'independent_filetime_stream_deltas': filetime_deltas, 'visual_unchanged_by_filetime': True,
                               'filetime_perturbation': changed['plane_clocks'], 'absent_log_control': blank['plane_clocks'],
                               'unchanged_child_sha256': digest(child.BytesValue), 'container_sha256': digest(payload)})
        if not variant:
            feature_id = state.PlaneValues['x'].FieldsValue['f08']
            top_logs = headers[1].FieldsValue['f20'].FieldsValue
            items = top_logs['items']
            top_logs['items'] = tuple(log for log in items if log.FieldsValue['f48'] != feature_id)
            try:
                make_visual_store(state, headers, refs, intent, reg)
            except ValueError as error:
                refusals['missing_log_in_header2'] = str(error)
            finally:
                top_logs['items'] = items
            stamp = feature_log(headers[1], feature_id)[1][0]
            creation = stamp['f18']
            stamp['f18'] += 1
            try:
                make_visual_store(state, headers, refs, intent, reg)
            except ValueError as error:
                refusals['divergent_log_in_header2'] = str(error)
            finally:
                stamp['f18'] = creation
            context = state.CurrentConfig.FieldsValue['fce8'][1]['o'].FieldsValue['f10'].FieldsValue['f40'].FieldsValue
            context['f58'] = 8
            try:
                make_visual_store(state, headers, refs, intent, reg)
            except ValueError as error:
                refusals['context_flag_eight'] = str(error)
            finally:
                context['f58'] = 0
    need(set(refusals) == {'missing_log_in_header2', 'divergent_log_in_header2', 'context_flag_eight'} and not audit.DeniedReads,
         'guard scope or refusal failed')
    need(results[0]['occurrence_feature_ids'] != results[1]['occurrence_feature_ids'], 'generated occurrence identities failed to vary')
    return results, refusals


def main():
    parser = argparse.ArgumentParser(description='Author two independent mode-zero VisualStates stores in a guarded host process')
    parser.add_argument('disclosed_sync_packet', type=Path)
    args = parser.parse_args()
    checked(REPO / 're/solidworks/measurements/2026/ConcentricVisualStateStore01.json', STRUCTURAL_RECEIPT)
    source = source_evidence(args.disclosed_sync_packet.resolve(), registry())
    reg = registry()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    modules = (Path(__file__), *(Path(__file__).with_name(name) for name in ('MakeVisualStateStore.py', 'MakeDisplayTree.py',
                  'AuditConcentricDisplayState.py', 'ProveConcentricSourceBrep.py')),
               *(SW2026 / 'serial/defs' / name for name in ('Visual.py', 'VisualRefs.py', 'ResolvedComp.py')),
               *(REPO / 'src/convert/adapters/solidworks/Archive/Construction' / name for name in ('Assembly/System/MakeAsmPlane.py',
                  'Assembly/Occurrences/MakeOccConfig.py', 'Assembly/EmitAsmStreams.py', 'PlanarMates/CompRefFields.py',
                  'Nodes/FeatureTime.py', 'Header/MakeRootLog.py', 'PlanarMates/DatumTime.py', 'PlanarMates/ReadLogItems.py')))
    hashes = {str(path.relative_to(REPO)): digest(path.read_bytes()) for path in modules}
    audit = BuildAudit(SW2026 / 'serial/defs')
    sys.addaudithook(audit.InspectEvent)
    models, refusals = generated_proof(reg, audit)
    print(json.dumps({'schema': 'kit.sw2026.concentric-visual-creation-logs.v1', 'head': head, 'source_hashes': hashes,
                      'prior_filetime_structural_experiment': {'commit': STRUCTURAL_REVISION, 'receipt_sha256': STRUCTURAL_RECEIPT},
                      'disclosed_source_evidence': source, 'generated_models': models, 'refusals': refusals,
                      'runtime_input_io_attempts': len(audit.DeniedReads), 'cad_files_written': 0, 'native_processes_started': 0,
                      'native_acceptance': False, 'public_writer_qualified': False, 'heldout_inputs_read': 0, 'passed': True},
                     indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
