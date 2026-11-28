# SOLIDWORKS 2026 captured-control admission

Baseline work for [the plan on PR #296](https://github.com/TryUniCAD/Kit/pull/296):
pin the revision, build, input hashes and tolerances (baseline 1), and admit a capture as a
control only after independent checks verify its expected values (baseline 5).

This page records, for the committed SOLIDWORKS 2026 research inputs, whether each pinned
file exists with the recorded SHA-256 and whether the values recorded for it match what the
repository's own pinning and campaign verifiers report when run. It is research evidence; it
does not qualify native writing, complete feature semantics or conversion acceptance.

## Pinned inputs

| input | value |
| ----- | ----- |
| repository revision (audit base) | `1619f00bf532caad262d1557bd69281179e5c497` (`main`) |
| corpus pin revision | `f643a3dd01555bc18cc49aa973cf3f7d3ff21ad2` (`re/NativePlacement2026/CanonicalCorpus.json` `source_revision`, an ancestor of `main`) |
| build manifest | `re/solidworks/v2026/Manifest2026.json`, file SHA-256 `e046379b265c216a40c2dc29e9a93afb3377401e23fa5044ebb7ff44667d3909`, introduced at `181d3268a` |
| pinning tool | `re/automation/Corpus.py` |
| campaign verifiers | `re/NativePlacement2026/Verify.py`, `re/FeatureLadders2026/Verify.py` |
| environment | git 2.43.0, Python 3.12.3 |

## 1. Build pin (`Manifest2026.json`)

`Manifest2026.json` records the SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`. It lists 14
licensed modules and sets `tracked_in_git: false`. The modules are vendor binaries held
outside the repository, so their existence and SHA-256 cannot be checked in this checkout and
were deliberately not fetched. The manifest is the baseline pin for the build only.

| module | bytes | SHA-256 | file version |
| ------ | ----: | ------- | ------------ |
| sldappu.dll | 16519768 | `50d9ec9df77bb6cc0fcf6f5620626291df948bd839d153836d317237afca71bf` | 34.5.2.0604 |
| sldarchiveu.dll | 231512 | `5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48` | 34.5.2.0604 |
| sldasmu.dll | 10863704 | `05ab90ee7380335088505c47202137c63dbce18d7d516e7fd6703aee31d70390` | 34.5.2.0604 |
| sldmatu.dll | 5517400 | `8a07d6b5d8d7d4f9f064b28e1d60f853fd754caa6d507db28b06031f287e051e` | 34.5.2.0604 |
| sldmfcu.dll | 8274520 | `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` | 34.5.2.0604 |
| sldmgu.dll | 2363992 | `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c` | 34.5.2.0604 |
| sldmodu.dll | 46536280 | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` | 34.5.2.0604 |
| sldmopartu.dll | 6836824 | `aa3fa88eeb5349c8ac2161ce9b3f18ab4e23417598c6b57719c88d5d6c178da9` | 34.5.2.0604 |
| sldsmmu.dll | 8364632 | `460e6d82f6b811805860b6df03e7b551a4a573aad598bd27501226586b0c9b95` | 34.5.2.0604 |
| slduiu.dll | 36036696 | `025917f6acd906e041652386c763a7f5dea8c2c1e8190f50265a6c51bd5d51d7` | 34.5.2.0604 |
| sldutu.dll | 4061272 | `dbc147c10b658544e44a7c13d3ae656c26a0778e9241fe74d6ca9ecae8730933` | 34.5.2.0604 |
| sldvisualstateu.dll | 1326168 | `fb85d7921c52393e8bb847258b72d8cd006b37c118138c8260c6efe7dcc22c2c` | 34.5.2.0604 |
| sldworks.exe | 718936 | `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe` | 34.5.2.0604 |
| swccu.dll | 252504 | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` | 34.5.2.0604 |

## 2. Committed captured controls

The committed captured controls in the 2026 tree are the seven `.SLDPRT` parts under
`re/solidworks/v2026/corpus/`. `Manifest2026.json` itself does not list them; they are pinned
by the corpus manifest and by the per-control measurement records.

Every listed file exists. Its working-tree SHA-256 equals the blob stored at the corpus pin
revision and the SHA-256 recorded for it in `re/NativePlacement2026/CanonicalCorpus.json` and
in the primary expected-value record. Hash identity is exact; no numeric tolerance is
recorded for these controls.

| control | bytes | SHA-256 | git blob at `f643a3dd` | introduced | primary expected-value record | admitted |
| ------- | ----: | ------- | ---------------------- | ---------- | ----------------------------- | -------- |
| `corpus/curves-discovery/D19Annulus.SLDPRT` | 71454 | `2a9846fa9ddc882ef3b848dfc311a7859d102ab9fa7687769cdba88a7b510439` | `05c0016070a32af5242e34f39f2717422115e49c` | `f89ac9a72` (#206) | `../measurements/2026/HistoryStreamSources01.json` | pass |
| `corpus/ladder/L1_boss.SLDPRT` | 56249 | `55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6` | `e140de65b6000c94897474edb61ad4c91540c8ad` | `c34686b1b` (#171) | `../measurements/2026/SdkOrdinaryPartDefinition01.json` | pass |
| `corpus/light-counts/OneLights.SLDPRT` | 66664 | `b2772eebfd9f11038f72c76fe3a6ace4b9cd45373425f75921be45174943edb7` | `15586c33c5dfe0394b8d285fb238c940c095fc40` | `1b70ad5f5` (#191) | `../measurements/2026/ConfigSceneCounts01.json` | pass |
| `corpus/light-counts/TwoLights.SLDPRT` | 66103 | `287f64869f8d037ebf3c92712453440e3f162beb6d1ac9226afd215d965b7dba` | `a0700b7cac232810343cab6afd9fe2812228328d` | `1b70ad5f5` (#191) | `../measurements/2026/ConfigSceneCounts01.json` | pass |
| `corpus/local-import-readback/ConcaveOwned.SLDPRT` | 10890 | `fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33` | `f0f62c325039d6ffc063bc4fe8f0de982f9aba25` | `086870fac` (#172) | `../measurements/2026/LocalImportReadbackFixtures01.json` | pass |
| `corpus/local-import-readback/RectangularBare.SLDPRT` | 9914 | `302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357` | `9283c487d2c834b63c7ecdec73199ff86847c002` | `086870fac` (#172) | `../measurements/2026/LocalImportReadbackFixtures01.json` | pass |
| `corpus/part-properties/CircularProperties.SLDPRT` | 66367 | `1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23` | `9d7fb7cd28856dd2a03b0e9aee588ee850fb63c0` | `a3f014640` (#183) | `../measurements/2026/LiteralPartTextPhysical01.json` | pass |

Recorded expected values, quoted from the primary records:

- `D19Annulus`: `bytes` 71454, `sha256` `2a9846fa…0439`, `original_source_sha256`
  `f2d1bafc…5294`, `source_role` "SOLIDWORKS authored discovery case with published privacy
  normalization" (`HistoryStreamSources01.json`); `saved.D19Annulus.source_path` bound in
  `SdkOrdinaryPartDefinition01.json`.
- `L1_boss`: `file_sha256` `55e5a984…2ac6` (`SdkOrdinaryPartDefinition01.json`);
  `controls.ladder.part_sha256` `55e5a984…2ac6` with `config_sha256` `e7e700d5…e5b2`
  (`ConfigSceneSource01.json`).
- `OneLights`: `controls.one.part_bytes` 66664, `part_sha256` `b2772eeb…edb7`,
  `directional_count` 1, `scene_counter` `[70, 79]` (`ConfigSceneCounts01.json`).
- `TwoLights`: `controls.two.part_bytes` 66103, `part_sha256` `287f6486…7dba`,
  `directional_count` 2, `scene_counter` `[70, 81]` (`ConfigSceneCounts01.json`).
- `ConcaveOwned`: `bytes` 10890, `sha256` `fa1b84b7…3d33`, `native_geometry.volume_m3`
  `5.16e-06`, `area_m2` 0.002068, `faces` 8, `edges` 18, `vertices` 12 (`LocalImportReadbackFixtures01.json`).
- `RectangularBare`: `bytes` 9914, `sha256` `302c8e9b…a357`, `native_geometry.volume_m3`
  `2.574e-06`, `area_m2` 0.00115, `faces` 6, `edges` 12, `vertices` 8 (`LocalImportReadbackFixtures01.json`).
- `CircularProperties`: `control.sha256` `1c1bc718…2d23`, `config_sha256` `5c789425…45c7`,
  `text.feature_count` 27, `archive_version` 19000, `profile` `compatible_literal_text`,
  `status` `complete` (`LiteralPartTextPhysical01.json`).

## 3. Command results

`Corpus.py` at the corpus pin revision reports the same control identities and the same
recorded evidence as the committed manifest:

```sh
python3 re/automation/Corpus.py snapshot \
  --revision f643a3dd01555bc18cc49aa973cf3f7d3ff21ad2 \
  --manifest /tmp/verify/canonical_f643a3dd.json
# exit 0
# {"evidence_files": 299, "native_acceptance": "not_established",
#  "native_by_format": {"f3d": 2040, "f3z": 2, "sldasm": 6, "sldprt": 248},
#  "qualified_pairs": 0}
```

Comparing that fresh snapshot with `re/NativePlacement2026/CanonicalCorpus.json`: 2597 assets
and 299 evidence files in both, **0 differing assets**, and 33 differing evidence entries. The
seven control assets agree on `sha256`, `size_bytes` and `git_blob` in the fresh snapshot, the
committed manifest and the working tree.

The two campaign verifiers pass for their own packages:

```sh
python3 re/NativePlacement2026/Verify.py --output /tmp/verify/np.json
# {"status": "passed", "artifacts": 1329, "complete_native_batches": 47, ...}
python3 re/FeatureLadders2026/Verify.py --output /tmp/verify/fl.json
# {"status": "passed", "artifacts": 514, "cases": 96, ...}
```

## 4. Commands run

```sh
sha256sum re/solidworks/v2026/Manifest2026.json
sha256sum re/solidworks/v2026/corpus/*/*.SLDPRT
git rev-parse f643a3dd01555bc18cc49aa973cf3f7d3ff21ad2:re/solidworks/v2026/corpus/<control>.SLDPRT
git cat-file blob <blob> | sha256sum
python3 re/automation/Corpus.py snapshot --revision f643a3dd01555bc18cc49aa973cf3f7d3ff21ad2 --manifest /tmp/verify/canonical_f643a3dd.json
python3 re/automation/Corpus.py check --manifest re/automation/Corpus.json
python3 re/automation/Corpus.py check --manifest re/NativePlacement2026/CanonicalCorpus.json
python3 re/NativePlacement2026/Verify.py --output /tmp/verify/np.json
python3 re/FeatureLadders2026/Verify.py --output /tmp/verify/fl.json
git log --diff-filter=A --format='%H %s' -- re/solidworks/v2026/corpus/<control>.SLDPRT
```

## 5. Mismatches and gaps

- `Manifest2026.json` lists only the 14 build modules, not corpus controls. The committed
  controls are the seven `.SLDPRT` parts under `re/solidworks/v2026/corpus/`; this page admits
  them and records the build pin separately.
- `python3 re/automation/Corpus.py check --manifest re/automation/Corpus.json` fails with
  `corpus error: Command '[... 'rev-parse', '--verify', '74a0bc35…^{commit}']' returned non-zero
  exit status 128`. The committed canonical corpus manifest pins `source_revision`
  `74a0bc353421c25f7a6c539897baadf593a05766`, which is not present in the repository after a
  full fetch, so this manifest cannot be checked here.
- `python3 re/automation/Corpus.py check --manifest re/NativePlacement2026/CanonicalCorpus.json`
  fails with `corpus error: manifest differs from pinned Git objects or authoring
  specifications`. The published file was normalized: its 33 evidence entries (204 historical
  external profile paths) replace absolute capture paths with `<historical external path>`, as
  `CorpusVerification.json` records. A fresh snapshot at the same revision differs only in
  those entries. No control asset differs.
- Neither campaign verifier references these seven controls: `D19Annulus`, `L1_boss`,
  `OneLights`, `TwoLights`, `ConcaveOwned`, `RectangularBare` and `CircularProperties` appear
  zero times in `re/NativePlacement2026/Manifest.json`, `re/NativePlacement2026/OfflineOutcomes.json`,
  `re/NativePlacement2026/ScopePins.json`, `re/FeatureLadders2026/Manifest.json` and
  `re/FeatureLadders2026/EarlierCorpusOutcomes.json.gz`. Their passing status is not admission
  evidence for these controls; only `Corpus.py` and the per-control records cover them.
- `D19Annulus` is a privacy-normalized discovery case: its `original_source_sha256` differs
  from the committed `sha256`. The committed hash is the pin.
- No numeric comparison tolerance is recorded for these controls. The recorded geometry in
  `LocalImportReadbackFixtures01.json` is classified `recorded_unqualified`. The campaign
  verifiers use `rel_tol=1e-8` with `abs_tol=1e-6` for their own cuboid checks; that tolerance
  does not extend to these controls.
