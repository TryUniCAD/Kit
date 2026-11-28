import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(packet_path):
    packet = json.loads(packet_path.read_bytes())
    require(packet['schema'] == 'kit.sw2026.sdk-revolve-native-packet.v1', 'unexpected SDK revolve packet')
    root = packet_path.parent
    for row in packet['files']:
        relative = Path(row['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'packet path escapes its fixed root')
        path = root / relative
        require(path.is_file() and path.stat().st_size == row['bytes'] and digest(path) == row['sha256'],
            'frozen SDK revolve packet differs: ' + row['path'])
    job_path = root / packet['job_path']
    job = json.loads(job_path.read_bytes())
    require(job['source_revision'] == packet['source_revision']
        and job['verify_saved_edit'] is True and job['inspect_profile'] is True
        and job['inspect_before_rebuild'] is True and job['forward_handedness'] == -1
        and job.get('inspect_regeneration_warning', False) is False,
        'SDK revolve native acceptance protocol differs')
    require(len(job['cases']) == 4 and len({row['sha256'] for row in job['cases']}) == 4,
        'SDK revolve packet lacks the four independent generated inputs')
    for row in job['cases']:
        require(row['model']['plane'] == 'front' and row['model']['split'] == 'discovery',
            'native packet attempts an unqualified source family or hidden input')
    return packet, job_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('packet', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    packet_path = args.packet.resolve(strict=True)
    packet, job_path = verify(packet_path)
    if args.verify_only:
        print(json.dumps({'verified': True, 'packet_sha256': digest(packet_path), 'files': len(packet['files']),
            'native_execution': False, 'heldout_inputs_read': 0}))
        return 0
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from InspectGeneratedRevolves import main as inspect_main
    import AuthorRevolveSources
    from SdkRevolveObserver01 import SdkRevolveObserver
    job = json.loads(job_path.read_bytes())
    SdkRevolveObserver.expected_trees = {row['model']['name']: row['expected_tree'] for row in job['cases']}
    AuthorRevolveSources.RevolveAuthor = SdkRevolveObserver
    sys.argv = [str(Path(__file__).with_name('InspectGeneratedRevolves.py')), str(job_path)]
    status = inspect_main()
    verify(packet_path)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
