# Fusion encoder native measurements

Both edited cuboid candidates passed fresh-process measurements in licensed Fusion 2706.1.17 on Windows on November 25, 2026.
The [oracle procedure](../LocalOracle/EncoderRoundTrip/README.md) records how to reproduce the measurements.
These observations apply to the two candidate digests below and to the edited role.

The candidate generator was the Fusion adapter at `2050093926c96c03fc69c161e1b41276b0859788`.
Its source SHA-256 was `7981a19ddeffebd7fef30742a3b105f06ca7977f0d5650c779c80cae8dac581a`.
The measurement script SHA-256 was `2b00f06d5861be06cbaf9f3b8dcc8924d7f452dd39f0efe35e27dc19983d9e8a`.

The public Kit writer generated each seed archive.
The strict SDK reader decoded the seed, which was persisted and reloaded as typed JSON.
The encoder set the extrusion depth and produced a new archive from the supported cuboid model.
The Fusion API independently authored each control at the expected candidate dimensions.

| Case     | Seed height (mm) | Encoder height (mm) | Opened volume (mm³) | Opened centre (mm) | Native edited height (mm) | Edited volume (mm³) |
| -------- | ---------------: | ------------------: | ------------------: | ------------------ | ------------------------: | ------------------: |
| Baseline |             13.8 |                22.6 |           10044.344 | 8.2, 13.55, 11.3   |                      28.3 |           12577.652 |
| Holdout  |             24.6 |                31.4 |           17701.122 | 21.85, 6.45, 15.7  |                      19.7 |           11105.481 |

Both candidates contained one solid, six faces, twelve edges, and eight vertices.
Both showed healthy `Encoder Rectangle` and `Encoder Extrusion` timeline nodes and a fully constrained sketch.
Fusion rebuilt, rolled back and restored the extrusion, and rebuilt after the driving height edit.
A fresh process reopened each saved edited and restored variant with its expected geometry.
Both bracketing controls passed for each case. Each stage closed all opened documents.

| Case     | Source SHA-256                                                     | Neutral JSON SHA-256                                               | Candidate SHA-256                                                  |
| -------- | ------------------------------------------------------------------ | ------------------------------------------------------------------ | ------------------------------------------------------------------ |
| Baseline | `dc2e0269311de79c13c3617b6febe9cd47a707d92968903b1c4ed5dfff9625e7` | `bcc0a9002a1b88041ff697f89863305cd64ddf42f9ebe30e3db8759500b50f3d` | `aeab6d2642a297a654483aca09aea4943fd87d53d6633d9f776e643353df99c2` |
| Holdout  | `930ebdc5bf47084f53db9da28524f444405feac5c287bdc43bc8273405482cee` | `eee8256f6028a4171ce733dc551c029e29b8f8ace36d0a0aa7677b4094481322` | `cc19ad56fe816263f0d2cb46072c1b17fe9acfeec3110a03e503ef4ed2df78ed` |

| Case     | Stage          |   PID | Receipt SHA-256                                                    |
| -------- | -------------- | ----: | ------------------------------------------------------------------ |
| Baseline | Control before | 26616 | `01ba4f79d0e6e13dbaa18aafbdec49db0558b97f9157feb8a29fb54aa3b6c731` |
| Baseline | Candidate      | 25736 | `e973a4467beeedfe1f9111f40c7e9c3e89b1e1ef82acd16fdb245068c76ed73a` |
| Baseline | Reopen         | 34496 | `8f6cac146d7d6f46d3eac32a5b7c227a146d1e24f9feb25cb437d4786fe16133` |
| Baseline | Control after  | 36336 | `a311993d113f335cc33df9ee9a346418ac0f47462c1359a3cea2d8cc5b8c0de1` |
| Holdout  | Control before | 26616 | `eb8e5249769f449687aa7a189eeb06890e7c90885fb010357d0a9f85d38e7586` |
| Holdout  | Candidate      | 34800 | `eb06eb8ec602e71d07d7782172cbf4c7053ece314ad5827548726f8d2b64d4d9` |
| Holdout  | Reopen         | 30472 | `9247b260cd0f94f64f2c64af3a80eb548c909bcc97ffb0089132169bd88fb739` |
| Holdout  | Control after  | 36336 | `1d01460be81710b3f4c5fffbe8adbe3a63ca02b2dc89529d2b865f3cb1a78b57` |

The source archives, persisted JSON, candidates and stage receipts are retained in the task scratch directory `.rescratch/FusionEncoderNativeCandidateArtifacts` of the original checkout.
The measured seed archives use the Kit constructor profile. Vendor-authored controls establish the measured geometry independently.
Native verification of unchanged reconstruction and qualification against additional source graphs remain open.

The strict SDK reader reopened both Kit-emitted candidates in Python 3.14.6 before native measurement.
The same reader refused the four `VendorEdited.f3d` and `VendorRestored.f3d` variants after Fusion saved and reopened them.
It reported `Native constrained rectangle requires five rules and two dimensions` for each one.
The native observations establish the edited candidates' application behavior. The saved variants still need a separate strict reader qualification.
