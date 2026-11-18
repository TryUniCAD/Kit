from dataclasses import replace

from convert.adapters.solidworks.Archive.Construction.Nodes.InitConceptMut import InitConceptMut
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import EmitPartStreams
from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Container.Container import BuildSldprt


def construct(document, settings):
    if len(document.bodies) != 1 or len(document.feature_timeline) != 1:
        raise ValueError('cold named experiment requires one actual body and creating feature')
    body, = document.bodies
    feature, = document.feature_timeline
    label = body.name
    if (type(label) is not str or not 1 <= len(label) <= 255
            or label != label.strip() or any(not 32 <= ord(value) < 127 for value in label)
            or label == feature.name):
        raise ValueError('cold experiment needs a distinct explicit printable ASCII body label')
    base_document = replace(document, bodies=(replace(body, name=feature.name),))
    candidate = MakeBlindPart(base_document, settings)
    named = attach(candidate, settings, label)
    return named, candidate.BytesValue, candidate.StreamsValue


def attach(candidate, settings, label):
    model = candidate.SystemValue.RootValue
    manager = model.FieldsValue['fd88']
    boss = candidate.BossValue.FeatureValue
    if (type(manager) is not dict or manager['n6c'] != 0 or manager['atoms']
            or manager['fa8'] != 0 or type(manager['f260']) is not int
            or candidate.BossValue.FeatureValue is not candidate.ResolvedValue.RootsValue[-1]
            or boss.FieldsValue['has_f528'] != 0 or boss.FieldsValue['has_f530'] != 0
            or boss.FieldsValue['f538'] is not None or boss.FieldsValue['n494'] != 0
            or boss.FieldsValue['f498']
            or any('Partition' in name for name in candidate.StreamsValue)):
        raise ValueError('cold name construction requires a fresh no-cache ordinary output graph')
    atom_id = manager['f260'] + 1
    feature_id = boss.FieldsValue['f08']
    if not 0 < atom_id < (1 << 31) or type(feature_id) is not int or feature_id <= 0:
        raise ValueError('cold atom and feature identifiers exceed their independent domains')
    atom = ArchiveNode(RuntimeClass('moAtom_c', 1), {})
    InitConceptMut(atom, label)
    atom.FieldsValue.update({'f140': atom_id, 'f144': 0,
        'f130': feature_id, 'f12c': feature_id, 'f158': 0, 'body_kind': 0,
        'f170': 0, 'f18c': 0, 'f198': -1, 'f180': 0, 'f188': 0,
        'f1b0': 0, 'f19c': 6})
    manager.update(f260=atom_id, n6c=1, atoms=[{'o': atom}])
    boss.FieldsValue.update(has_f528=1, f528={'n': 1, 'items': [{'o': atom}]},
                            n494=1, f498=[{'v': atom_id}])
    streams, config, resolved = EmitPartStreams(candidate.SystemValue,
        candidate.ResolvedValue.RootsValue,
        (candidate.HeaderValue, candidate.TopHeader, candidate.ManagerHeader),
        candidate.DefinitionValue, settings, candidate.PlanValue)
    if any('Partition' in name for name in streams):
        raise ValueError('cold named experiment must not transmit any kernel cache')
    return replace(candidate, StreamsValue=streams, ConfigValue=config,
                   ResolvedValue=resolved, BytesValue=BuildSldprt(streams, FormatVersion=4))
