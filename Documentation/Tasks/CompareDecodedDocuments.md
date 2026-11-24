# Compare decoded documents in bulk

From a trusted checkout, compare folders of decoded JSON:

```sh
kit research --root . compare SolidWorks Fusion --unit mm -o NewComparison
```

The command pairs files by matching relative paths.
Either folder can go first. The first is labeled left in reports and the second is labeled right.
Use the geometry unit declared for your exports and choose a new output directory.

## Purpose

Compare existing Kit `CadDocument` JSON exports with one standalone command.
The programme uses the existing semantic graph comparator.
Neither decoder runs during comparison.
Feature correspondence uses typed fields and relationships, independently of native identifiers and feature names.

## Before you start

Use a trusted source checkout containing this version of the comparison programme.
Install Kit from this revision with `uv tool install .`.
The installed launcher requires `--root` and runs the comparator from that checkout.
You can also use `python -m KitCli research` in the installed environment.
The comparator itself is source tooling outside the installed wheel.
Raw vendor record dumps and reader receipts are not `CadDocument` inputs.

Identify which exports describe corresponding source designs.
Use `--unit` when both sides share a geometry unit.
For different units, use `--left-unit` and `--right-unit` together in place of `--unit`.
Display units alone do not establish geometry units.
Supported geometry units are `mm`, `cm`, `m`, `in`, and `ft`.

Exact comparison is the default.
For approximate quantities, prepare the five-value [absolute tolerance profile](../Reference/Research/SemanticComparison.md#before-you-start).
Choose tolerances before comparing results.

## Procedure

### Pair independently named exports

Use a manifest when the decoders produce different filenames or source-hash directories.
For example, save `Pairs.json` beside your export folders:

```json
{
  "version": 1,
  "pairs": [
    {
      "id": "rectangle-boss",
      "left": "Solidworks/Rectangle.json",
      "right": "Fusion/source-hash/document.json"
    },
    {
      "id": "through-hole",
      "left": "Solidworks/Hole.json",
      "right": "Fusion/another-hash/document.json"
    }
  ]
}
```

Manifest paths resolve relative to the manifest directory.
Absolute input paths are also accepted.
Each pair needs a unique, nonempty `id` and two input paths.
Pair identities describe the requested comparison; they do not select feature counterparts.

Run from the trusted checkout:

```sh
kit research --root . compare --manifest /path/to/Pairs.json --unit mm -o /path/to/NewComparison
```

Replace the example paths with your actual paths.
The output parent directory must exist.
The output directory must be unused.

### Pair matching directory layouts

`SolidWorks/Case/Part.json` pairs with `Fusion/Case/Part.json`.
Files without a counterpart remain `missing_input` outcomes.
The programme does not infer matching designs from unrelated filenames.
Feature matching happens within each requested document pair.

By default, recursive discovery selects every `*.json` file.
Use `--pattern document.json` for matching reader trees containing receipt and summary sidecars.
Differently hashed reader directories still require a manifest.
Patterns use relative `Path.match` semantics.

Add `--tolerances /path/to/Tolerances.json` to use your declared absolute limits.
Add `--max-candidates 50000` to change each pair's correspondence budget.
The supported candidate range is 1 through 100000; the default is 20000.

Run `kit research --root . compare --help` for all options.
Existing direct invocations of `re/automation/CompareDecoded.py` still accept `--left`, `--right`, `--output` and both per-side unit flags.
Use one pairing mode per run.
Relative CLI inputs and outputs resolve from the command's working directory.

## Expected result

The programme prints the output path, pair count, outcome totals, and exit code.
Inspect these artifacts:

| Artifact                                            | Contents                                                                                                               |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `summary.txt`                                       | One readable outcome and feature-correspondence count per pair                                                         |
| `summary.json`                                      | Complete pair roster, input paths, available input hashes, options, counts, and report hashes                          |
| `reports/0000.json` and subsequent numbered reports | Detailed correspondence evidence, field differences, dependency differences, ambiguity, and unresolved source evidence |
| `unified/`                                          | Original left JSON bytes for pairs that compare equal at zero tolerance with no unresolved issues                      |

Use the `unified` field in each summary row to find the copy, its SHA-256, byte count and geometry unit.
The numbered name uses the same pair index as the detailed report.
The copy preserves the original document and any qualification markers.
Both documents and their embedded documents must contain feature history before a unified copy is eligible.
Each must also contain a design body with an active generating history accepted by the SDK feature preflight.
Datum-only, unsupported, and inactive generator histories retain reports without unified copies.
Historyless documents keep their comparison reports and `equal_observed_graph` status when their observed graphs agree.
Their summary rows and detailed reports record per-side `unified_exclusions` diagnostics, and no copy is published.
This history eligibility check does not establish geometry qualification or native acceptance.
Pairs with differences, unresolved evidence or input failures get reports without copies.
Any nonzero tolerance disables copying for the entire run.
This keeps the folder limited to exact agreement within the comparator's observed scope.
If a copy cannot be published, the report remains available, its summary row records `unified_error`, and the batch returns exit `1`.
The direct script creates `unified/` when you supply `--unified`.

A feature correspondence can contain differences.
It does not mean the features are equal.
The existing engine compares supported parameters, planes, sketches, constraints, selections, timelines, bodies, and materials.
Declared decimal length factors are converted to exact rational values before deriving area and volume factors.
This preserves equivalent feet/millimetre topology measurements at zero tolerance; it cannot recover precision already lost in source values.
Full B-rep, meshes, retained payloads, and assembly graphs remain outside its semantic comparison scope.
Unsupported domains remain explicit issues.

| Exit | Meaning                                                                                                |
| ---: | ------------------------------------------------------------------------------------------------------ |
|    0 | Every selected pair has `equal_observed_graph` status and no copy failed                               |
|    1 | Invalid setup, a missing input, an input error, or a failed unified copy                               |
|    2 | Observed differences exist, without errors or unresolved outcomes                                      |
|    3 | At least one pair is ambiguous, unresolved, incomplete, or retains source issues, without input errors |

Input errors take precedence over unresolved outcomes; unresolved outcomes take precedence over differences.
Read the full outcome totals when a batch contains several statuses.
Invalid documents do not stop later comparisons.
Output-budget refusals retain an incomplete pair report and continue.
Filesystem failures that prevent writing reports or summaries stop the batch.
The detailed engine status can remain `different` when unresolved source evidence also exists.
Without input or copy errors, such batches return exit `3`. Inspect each pair's `counts.source_issues` alongside its detailed differences.

`summary.json` is published last and marks a completed observation batch.
A directory without it is incomplete.
Keep incomplete artifacts for diagnosis and choose a new output directory.
Existing outputs and input files are never overwritten.

The programme observes and hashes input bytes during this invocation.
Those hashes do not prove original capture custody or independently qualify the source semantics.
Every report keeps semantic qualification unverified and native acceptance not established.
Reader agreement alone does not qualify editable conversion.
Even self comparison can retain differences when source references are unresolved; inspect the [self-comparison gotcha](../Gotchas/Research/Comparison/SelfComparisonReferences.md).

## Limits and failure recovery

A batch accepts at most 1000 pairs.
Directory discovery visits at most 100000 entries per side.
Linked directories, linked selected files, and incomplete directory enumeration are refused.
Each document and detailed report has a 32 MiB limit.
Manifests have a 1 MiB limit; tolerance files have a 64 KiB limit.
The batch output budget is 1 GiB, shared by reports, unified copies and reserved summary and error-report capacity.
The [existing graph limits](../Reference/Research/SemanticComparison.md#limits-and-failures) also apply.

For `missing_input`, correct the directory layout or manifest path.
For `reader_error`, inspect the numbered report and supply valid codec JSON.
For ambiguity, obtain distinguishing source relationships.
For unsupported semantics, extend the decoder or comparator with independent evidence.
Do not remove source evidence or increase tolerances merely to obtain equality.

## Related information

- [Semantic comparison contract](../Reference/Research/SemanticComparison.md)
- [Bulk programme change](../Changes/Research/Readers/Comparison/BulkDecodedComparison.md)
- [Exact topology unit factors](../Changes/Research/Readers/Comparison/ExactTopologyUnitFactors.md)
- [Reader sidecar and path gotcha](../Gotchas/Research/Comparison/DecodedExportPairing.md)
- [CAD acceptance criteria](../Reference/Operations/CadSuccessCriteria.md)
- [Historyless unified exports](../Gotchas/Research/Comparison/HistorylessUnifiedExports.md)
