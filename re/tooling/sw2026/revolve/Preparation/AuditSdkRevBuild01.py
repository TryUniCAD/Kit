import argparse
import base64
import codecs
from dataclasses import replace
import hashlib
import importlib
from io import BytesIO
import json
from math import cos, isclose, sin, tau
from pathlib import Path
import sys
from xml.etree.ElementTree import fromstring


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdk', type=Path, required=True)
    args = parser.parse_args()
    row = json.loads(sys.stdin.read())
    sys.path.insert(0, str(args.sdk / 'src'))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from convert.adapters.solidworks.Archive.Construction.Revolves.Part.MakeRevPart import MakeRevPart as make_candidate
    from MakeRevolveRequest01 import make_request, native_model
    from convert import open_document, write_document
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
    from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
    from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHdrMut import ReadMgrHdrMut
    from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHdrMut import WriteMgrHdrMut
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Construction.Metadata.FrameKeywords import FrameKeywords
    from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
    from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
    from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
    from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners
    from convert.Geometry.Revolve.FullPolySweep import BuildFullSweep
    from convert.Geometry.Revolve.PolygonSweep import BuildPolySweep
    from convert.Geometry.Revolve.SweepMetrics import MeasureInterval
    from interchange.document.Behavior.DocumentIo import ToJson, FromJson
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.Features.FeatureAngleRev import AngularRevolve
    from interchange.geometry.Models.VectorSpace import SpaceVector
    from interchange.Records.RecordParameter import Expression, ParameterValue
    from interchange.Enums.EnumValues import ValueKind
    for name in ('ascii', 'utf-8', 'utf-8-sig', 'utf-16-le', 'utf-16-be', 'latin-1'):
        codecs.lookup(name)
    for name in ('interchange.document.Models.DocumentProvenance',
        'interchange.brep.Validation.BrepValidate',
        'interchange.document.Validation.DocumentAssemblyValidate',
        'interchange.document.Validation.DocumentFeatureValidate',
        'interchange.document.Validation.DocumentReferenceValidate'):
        importlib.import_module(name)
    audit_state = {'enabled': False, 'attempts': []}
    def audit(event, arguments):
        if audit_state['enabled'] and (event == 'open' or event.startswith(('subprocess.', 'socket.'))
            or event in ('os.system', 'os.fork', 'os.posix_spawn', 'ctypes.dlopen')):
            audit_state['attempts'].append(event)
            raise RuntimeError('revolve construction attempted forbidden runtime external access')
    sys.addaudithook(audit)
    result = {'schema': 'kit.sw2026.sdk-revolve-build-worker.v1', 'passed': False,
        'heldout_inputs_read': 0, 'native_processes': 0}
    audit_state['enabled'] = True
    try:
        document, settings = make_request(row['spec'])
        mutation = row.get('mutation')
        if mutation:
            feature, sketch, parameter, selection = (document.feature_timeline[0], document.sketches[0],
                document.parameters[0], document.selections[0])
            if mutation == 'expression':
                document = replace(document, parameters=(replace(parameter, expression=Expression('pi / 2')),))
            elif mutation in ('negative_angle', 'excess_angle', 'tiny_angle', 'nonfinite_angle'):
                angle = {'negative_angle': -1.0, 'excess_angle': 7.0, 'tiny_angle': 1e-12,
                    'nonfinite_angle': float('nan')}[mutation]
                document = replace(document, parameters=(replace(parameter, value=ParameterValue(angle, ValueKind.KAngle, 'rad')),))
            elif mutation == 'two_sided':
                document = replace(document, feature_timeline=(replace(feature,
                    definition=replace(feature.definition, SideMode='two_sided', AgainstParameterId='parameter/other')),))
            elif mutation == 'axis_in_contour':
                path = (selection.path[0], replace(selection.path[1], entity_id=sketch.entities[0].id))
                document = replace(document, selections=(replace(selection, path=path),))
            elif mutation == 'missing_axis_relation':
                document = replace(document, sketches=(replace(sketch, constraints=sketch.constraints[:-1]),))
            elif mutation == 'fixed_axis':
                entities = tuple(replace(entity, fixed=True) if entity.construction else entity for entity in sketch.entities)
                document = replace(document, sketches=(replace(sketch, entities=entities),))
            elif mutation == 'extra_metadata':
                document = replace(document, metadata={**document.metadata, 'unowned': True})
            elif mutation == 'body_name':
                document = replace(document, bodies=(replace(document.bodies[0], name='unmodeled output label'),))
            elif mutation == 'support_origin':
                plane = document.support_planes[0]
                document = replace(document, support_planes=(replace(plane,
                    transform=replace(plane.transform, origin=SpaceVector(1.0, 0.0, 0.0))),))
            elif mutation == 'wrong_relation':
                relation = replace(sketch.constraints[0], kind='vertical')
                document = replace(document, sketches=(replace(sketch, constraints=(relation, *sketch.constraints[1:])),))
            elif mutation == 'axis_relation':
                relation = replace(sketch.constraints[0], references=(replace(sketch.constraints[0].references[0], entity_id=sketch.entities[-1].id),))
                document = replace(document, sketches=(replace(sketch, constraints=(relation, *sketch.constraints[1:])),))
            elif mutation == 'downward_axis':
                axis = sketch.entities[-1]
                entity = replace(axis, geometry=replace(axis.geometry, start=axis.geometry.end, end=axis.geometry.start))
                document = replace(document, sketches=(replace(sketch, entities=(*sketch.entities[:-1], entity)),))
            elif mutation == 'axis_origin':
                document = replace(document, feature_timeline=(replace(feature,
                    definition=replace(feature.definition, AxisOrigin=SpaceVector(0.0, 0.0, 0.0))),))
            elif mutation == 'additional_configuration':
                document = replace(document, configurations=(*document.configurations,
                    replace(document.configurations[0], id='config/other', name='Other', active=False)))
            elif mutation == 'alternate_unit':
                document = replace(document, parameters=(replace(parameter, value=ParameterValue(90.0, ValueKind.KAngle, 'degree')),))
            else:
                raise ValueError('unregistered negative fixture')
            try:
                make_candidate(document, settings)
            except (ValueError, TypeError, KeyError) as error:
                result.update(passed=True, rejected=True, error_class=type(error).__name__, error_message=str(error))
            else:
                raise ValueError('unsupported neutral revolve emitted an output')
        else:
            public_target = BytesIO()
            try:
                write_document(document, public_target, destination_format='solidworks.sldprt', allow_carrier=False)
            except NotFoundError:
                require(not public_target.getvalue(), 'public registration published unsupported revolve bytes')
            else:
                raise ValueError('private revolve construction unexpectedly enabled public registration')
            initial_json = ToJson(document)
            candidate = make_candidate(document, settings)
            second = make_candidate(document, settings)
            require(ToJson(document) == initial_json, 'constructor mutated the caller neutral document')
            require(candidate.BytesValue == second.BytesValue and candidate.SystemValue.RootValue is not second.SystemValue.RootValue,
                'revolve deterministic builds did not allocate independent graphs')
            require(not any('partition' in name.casefold() or 'delta' in name.casefold() for name in candidate.StreamsValue),
                'revolve output unexpectedly transmits geometry cache state')
            archive = SldprtArchive.from_bytes(candidate.BytesValue)
            require(dict(archive.streams) == candidate.StreamsValue, 'container readback does not retain generated logical streams')
            link = ReadNativeLink(archive, 0)
            owner, = ReadRevOwners(link)
            require(owner.AngleValue.RadiansValue == candidate.PlanValue.AngleValue
                and owner.IsReverse == candidate.PlanValue.IsReverse
                and owner.AxisValue.MarkValue == candidate.ProfileValue.GeometryValue.LineValues[-1].FieldsValue['f08']
                and owner.AxisValue.SelectionValue.FieldsValue['ff0']['f08'] == 2592000,
                'wire readback lost angular direction permanent mark or actual profile identity')
            require(owner.AxisValue.IndexValue == 4 and len(owner.ProfileGraph.LoopValue.LinesValue) == 4
                and len(owner.ProfileGraph.AxisRules) == 4 and len(owner.ProfileGraph.AxisPoints) == 2,
                'wire readback changes selected axis or authored solver geometry')
            decoded = link.ConfigValue
            config_bytes, config = WriteConfigMut(decoded.RootValue, 19000, decoded.HeaderValue)
            resolved_bytes, resolved = WriteResolMut(link.ResolvedValue.RootsValue,
                link.ResolvedValue.ExtraFields, 19000, config.MapValue, link.ResolvedValue.ContextValue)
            require(config_bytes == archive.require('Contents/Config-0')
                and resolved_bytes == archive.require('Contents/Config-0-ResolvedFeatures'),
                'linked typed Config and Resolved re-emission differs')
            stream_checks = {'Contents/Config-0': True, 'Contents/Config-0-ResolvedFeatures': True}
            for name in ('Header2', 'Contents/Config-0-ModelHeader'):
                stream_checks[name] = WriteHeadGraph(ReadHeaderGraph(archive.require(name), 19000), 19000) == archive.require(name)
            stream_checks['Contents/CMgr'] = WriteCmgrMut(ReadCmgrMut(archive.require('Contents/CMgr'), 19000).RootValue, 19000) == archive.require('Contents/CMgr')
            stream_checks['Contents/CMgrHdr2'] = WriteMgrHdrMut(ReadMgrHdrMut(archive.require('Contents/CMgrHdr2'), 19000).RootValue, 19000)[0] == archive.require('Contents/CMgrHdr2')
            stream_checks['Contents/Definition'] = WriteModelDef(ReadModelDef(archive.require('Contents/Definition'), 19000).GraphValue).OutputValue == archive.require('Contents/Definition')
            for name in ('_MO_VERSION_19000/Biography', '_MO_VERSION_19000/History'):
                stream_checks[name] = WriteHistMut(ReadHistMut(archive.require(name), 19000).RootValue, 19000)[0] == archive.require(name)
            name = 'swXmlContents/KeyWords'
            stream_checks[name] = FrameKeywords(fromstring(archive.require(name)[1:]), True) == archive.require(name)
            require(len(stream_checks) == 10 and all(stream_checks.values()), 'a generated logical stream failed typed byte identity')
            for report in (config.ReportValue, resolved.ReportValue):
                require(report['completed'] and not report['missing_schemas'] and not report['provisional_schemas'],
                    'generated graph reaches an unproved archive owner')
            public = open_document(candidate.BytesValue, source_format='solidworks.sldprt', strict=True,
                include_brep=False, include_tessellation=False)
            public.assert_valid()
            require(ToJson(FromJson(CadDocument, ToJson(public))) == ToJson(public), 'public neutral JSON roundtrip differs')
            step, = (value for value in public.feature_timeline if value.name == candidate.PlanValue.FeatureName)
            require(type(step.definition) is AngularRevolve and public.metadata['solidworks.typed_revolve_semantics']['status'] == 'projected',
                'normal SDK readback does not expose the actual linked revolve')
            theta = owner.AngleValue.RadiansValue
            axis_x = candidate.PlanValue.AxisStart[0]
            xy = [point.PositionValue for point in owner.ProfileGraph.LoopValue.PointsValue.values()]
            ri, ro = min(point[0] for point in xy) * .001 - axis_x, max(point[0] for point in xy) * .001 - axis_x
            low, high = min(point[1] for point in xy) * .001, max(point[1] for point in xy) * .001
            delta = ro * ro - ri * ri
            volume = (high - low) * theta * delta / 2
            area = theta * ((high - low) * (ri + ro) + delta) + (0 if theta == tau else 2 * (high-low) * (ro-ri))
            factor = 2 * (ro**3 - ri**3) / (3 * theta * delta)
            center = [axis_x + factor*sin(theta), (low+high)/2,
                (1 if owner.IsReverse else -1)*factor*(1-cos(theta))]
            origin = SpaceVector(axis_x * 1000, 0.0, 0.0)
            direction = SpaceVector(0.0, -1.0 if owner.IsReverse else 1.0, 0.0)
            radial = SpaceVector(1.0, 0.0, 0.0)
            meridian = tuple(((point[0] - axis_x)*1000, point[1]*1000*(-1 if owner.IsReverse else 1)) for point in candidate.PlanValue.VerticesValue)
            measured_volume, measured_area, bounds = MeasureInterval(meridian, origin, direction, radial, 0.0, theta)
            require(isclose(measured_volume * 1e-9, volume, rel_tol=1e-12, abs_tol=1e-16)
                and isclose(measured_area * 1e-6, area, rel_tol=1e-12, abs_tol=1e-16),
                'independent triangulated meridian geometry disagrees with annular-sector mathematics')
            brep = (BuildFullSweep('analytic/revolve', meridian, origin, direction, radial) if theta == tau
                else BuildPolySweep('analytic/revolve', meridian, origin, direction, radial, 0.0, theta))
            require(not brep.validate(frozenset(('analytic/revolve',))), 'independent analytic B-rep is not a closed validated solid')
            require(len(brep.bodies) == 1 and len(brep.faces) == (4 if theta == tau else 6), 'independent revolve topology differs')
            result.update(passed=True, rejected=False, blob=base64.b64encode(candidate.BytesValue).decode(),
                sha256=hashlib.sha256(candidate.BytesValue).hexdigest(), bytes=len(candidate.BytesValue),
                com_request=native_model(row['spec']), streams={name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                    'roundtrip': stream_checks[name]} for name, data in candidate.StreamsValue.items()},
                graph={'resolved_roots':len(resolved.RootsValue), 'model_id':candidate.SystemValue.RootValue.FieldsValue['f08'],
                    'profile_id':candidate.ProfileValue.ProfileValue.FieldsValue['f08'], 'feature_id':candidate.FeatureValue.FieldsValue['f08'],
                    'angle_dimension_id':candidate.AngleValue.DimensionValue.FieldsValue['f50'],
                    'selected_axis_index':owner.AxisValue.IndexValue, 'axis_mark':owner.AxisValue.MarkValue,
                    'axis_profile_time':2592000, 'point_rows':6, 'line_rows':5, 'axis_relations':0,
                    'contour_relations':4, 'angle_rad':theta, 'reverse':owner.IsReverse},
                geometry={'volume_m3':volume, 'area_m2':area, 'com_m':center, 'faces':len(brep.faces),
                    'edges':len(brep.edges), 'vertices':len(brep.vertices), 'brep_validated':True,
                    'independently_computed_not_transmitted':True},
                native_qualified=False, heldout_qualified=False, public_registration_enabled=False)
    finally:
        audit_state['enabled'] = False
    result['runtime_external_attempts'] = audit_state['attempts']
    result['sdk_modules'] = sorted({module.__file__ for name, module in sys.modules.items()
        if (name == 'convert' or name.startswith(('convert.', 'interchange.'))) and getattr(module, '__file__', None)})
    require(not audit_state['attempts'], 'runtime access guard recorded forbidden access')
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
