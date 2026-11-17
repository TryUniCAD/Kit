# Decode pinned Fusion research inputs

## Purpose and prerequisites

Decode committed F3D/F3Z assets with separate typed documents, evidence receipts, and a run summary.
Use Python 3.14 and a trusted checkout containing the pinned corpus Git objects.
Choose an unused output directory and asset paths from `re/automation/Corpus.json`.
No CAD application or model provider is required.
The [step register](AutomationSteps.md) owns implementation and qualification status.

## Procedure

Run the reader from the selected checkout:

```sh
uv run --frozen --no-default-groups --extra dev --python 3.14 python re/automation/FusionReader.py --root . --asset re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d --output /tmp/KitFusionResearch
```

Repeat `--asset` for up to 1000 distinct committed inputs.
The direct entry point remains `re/automation/FusionReader.py` with the same reader options.
Use `--manifest PATH` for another supported manifest.
`--allow-partial` explicitly permits strict-first fallback and records any strict rejection.

## Expected result and limits

`summary.json` records every selected asset as decoded, rejected, or reader error.
Each decoded asset has a path-hash directory containing `document.json` and `receipt.json`.
Documents retain SDK serialization and pass typed reconstruction.
Receipts bind source bytes, SDK/tool fingerprints, options, hashes, and unresolved evidence.

Exit `0` means all selected assets decoded.
Exit `3` means a published summary includes rejected or reader-error outcomes.
Exit `1` means the run failed before normal publication.
Existing output directories and symlinks are refused.
Files use `0600` and directories use `0700` where supported.

Inputs are bounded to 256 MiB, neutral JSON to 64 MiB, receipts to 32 MiB, and a run to 4 GiB.
Pin checks cover path, blob, size, SHA-256, and prefix.
SDK source changes detected during decoding reject publication.
`portable_complete` remains false, and native acceptance remains not established.
Both strict and partial research outputs carry `kit.research_read_status = unqualified` in document metadata. This marker is advisory on the existing main SDK; this automation scope adds no production export guard. Retain the receipt and its unresolved evidence when inspecting output.
Structural decoding and partial fallback do not qualify editable cross-format conversion.

## Historical decoder evidence

The original [reader guide at `fb723e0a`](https://github.com/Stephen316/Kit/blob/fb723e0a920b4d03ad2d5635882860b800a9b61c/Documentation/Reference/Research/FusionResearchReader.md) describes the broader strict-prism rules, native write safeguards and full per-file outcome census. Those decoder additions and their coupled suites remain in the preserved follow-up scope. They are not features or CI artifacts of this main-based automation candidate.

The historical 714-input checkpoint reported 12 strict results, 685 partial results and 17 rejections at its original source. Parsing outcomes do not establish complete semantics, independent native acceptance or the result of a current-candidate run. The current [main-SDK boundary record](../../Changes/Research/Controller/MainSdkAutomationBoundaries.md) owns the reader contract.

## Recovery and related information

Use the [sealed history preparation](../../Changes/Research/CaptureHistoryBinding.md) to acquire the permitted pinned inputs. Restore the intended manifest or choose another output path as needed.
Inspect per-asset reasons and implement missing codec knowledge instead of relaxing checks.

- [Separate installed CLI proposal](https://github.com/TryUniCAD/Kit/pull/119)
- [Reader source](../../../re/automation/FusionReader.py)
- [SOLIDWORKS reader](SolidworksResearchReader.md)
