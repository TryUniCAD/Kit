from __future__ import annotations

from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


SW2026 = Path(__file__).resolve().parents[2]
REPO = SW2026.parents[2]
sys.path[:0] = [str(REPO), str(REPO / 'src'), str(SW2026)]

from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


EVIDENCE = {
    'ConcentricDisplayAuthoring04.json': '1b008f32adcaaadd61a1d072ae3a012f8136418a5a6a9fe51b8fc65c2228587a',
    'ConcentricDisplaySyncNative01.json': 'e14c77749cd68ed554bbbdbf014d1360df9fa58a1524976329d93976b48e5d71',
}


def need(value, why):
    if not value:
        raise ValueError(why)


def digest(value):
    return sha256(value).hexdigest()


def bind_evidence():
    records = []
    for name, expected in EVIDENCE.items():
        payload = (REPO / 're/solidworks/measurements/2026' / name).read_bytes()
        need(digest(payload) == expected, 'disclosed native visibility evidence changed')
        records.append(json.loads(payload))
    model, native = records
    index = model['archives']['after']['xml']
    authored = model['native_observations']['author_named_visibility']
    refs = [row['feature_id'] for row in index['occurrences']]
    state_ids = [index['states'][name]['xml_id'] for name in authored]
    cold = native['paired_cold_opens']['Synchronized']
    need(model['audit_passed'] and index['byte_identity'] and native['controls_healthy']
         and cold['open_error'] == cold['open_warning'] == 0 and cold['named_and_live_visibility_match']
         and cold['native_default_and_mixed_visibility'] == authored, 'actual typed and cold-authored state evidence differs')
    need(index['configuration'] == [1, 0, 'Default'] and index['state']['members'] == [[ref, 'Yes'] for ref in refs]
         and refs != [row['xml_id'] for row in index['occurrences']]
         and sorted(state_ids) == list(range(index['state']['list_id'] + 1, index['actual_xml_object_count'] + 1)),
         'native display occurrence and object ID namespaces are not independently owned')
    for name, vector in authored.items():
        actual = index['states'][name]
        need(actual['visibility'] == vector and actual['show_tokens'] == [('Yes' if visible else 'No') for visible in vector],
             'native XML polarity does not match the persisted native authored vector')
    return {'pins': EVIDENCE, 'native_default_and_mixed_rows': len(authored), 'native_owner_ids_distinct': True,
            'synchronized_open_status': [cold['open_error'], cold['open_warning']], 'stream_precedence_measured': False}


def source_hashes():
    sources = [Path(__file__), Path(__file__).with_name('MakeDisplayTree.py')]
    adapter = REPO / 'src/convert/adapters/solidworks'
    sources.extend(adapter / path for path in ('Archive/Construction/Assembly/MakeAssembly.py',
                   'Archive/Construction/Assembly/EmitAsmStreams.py', 'Archive/Construction/Assembly/Xml/MakeAsmTree.py',
                   'Assembly/Display/ReadDisplayXml.py', 'Assembly/Display/CheckDisplay.py'))
    return {str(path.relative_to(REPO)): digest(path.read_bytes()) for path in sources}


def compose(audit):
    from SdkAssemblySettings import assembly_settings, mate_settings, occurrence_settings
    from SdkBlindPartSettings import settings
    from tests.Convert.Solidworks.Research.Construction.Assembly.MakeAsmCase import MakeAsmCase
    from convert.adapters.solidworks.Archive.Construction.Assembly.MakeAssembly import MakeAssembly
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
    from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm, XmlRoot
    from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
    from convert.adapters.solidworks.Container.Format import KComponentTreeStream
    import interchange.document.Validation.DocumentAssemblyValidate
    import interchange.document.Validation.DocumentFeatureValidate
    import interchange.document.Validation.DocumentReferenceValidate
    from interchange.serialization.Deserialize import FromData
    from para.concentric.MakeDisplayTree import DisplayListIntent, DisplayStateIntent, PREFIX, frame_tree, make_display_tree

    for encoding in ('utf-16-le', 'utf-16-be', 'cp1252', 'utf-8', 'latin-1'):
        lookup(encoding)
    audit.BeginBuild()

    def candidate(variant):
        request = MakeAsmCase('coincident', 'z', variant)
        child = MakeBlindPart(FromData(request['child']['document']), settings(request['child']['settings']))
        config = 'Fixture review' if variant else 'Shop layout'
        inputs = assembly_settings(request['assembly'] | {'configuration_name': config})
        if variant:
            inputs = replace(inputs, SystemValue=replace(inputs.SystemValue, HasEmptyExplodedView=True))
        return MakeAssembly(child, inputs, occurrence_settings(request['occurrences']), mate_settings(request['mate']))

    def arguments(assembly):
        return assembly.StateValue, assembly.HeaderValue, assembly.ChildValue, assembly.OccurrenceValues

    def inspect(assembly, intent):
        original = assembly.StreamsValue
        baseline = original[KComponentTreeStream]
        need(make_display_tree(*arguments(assembly)) == baseline, 'the no-intent path changed the shared generated XML')
        tree_data = make_display_tree(*arguments(assembly), intent)
        tree = XmlRoot(tree_data)
        config, = tree.iter(f'{PREFIX}swConfiguration')
        listing, = config
        original_count = int(XmlRoot(baseline).attrib['swObjCount'])
        published_count = int(tree.attrib['swObjCount'])
        occurrence_xml_ids = tuple(int(row.attrib['id']) for row in tree.iter(f'{PREFIX}swReference'))
        members = tuple(int(value) for value in listing.attrib['swCompNameList'].split(',')[:-1])
        real_refs = tuple(row.FieldsValue['f08'] for row in assembly.OccurrenceValues)
        need(members == real_refs and config.attrib['swID'] == str(intent.configuration_id), 'generated display XML lost actual ownership')
        records = [(int(row.attrib['id']), row.attrib['swDisplayStateName'], row.attrib['swShowState']) for row in listing]
        need(published_count == original_count + 1 + len(records)
             and int(listing.attrib['id']) == original_count + 1
             and [record[0] for record in records] == list(range(original_count + 2, published_count + 1))
             and sorted(int(row.attrib['id']) for row in tree.iter() if 'id' in row.attrib) == list(range(1, published_count + 1)),
             'the emitted list and leaves do not extend the actual generated object count')
        combined = BuildSldprt(dict(original) | {KComponentTreeStream: tree_data}, FormatVersion=4)
        archive = SldprtArchive.from_bytes(combined)
        need(archive.streams.keys() == original.keys() and all(archive.require(name) == value for name, value in original.items()
             if name != KComponentTreeStream) and archive.get('ThirdPtyStore/VisualStates') is None,
             'display composition changed another archive stream')
        opened = DecodeNativeAsm(archive)
        readback = [(row.object_id, row.name, dict(row.attributes)['swShowState']) for row in opened.display_states]
        need(readback == records and tuple(row.feature_id for row in opened.occurrences) == real_refs
             and (opened.display_owner is not None) == (len(intent.states) == 1), 'normal assembly read changed the display graph or admission')
        config.remove(listing)
        tree.set('swObjCount', str(original_count))
        need(frame_tree(tree) == baseline, 'adding display content rewrote another XML owner')
        return {'configuration_id': intent.configuration_id, 'configuration_name': config.attrib['swName'],
                'occurrence_feature_ids': real_refs, 'occurrence_xml_ids': occurrence_xml_ids,
                'xml_object_counts': [original_count, published_count], 'list_xml_id': int(listing.attrib['id']), 'display_rows': records,
                'bytes': [len(baseline), len(tree_data)], 'sha256': [digest(baseline), digest(tree_data)],
                'existing_typed_reader_admitted': opened.display_owner is not None, 'changed_logical_streams': [KComponentTreeStream]}

    result = []
    ordinary = None
    for variant in (False, True):
        assembly = candidate(variant)
        repeat = candidate(variant)
        need(assembly.BytesValue == repeat.BytesValue and assembly.ChildValue.BytesValue == repeat.ChildValue.BytesValue,
             'fresh independent neutral builds differ')
        first, second = (row.FieldsValue['f08'] for row in assembly.OccurrenceValues)
        config = assembly.StateValue.CurrentConfig.FieldsValue['f08']
        states = (DisplayStateIntent('Inspection overview', ((second, True), (first, True))),
                  DisplayStateIntent('Hinge & enclosure', ((second, False), (first, True))),
                  DisplayStateIntent('Drive end Ω', ((first, False), (second, True))))
        intent = DisplayListIntent(config, states)
        single = inspect(assembly, DisplayListIntent(config, states[:1]))
        mixed = inspect(assembly, intent)
        need(mixed['sha256'][1] == digest(make_display_tree(*arguments(repeat), intent)), 'fresh mixed composition differs')
        need([row[2] for row in mixed['display_rows']] == ['Yes,Yes,', 'Yes,No,', 'No,Yes,'], 'authored keyed rows followed insertion order rather than the actual tree')
        result.extend((single, mixed))
        if not variant:
            ordinary = assembly, intent
    need(result[0]['occurrence_feature_ids'] != result[2]['occurrence_feature_ids'], 'the actual allocator did not shift occurrence IDs')
    assembly, intent = ordinary
    first, second = (row.FieldsValue['f08'] for row in assembly.OccurrenceValues)
    names = intent.states
    args = arguments(assembly)
    object_ids = result[0]['occurrence_xml_ids']
    negatives = {
        'foreign_configuration': (*args, replace(intent, configuration_id=intent.configuration_id + 1)),
        'reversed_native_references': (*args[:3], tuple(reversed(args[3])), intent),
        'missing_occurrence': (*args, replace(intent, states=(replace(names[0], visibility=((first, True),)),))),
        'duplicate_occurrence': (*args, replace(intent, states=(replace(names[0], visibility=((first, True), (first, True))),))),
        'xml_ids_as_members': (*args, replace(intent, states=(replace(names[0], visibility=tuple((key, True) for key in object_ids)),))),
        'conflicting_default': (*args, replace(intent, states=(replace(names[0], visibility=((first, True), (second, False))),))),
        'duplicate_state_name': (*args, replace(intent, states=(names[0], replace(names[1], name=names[0].name)))),
    }
    refusals = {}
    for label, options in negatives.items():
        try:
            make_display_tree(*options)
        except ValueError as error:
            refusals[label] = str(error)
        else:
            raise ValueError('display composer admitted an ambiguous request: ' + label)
    need(not audit.DeniedReads, 'guarded construction touched runtime files')
    return result, refusals


def main():
    native = bind_evidence()
    sources = source_hashes()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
    audit = BuildAudit(REPO / 're/tooling/sw2026/serial/defs')
    sys.addaudithook(audit.InspectEvent)
    cases, refusals = compose(audit)
    print(json.dumps({'schema': 'kit.sw2026.concentric-display-tree-composition.v1', 'checkout_revision': revision,
                      'sources_sha256': sources, 'authored_evidence': native, 'compositions': cases, 'refusals': refusals,
                      'independent_neutral_parents': 2, 'runtime_input_file_reads': len(audit.DeniedReads),
                      'native_processes_started': 0, 'heldout_inputs_read': 0, 'cad_files_written': 0,
                      'native_acceptance': False, 'public_writer_qualified': False, 'passed': True},
                     indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
