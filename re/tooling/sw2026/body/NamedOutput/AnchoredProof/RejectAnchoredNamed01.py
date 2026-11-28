from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from json import dumps, load
from pathlib import Path
import sys


def main():
    parser = ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--variant', required=True)
    args = parser.parse_args()
    case = load(sys.stdin)
    sys.path[:0] = [str(args.sdk/'src'), str(Path(__file__).resolve().parent/'Harness01')]
    from MakeAnchoredRequest import request
    from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import AnchorPartInput
    from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeAnchorBase import MakeAnchorBase
    from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeAnchorNamed import MakeAnchorNamed
    from convert.adapters.solidworks.Archive.Construction.BodyNames.NameOutputMut import NameOutputMut
    from convert.adapters.solidworks.Archive.Construction.Part.MakeBlindPart import MakeBlindPart
    from interchange.Enums.EnumGeometry import GeometryKind
    from interchange.geometry.Models.GeometryCurves import CircleGeometry
    from interchange.geometry.Models.VectorPlane import PlaneVector
    from interchange.serialization.EncodeData import ToData
    for name in ('ascii', 'utf-8', 'utf-16-le', 'utf-16-be', 'latin-1'):
        lookup(name)
    for name in ('interchange.document.Models.DocumentProvenance', 'interchange.document.Behavior.DocumentIo',
                 'interchange.brep.Validation.BrepValidate', 'interchange.document.Validation.DocumentAssemblyValidate',
                 'interchange.document.Validation.DocumentFeatureValidate', 'interchange.document.Validation.DocumentReferenceValidate'):
        import_module(name)
    document, settings, dimensions = request(case)
    anchor = AnchorPartInput(case['anchor_kind'], dimensions)
    body, = document.bodies
    feature, = document.feature_timeline
    sketch, = document.sketches
    variant = args.variant
    graph_variant = variant.startswith('Graph')
    if variant == 'EmptyName':
        document = replace(document, bodies=(replace(body, name=''),))
    elif variant == 'OuterWhitespace':
        document = replace(document, bodies=(replace(body, name=' '+body.name),))
    elif variant == 'OverlongName':
        document = replace(document, bodies=(replace(body, name='A'*256),))
    elif variant == 'WideUnitOverflow':
        document = replace(document, bodies=(replace(body, name='𐐷'*128),))
    elif variant == 'UnpairedSurrogate':
        document = replace(document, bodies=(replace(body, name='invalid\ud800name'),))
    elif variant == 'EmbeddedNull':
        document = replace(document, bodies=(replace(body, name='invalid\x00name'),))
    elif variant == 'ControlCharacter':
        document = replace(document, bodies=(replace(body, name='invalid\nname'),))
    elif variant == 'UnownedBody':
        document = replace(document, bodies=(replace(body, final_feature_id=sketch.id),))
    elif variant == 'SecondBody':
        document = replace(document, bodies=(body, replace(body, id='body/another')))
    elif variant == 'BodyAttributes':
        document = replace(document, bodies=(replace(body, attributes={'unrepresented':'authored'}),))
    elif variant == 'ExtraMetadata':
        document = replace(document, metadata={**document.metadata, 'unrepresented':'authored'})
    elif variant == 'ExtraFeature':
        document = replace(document, feature_timeline=(feature, replace(feature, id='feature/extra', order=1)))
    elif variant == 'ReversedEnd':
        document = replace(document, feature_timeline=(replace(feature, definition=replace(feature.definition, reversed=True)),))
    elif variant == 'CircleProfile':
        entity = replace(sketch.entities[0], kind=GeometryKind.KCircle, geometry=CircleGeometry(PlaneVector(0,0),1))
        document = replace(document, sketches=(replace(sketch, entities=(entity,*sketch.entities[1:])),))
    elif variant == 'WrongDriverOwner':
        document = replace(document, parameters=(replace(document.parameters[0], owner_id=feature.id),*document.parameters[1:]))
    elif variant == 'DuplicateDriverName':
        document = replace(document, parameters=(document.parameters[0],replace(document.parameters[1],name=document.parameters[0].name),document.parameters[2]))
    elif variant == 'NullAnchorInput':
        anchor = None
    elif variant == 'NullDimensions':
        anchor = replace(anchor, DimensionsValue=None)
    elif variant == 'InvalidAnchorKind':
        anchor = replace(anchor, KindValue='guessed')
    elif variant == 'WrongAnchorFamily':
        anchor = replace(anchor, KindValue='center' if case['anchor_kind']=='corner' else 'corner')
    elif variant == 'DroppedAxis':
        document = replace(document, sketches=(replace(sketch, constraints=sketch.constraints[1:]),))
    elif variant == 'SuppressedAxis':
        document = replace(document, sketches=(replace(sketch, constraints=(replace(sketch.constraints[0],suppressed=True),*sketch.constraints[1:])),))
    elif variant == 'WrongAnchorPlacement':
        entities = tuple(replace(entity,geometry=replace(entity.geometry,
            start=PlaneVector(entity.geometry.start.x+2.13,entity.geometry.start.y-1.79),
            end=PlaneVector(entity.geometry.end.x+2.13,entity.geometry.end.y-1.79))) for entity in sketch.entities)
        document = replace(document,sketches=(replace(sketch,entities=entities),))
    elif variant == 'ExtraConstruction':
        document = replace(document,sketches=(replace(sketch,entities=(*sketch.entities,replace(sketch.entities[0],id='unrepresented/construction',construction=True))),))
    elif not graph_variant:
        raise ValueError('unknown named negative variant')
    source_before = sha256(dumps(ToData(document),ensure_ascii=True,sort_keys=True).encode()).hexdigest()
    state = {'enabled': False, 'attempts': []}

    def audit(event, arguments):
        if state['enabled'] and (event == 'open' or event.startswith(('subprocess.', 'socket.'))
            or event in ('os.system', 'os.fork', 'os.posix_spawn', 'ctypes.dlopen')):
            state['attempts'].append({'event':event,'arguments':repr(arguments[:2])})
            raise RuntimeError('negative construction attempted runtime external access')

    sys.addaudithook(audit)
    error = None
    graph_before = graph_after = None
    state['enabled'] = True
    try:
        if graph_variant:
            base = replace(document, bodies=(replace(document.bodies[0],name=feature.name),))
            candidate = MakeAnchorBase(base, settings, anchor)
            manager = candidate.SystemValue.RootValue.FieldsValue['fd88']
            boss = candidate.BossValue.FeatureValue
            if variant == 'GraphRepeatedOutput':
                NameOutputMut(candidate, body.name)
            elif variant == 'GraphOldManager':
                manager['fa8'] = 1
            elif variant == 'GraphCounterOverflow':
                manager['f260'] = (1 << 31)-1
            elif variant == 'GraphExistingOutput':
                boss.FieldsValue['has_f528'] = 1
            elif variant == 'GraphGhostBody':
                candidate.SystemValue.RootValue.FieldsValue['fd90']['n'] = 1
            elif variant == 'GraphPresentPartition':
                candidate = replace(candidate, StreamsValue={**candidate.StreamsValue,'Contents/Config-0-Partition':b''})
            elif variant == 'GraphForeignHistory':
                candidate = replace(candidate, ResolvedValue=replace(candidate.ResolvedValue,RootsValue=tuple(reversed(candidate.ResolvedValue.RootsValue))))
            else:
                raise ValueError('unknown graph negative variant')
            graph_before = sha256(repr((manager,boss.FieldsValue)).encode()).hexdigest()
            try:
                NameOutputMut(candidate, 'Rejected Replacement')
            finally:
                graph_after = sha256(repr((manager,boss.FieldsValue)).encode()).hexdigest()
        else:
            MakeAnchorNamed(document, settings, anchor)
    except (TypeError, ValueError) as value:
        error = {'class':type(value).__name__,'message':str(value)}
    finally:
        state['enabled'] = False
    source_after = sha256(dumps(ToData(document),ensure_ascii=True,sort_keys=True).encode()).hexdigest()
    source_root = (args.sdk/'src').resolve()
    outside, research = [], []
    for name, module in tuple(sys.modules.items()):
        filename = getattr(module,'__file__',None)
        if name.startswith(('convert','interchange')) and filename and not Path(filename).resolve().is_relative_to(source_root):
            outside.append(name)
        if filename and '/re/tooling/' in str(filename):
            research.append(name)
    passed = error is not None and source_before == source_after and not state['attempts'] and not outside and not research
    passed = passed and (not graph_variant or graph_before is not None and graph_before == graph_after)
    print(dumps({'schema':'kit.sw2026.typed-anchored-named-output-rejection.v1','variant':variant,'passed':passed,
        'error':error,'neutral_input_unchanged':source_before==source_after,
        'graph_unchanged_on_rejection':graph_before==graph_after,'runtime_access_attempts':state['attempts'],
        'unexpected_sdk_origins':outside,'research_runtime_imports':research,'heldout_inputs_read':0,
        'writer_output':False},ensure_ascii=True,sort_keys=True))
    raise SystemExit(0 if passed else 3)


if __name__ == '__main__':
    main()
