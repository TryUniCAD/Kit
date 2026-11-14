# Tracked part corpus coverage

## Behavior

`TestCorpus` opens every tracked `.SLDPRT` in the V8 example directory through the public
reader and writes each one with `allow_carrier=False`. Every part must report
`native-exact` compatibility, a self-contained result, application usability, and
near-lossless output. The case then reopens the written file and writes it a second time;
the second output must be byte-identical to the first, which proves the native streams are
stable across a read and rewrite.

The directory is tracked in the repository, so the case runs in CI without a local
SOLIDWORKS install, FreeCAD, or the absent `.rescratch` corpus.

## Usage

No option is required. The case is skipped when the tracked directory is absent, which
keeps partial checkouts working.

## Limitations

- the case proves the recovered part families round-trip; it does not prove arbitrary
  histories, drawings, or from-scratch mate generation
- the count is pinned to the 57 tracked parts, so adding or removing a tracked part
  requires updating the assertion
- SOLIDWORKS acceptance of these outputs is not re-run here; the earlier oracle evidence
  for the recovered families is recorded in the research records

## Verification

`tests/convert/solidworks/core/SolidworksCorpusTests.py` contains `TestCorpus`. A local
run over the same directory produced 57 of 57 parts with `native-exact` compatibility,
self-contained output, and a byte-identical second write in 19.4 seconds for the first
pass. The CI job `Exercise native file reading and writing` runs the case against the
tracked files.
