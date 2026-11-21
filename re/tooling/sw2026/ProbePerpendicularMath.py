import argparse
from base64 import b64decode
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
import sys


def doubles(values):
    return [value.hex() for value in values]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    sys.path.insert(0, str(root / 'src'))
    from convert.adapters.solidworks.Archive.Construction.Views.MakeStdViews import MakeStdViews
    from convert.adapters.solidworks.Archive.Construction.Views.MultiplyQuat import MultiplyQuat
    from convert.adapters.solidworks.Archive.Construction.Views.ViewMatrix import ViewMatrix
    from convert.adapters.solidworks.Archive.Construction.Views.ViewPlans import KViewPlans
    from convert.adapters.solidworks.Archive.Construction.Views.ViewRotation import ViewRotation
    from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    worker = json.loads(args.worker.read_bytes())
    archive = SldprtArchive.from_bytes(b64decode(worker['assembly']['blob'], validate=True))
    link = ReadNativeLink(archive, 0)
    graph = ReadMatesMut(archive.require('Contents/Config-0-MatesList'), link.ResolvedValue)
    wrapper = graph.RootsValue[0].FieldsValue['f410'][0]['o']
    transform, origin = wrapper.FieldsValue['f100'], wrapper.FieldsValue['fd0']
    matrix = transform['f08']
    axis = [matrix['m' + str(index)] for index in (1, 4, 7)]
    products = [-origin[key] * value for key, value in zip(('x', 'y', 'z'), axis, strict=True)]
    sequential = 0.0
    for value in products:
        sequential += value
    projection = {'field': 'moPlaneRef_w.f100.f60', 'world_origin': origin, 'basis_v_hex': doubles(axis),
                  'product_hex': doubles(products), 'builtin_sum_hex': sum(products).hex(),
                  'explicit_sequential_hex': sequential.hex(), 'fsum_hex': math.fsum(products).hex(),
                  'stored_hex': transform['f60'].hex()}
    actual = MakeStdViews(1)
    views = []
    for index in (3, 4, 5, 6):
        name, steps = KViewPlans[index]
        quaternion = (0.0, 0.0, 0.0, 1.0)
        rotations = []
        for axis_name, angle in steps:
            step = ViewRotation(axis_name, angle)
            rotations.append({'axis': axis_name, 'angle_hex': angle.hex(), 'half_angle_hex': (angle * -0.5).hex(),
                              'sin_hex': math.sin(angle * -0.5).hex(), 'cos_hex': math.cos(angle * -0.5).hex(), 'quaternion_hex': doubles(step)})
            quaternion = MultiplyQuat(quaternion, step)
        derived = ViewMatrix(quaternion)
        expected = link.ConfigValue.RootValue.FieldsValue['f9f8'][index]['o'].FieldsValue['f368']['f08']
        if derived != expected or actual[index].FieldsValue['f368']['f08'] != expected:
            raise ValueError('this runtime did not reproduce its own actual serialized standard-view coefficients')
        x, y, z, w = quaternion
        raw = [(1 - (z*(z+z) + y*(y+y)), x*(y+y) - w*(z+z), w*(y+y) + x*(z+z)),
               (w*(z+z) + x*(y+y), 1 - (z*(z+z) + x*(x+x)), y*(z+z) - w*(x+x)),
               (x*(z+z) - w*(y+y), w*(x+x) + y*(z+z), 1 - (y*(y+y) + x*(x+x)))]
        rows = [{'raw_hex': doubles(row), 'squared_length_hex': ((row[0]*row[0] + row[1]*row[1]) + row[2]*row[2]).hex(),
                 'inverse_length_hex': (1.0 / math.sqrt((row[0]*row[0] + row[1]*row[1]) + row[2]*row[2])).hex()} for row in raw]
        views.append({'name': name, 'index': index, 'rotations': rotations, 'quaternion_hex': doubles(quaternion),
                      'rows': rows, 'matrix_hex': {key: value.hex() for key, value in derived.items()}})
    result = {'schema': 'kit.sw2026.perpendicular-disclosed-runtime-math.v1', 'python_version': sys.version,
              'machine': platform.machine(), 'worker_sha256': sha256(args.worker.read_bytes()).hexdigest(),
              'probe_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
              'projection': projection, 'standard_views': views, 'heldout_inputs_read': 0, 'native_processes_started': 0,
              'writer_source_changed': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({'output_sha256': sha256(args.output.read_bytes()).hexdigest(), 'heldout_inputs_read': 0,
                      'native_processes_started': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
