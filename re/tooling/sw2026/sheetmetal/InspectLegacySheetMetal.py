from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
from types import ModuleType

PROBE_SHA256 = 'bc23bf8744fe292081ae2780eb6adc41d05630323dec2fd5026efdf419d24558'
CONFIG = 'Contents/Config-0'


def local_module(name, filename, expected=None):
    path = Path(__file__).resolve().with_name(filename)
    source = path.read_bytes()
    digest = sha256(source).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError(f'{filename} differs from its frozen SHA-256')
    module = ModuleType(name)
    module.__file__ = str(path)
    exec(compile(source, str(path), 'exec'), module.__dict__)
    return module, digest


def unpack_reference(reference, revision, root):
    git = ['git', '--no-replace-objects', '-C', str(reference)]
    clean_env = {key: value for key, value in os.environ.items()
                 if not key.upper().startswith('GIT_')}
    archive = root / 'Reference.tar'
    serial = 're/tooling/sw2026/serial'
    for selectors in ([revision, 'src'], [f'--prefix={serial}/', f'{revision}:{serial}']):
        with archive.open('wb') as output:
            subprocess.run([*git, 'archive', *selectors], check=True,
                           stdout=output, env=clean_env, timeout=90)
        with open_tar(archive) as payload:
            payload.extractall(root, filter='data')
    sys.path[:0] = [str(root / 'src'), str(root / serial)]


def inspect_legacy(source, probe, legacy):
    from Classes import registry
    from Core import ArchiveError
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    archive = SldprtArchive.from_bytes(source)
    observations = []
    bend_observations = []
    configured = []

    def legacy_registry():
        rules = registry()
        legacy.install_legacy_resolved_rules(rules, probe.record_boundary(observations))
        legacy.install_legacy_bend_rules(rules, probe.record_boundary(bend_observations))
        configured.append(rules)
        return rules

    result = probe.inspect(archive, legacy_registry, CONFIG, linked=True)
    linked = result['linked_streams']
    if not result['positive_populated_observed'] or linked['cmgr']['mode'] != 0:
        raise ArchiveError('expected a populated direct legacy master and CMgr mode zero')
    resolved = linked['resolved']
    image = archive.require(CONFIG + '-ResolvedFeatures')
    rules, = configured
    version = result['config_version']
    resolved['legacy_candidate_replays'] = probe.replay_boundaries(image, rules, version, observations)
    resolved['legacy_bend_replays'] = legacy.replay_legacy_bend(image, rules, version, bend_observations)
    return result


def main():
    parser = ArgumentParser(description='Replay loader-backed records in digest-pinned legacy ResolvedFeatures')
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--part', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    probe, probe_digest = local_module('FrozenConfigProbe', 'InspectSheetMetalConfig.py', PROBE_SHA256)
    legacy, rule_digest = local_module('LegacyResolvedRules', 'LegacyResolvedRules.py')
    with args.part.open('rb') as handle:
        source = handle.read(probe.MAX_PART + 1)
    digest = probe.image(source)
    if not source or len(source) > probe.MAX_PART or digest != args.sha256:
        parser.error('part is empty, oversized or differs from its supplied digest')
    provenance = dict(source_sha256=digest, reference_revision=probe.REFERENCE,
                      frozen_probe_sha256=probe_digest, legacy_rule_sha256=rule_digest,
                      legacy_probe_sha256=probe.image(Path(__file__).read_bytes()))
    with TemporaryDirectory(prefix='KitLegacySheetMetal') as temporary:
        unpack_reference(args.reference, probe.REFERENCE, Path(temporary))
        from Core import ArchiveError

        try:
            result = inspect_legacy(source, probe, legacy)
        except (ArchiveError, ValueError, KeyError) as error:
            print(json.dumps(dict(provenance, research_only=True, exact_replay=False,
                                  error_type=type(error).__name__, diagnostic=str(error)[:350])))
            return 2
    print(json.dumps(dict(provenance, **result), indent=2, sort_keys=True))
    return 0 if result['linked_streams']['resolved']['exact_replay'] else 2


if __name__ == '__main__':
    sys.exit(main())
