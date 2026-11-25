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
Qualification against additional source graphs remains open.

The strict SDK reader reopened both Kit-emitted candidates in Python 3.14.6 before native measurement.
The same reader refused the four `VendorEdited.f3d` and `VendorRestored.f3d` variants after Fusion saved and reopened them.
It reported `Native constrained rectangle requires five rules and two dimensions` for each one.
The checked records retain four horizontal and vertical rules, two dimensions, and a fixed corner at the origin position.
On save, Fusion adds graphics, one snapshot, and two configuration records.
Those records select the strict vendor projection, which expects a fifth rule for explicit coincidence with the sketch origin.
The native observations establish the edited candidates' application behavior. The saved variants still need a separate strict reader qualification.

## Integrated CLI reconstruction and edit

The normal research CLI on integration revision `a529ff98cb7624982bb05a41c1ab7c07eaed6a38` used the same baseline seed archive.
Both output roles passed native open, rebuild, independent height edit, restore, export, and fresh-process reopen.
The installed build was Fusion 2706.1.17. Each role had healthy independent before and after controls.

| Role           | Candidate SHA-256                                                  | Initial height (mm) | Initial volume (mm³) | Initial centre (mm) | Volume at 28.3 mm native edit (mm³) |
| -------------- | ------------------------------------------------------------------ | ------------------: | -------------------: | ------------------- | ----------------------------------: |
| Reconstruction | `bb662739916ed12c21680f9e4b53f553625ea799f066ba4e7d2f88417ea55112` |                13.8 |             6133.272 | 8.2, 13.55, 6.9     |                           12577.652 |
| Edited         | `8865a3153326e52034c9110ccfe5c14ec857d2bde524a723c8144bd8907abc8a` |                22.6 |            10044.344 | 8.2, 13.55, 11.3    |                           12577.652 |

| Role           | Stage          |   PID | Receipt SHA-256                                                    |
| -------------- | -------------- | ----: | ------------------------------------------------------------------ |
| Reconstruction | Control before | 25000 | `99c5649dc3e04c40582bcd0dc0d9587edb2e7a0e4f4bdcb87c2fb5258e48f24e` |
| Reconstruction | Candidate      | 34032 | `7560b4f5a920e61f0c97377d52609d4b03ccfd9946d30c48317a3965014ed71c` |
| Reconstruction | Reopen         | 13964 | `c86e76b10d8763cfeaa1b3206d0bc146b0b4b96e117365476535c3c25a617c8a` |
| Reconstruction | Control after  | 24112 | `8bf2da5d1a4f9b0671eb48b70a7228188ffa81c7fc293d7576262542b44f09c9` |
| Edited         | Control before | 25000 | `36c8e345083eec73692ce44f662067945efbac85415ad096a2eda5dc58714c30` |
| Edited         | Candidate      | 26152 | `c493581624bb8004ffd887a82df40c7381c16f5d2960d90065b2ed333a3b200f` |
| Edited         | Reopen         |  1460 | `fd900bac6e48665f5de523b951df9096f6387e2123d9ea979cf63362179f0e8d` |
| Edited         | Control after  | 24112 | `0eb6ea9dbbcbf73653c962b3b344a718a7bf08ac15ef9df8ef5330e51f9e2cf8` |

The raw readings, independent controls, saved variants, source hash, and exact generated artifacts remain under `.rescratch/EncoderIntegratedFusion01`.
The shared research CLI attached both receipts and reported `measurement_status: observed` and `native_qualification: pending` for each one.
The immutable manifest SHA-256 remained `974e6fa32c7db89aa27e64f6a669b38c2b6ad59143002cfe9d5b8a88dc347ecc`.
The reconstruction receipt SHA-256 is `5f2d54b0efe634bde01930c98ae6494fba5db3c467fc37059cfbca5df8727356`.
The edited receipt SHA-256 is `8e69751b17e255350f74fb92c47dcc294c3b33fb854f991c9f91044c26345106`.
The strict SDK reader also refused the four variants that Fusion saved in this integrated run.

| Oracle role    | Saved archive        | SHA-256                                                            |
| -------------- | -------------------- | ------------------------------------------------------------------ |
| Reconstruction | `VendorEdited.f3d`   | `1e7584c59f898b41af2ea3d5accf0c5c44e793bcd0ab7c5486a08feb55443aa2` |
| Reconstruction | `VendorRestored.f3d` | `b6726c11bd4e67155035de7fc6bcda3b559682fc9c4f496c2b35a05d84184752` |
| Edited         | `VendorEdited.f3d`   | `303c02e4b3853dbaf709900f3611348dc1df9f22019f61e5d1af875c86c2a3f4` |
| Edited         | `VendorRestored.f3d` | `ebd4cdc0e1802e5f3ba13c660dd3e99c90d930fbcfb62f36565b972302737361` |
