# Decoder load and start-up speed

## Behavior

Typed JSON reconstruction validates the wire data once at the root.
Before this change, `FromData` validated and copied each nested value again at every level.
One 3.25 MB Fusion document caused 2.96 million validation calls for 136,804 values.
Each reader uses this reconstruction to confirm that the neutral JSON is stable.
`CheckWireData` still validates the complete input before any value is decoded.
Rejected input raises the same exception as before.

The pinned Fusion and SOLIDWORKS readers hash the SDK sources with `os.walk` and plain string paths.
The digest mapping keeps the same keys, separators, order and values as the earlier `pathlib` code.
Both readers still hash every source file again at the end of the run.
The SOLIDWORKS reader now walks the source tree again for that check.
It therefore also detects a Python file added during the run.

The `convert` package resolves its public names on first use.
SOLIDWORKS write checks in the adapter registry load only when the registry writes.
The Fusion and SOLIDWORKS writer facades load their writers on first use.
Adapter discovery resolves deferred facade names, so the registry still finds every reader and writer.
Fusion strict projection loads its authoring code only after a native profile qualifies.
Every public name that resolved before this change still resolves to the same object.

Typed record resolution and tagged-container construction finish outside child traversal.
This preserves the supported assembly nesting range without increasing the interpreter recursion limit.
Adapter discovery includes namespace classes even when a plugin customizes `__dir__`.
The SOLIDWORKS writer facade retains its explicit wildcard export.

## Verification

The host was an Apple M4 with macOS 26.6, CPython 3.14.7 and Git 2.50.1.
Other jobs shared the host, so absolute times varied between runs.
The baseline was `145704048`.

Each measurement alternated the baseline and the candidate five times.

| Offline workload                           | Baseline median (s) | Candidate median (s) |
| ------------------------------------------ | ------------------: | -------------------: |
| Eight Fusion assets with `--allow-partial` |                3.12 |                 2.18 |
| `ordinary_rectangle_control.f3d`, strict   |                2.26 |                 1.36 |
| `example.SLDPRT`, default configuration    |                1.34 |                 1.04 |

The eight Fusion assets were `ordinary_rectangle_control.f3d`, `advanced.f3d`, `tangent_chain.f3d`, `surface_one_rail.f3d`, `cut.f3d`, `two_spacing.f3d`, `root_suppressed.f3d` and `solid_aligned.f3d`.
Both arms decoded one asset strictly and six with partial fallback.
Both arms rejected `root_suppressed.f3d` with the same reason and returned exit status `3`.
All nine `document.json` files matched the baseline byte for byte.
The strict Fusion control kept neutral SHA-256 `15e49b5f267f2327fd7b69dd975038d9bfa0c25eace57f0a2bcec698e3175825`.
The SOLIDWORKS control kept neutral SHA-256 `c30d13ac88073f1497606cf2cacbe7b8c5e88816c4bccce560f28476f9e75eb7`.
Receipts differ only in fields bound to source and tool hashes.

| Component measurement                            |   Baseline | Candidate |
| ------------------------------------------------ | ---------: | --------: |
| `CadDocument.from_json`, 3.25 MB Fusion JSON     |   1,491 ms |    179 ms |
| `CadDocument.from_json`, 0.76 MB SOLIDWORKS JSON |     370 ms |    316 ms |
| One SDK source digest pass                       |     210 ms |    118 ms |
| Fusion reader imports                            | 1,277.6 ms |  283.0 ms |
| SOLIDWORKS reader imports                        | 1,285.1 ms |  184.0 ms |

Reconstruction times are the best of five reads in one process.
Both reconstructions wrote back the same JSON text.
Digest and import times are the best of three runs.
Import times are `-X importtime` cumulative totals with warm bytecode.
The Fusion reader import loaded 2,244 modules instead of 3,933.
The SOLIDWORKS reader import loaded 1,001 modules instead of 3,934.

## Limits

SOLIDWORKS reconstruction gained little from the root check.
Most of its reconstruction time is in `get_type_hints` for each record.
Compatibility binding rewrites model annotations when packages load.
A cache of type hints therefore needs a separate design and is not part of this change.

Each module in `convert` and `interchange` imported in a fresh process.
`python -m convert --help`, `kit --help` and `kit formats` output matched the baseline.
Performance and byte comparisons establish offline compatibility only.
Native application acceptance and semantic qualification remain separate.

## Follow-up verification

The original head saved a 100-level linked assembly but raised `RecursionError` when reopening its JSON on Python 3.14.7.
The repaired decoder reopens that document and preserves its canonical JSON.
The regression also passed at 80 levels on Python 3.11.15.
The focused interchange, registry, and JSON adapter run passed 154 cases, including the hidden-plugin case.
The [assembly depth gotcha](../../../../Gotchas/Conversion/Json/AssemblyJsonDepth.md) records the failure and repair.
