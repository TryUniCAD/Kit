# Read scoreboard for pinned Fusion and SOLIDWORKS files

`re/automation/ReadScoreboard.py` decodes the pinned native files in `re/automation/Corpus.json` and reports how completely each reader understands them. It covers 714 Fusion files, 58 SOLIDWORKS parts and 6 SOLIDWORKS assemblies. The scoreboard measures progress towards a complete read for both applications before writer work.

## Behaviour

For each file, the scoreboard reads the pinned Git blob, checks its SHA-256 and attempts a strict read. When strict reading refuses the file, it records the reason and reads again in partial mode. Read options match the Fusion census: B-rep and tessellation payloads are included.
F3Z uses the pinned research reader's strict and partial modes because the public registry does not expose an F3Z adapter. The scoreboard records the archive's refusal reason. See the [F3Z routing gotcha](../../../Gotchas/Research/Offline/ScoreboardFusionPackages.md).

Each file row records:

- the outcome: `decoded`, `rejected`, `reader_error` or `evidence_limit`;
- the reader mode, `strict` or `partial`, and the strict refusal reason;
- every unresolved item from `ReaderEvidence.reader_evidence`, except the permanent independent-source marker, grouped by reason and by area;
- `fully_read`, which is true only when strict mode accepts the file and no unresolved item remains.

An area is the feature, sketch or document collection at an item's path. SOLIDWORKS feature steps use their stored native type. Fusion native steps use the class name from `re/Fusion/Study/fusion-class-catalog.json`, or a class GUID prefix when the catalogue has no name.

The summary for each application gives the totals, the areas that block the most files, unresolved reasons, strict refusals, diagnostics and the features seen. For Fusion, it also compares read modes with `re/automation/FusionOutcomes.json`.

`ReaderEvidence.reader_evidence` accepts an optional keyword `limit` between 1 and 20,000,000 entries. The default is still 200,000, so the existing callers are unchanged. The scoreboard passes 10,000,000, because the pinned SOLIDWORKS assemblies need between 0.9 and 5.8 million entries.

## Usage

Run the command with Python 3.14 from the repository root. Use an output directory that does not exist yet.

```shell
uv run python re/automation/ReadScoreboard.py --output /tmp/KitReadScoreboard
```

Add `--asset PATH` one or more times to score only those pinned paths. Paths are compared after Unicode NFC normalisation. `--top` sets how many rows each Markdown table shows.

The command writes `Scoreboard.json` with every file row and `Scoreboard.md` with the summary tables.

## Limitations

- Byte ownership is not measured. The reader evidence reports `byte_accounting: unavailable`, so `fully_read` is not the plan's complete byte-ownership criterion.
- A fully read file is not semantic qualification, native acceptance or lossless conversion.
- The largest assembly, `Engine Assy KF EDIT 2.SLDASM`, needs about 2.7 GB of memory and 19 seconds.
- Fusion class names come from observed study semantics and can be incomplete.

## Verification

- `tests/Research/Census/ReadScoreboardTests.py` runs the command on a strict Fusion file, a partial Fusion file and a SOLIDWORKS part whose accented path is supplied in NFD form. It checks totals, read modes, area attribution, the SOLIDWORKS decode and the Markdown page. It also checks that a reused output directory and an unpinned path are refused. Both cases passed locally.
- All 64 pinned SOLIDWORKS files were read with the default limit. Only the four assemblies exceeded it, with or without tessellation. Measured entries: `ENSAMBLE 3_IZQUIERDO.SLDASM` 896,894; `Cylinder Head Assy 1.SLDASM` 958,093; `Turbo Assy KF.SLDASM` 1,230,790; `Engine Assy KF EDIT 2.SLDASM` 5,828,609.
- Scored alone with the raised limit, `ENSAMBLE 3_IZQUIERDO.SLDASM` decodes as a partial read.
- The F3Z package regression exercises the exact pinned archive through the scoreboard CLI and checks its archive refusal.
- The complete 778-file replay ran offline with CPython 3.14.6 at code commit `00d863b95a15b40efd999cadd71c4741bf650393` against corpus revision `74a0bc353421c25f7a6c539897baadf593a05766`.
  Fusion recorded 16 strict reads, 681 partial reads, 17 refusals, zero reader errors and 16 fully read files by the scoreboard definition.
  SOLIDWORKS recorded 61 strict reads, two partial reads, one refusal, zero reader errors and zero fully read files.
  Compared with `571fd114b58395a848d47e5256b62182f0826fec`, the other 777 per-file records matched after excluding elapsed time.
  The resulting `Scoreboard.json` SHA-256 is `bff4560823bb4f371e4dca80bc561b21ea54d0028a20b457a21a0e73368c754d`.
