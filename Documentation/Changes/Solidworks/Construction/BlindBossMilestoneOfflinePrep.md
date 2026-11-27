# Offline preparation for the editable blind-boss milestone

This change adds offline preparation and integration verification for the
first SOLIDWORKS reader/writer milestone (items 2, 3, 7, and the offline half
of item 5) using the committed 40 x 20 x 10 mm rectangular blind-boss control
`re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT`.

## Behavior

- `re/tooling/sw2026/PrepareBlindBossMilestone.py` decodes the committed
  baseline part with `open_document`, verifies its body count, volume
  (`8000.0 mm^3`), centroid (`[20.0, 10.0, 5.0] mm`), configuration, and
  driving parameters against `measurements.json`, and projects the loop onto
  the neutral bounded-part model.
- It calls `PreparePlainPartEvidence.py` (`PrepareNative`) with
  `runtime_input_reads == 0` to generate both the 10 mm baseline candidate
  (`P03RectBoss10mm.SLDPRT`) and the 15 mm depth-edited candidate
  (`P03RectBoss15mm.SLDPRT`), recording exact archive, stream, neutral, and
  manifest SHA-256 digests in `MilestoneManifest.json`.
- Both generated candidates round-trip through `open_document(..., strict=True)`
  and cold-read `PrepareNative` with exact byte identity, preserving `D1`
  (`10.0 mm` -> `15.0 mm`), the 4-line closed Front-plane loop, and the
  `+4000.0 mm^3` volume delta (`8000.0 mm^3` -> `12000.0 mm^3`).
- `tests/Convert/Solidworks/PlainWriting/BlindBossMilestoneTests.py` verifies
  `kit decode` against the inventory, candidate preparation and round-trip,
  SDK vs CLI byte parity against `PlainPartWindowsCliParity01.json`, and
  `tools/Donors/CheckReplays.py src`.

## Usage

```sh
.venv/bin/python re/tooling/sw2026/PrepareBlindBossMilestone.py --scratch /tmp/BlindBossMilestone
```

## Limitations

This change covers only the offline half of Milestone 1. Live SOLIDWORKS 2026
open, rebuild, in-app depth edit, save/reopen, bracketing control checks, and
receipt-backed SDK/CLI publication of the new candidates still require a
Windows SOLIDWORKS worker.

## Verification

- `pytest tests/Convert/Solidworks/PlainWriting/ -q`
- `PYTHONPATH=. .venv/bin/python tools/Donors/CheckReplays.py src`
- `pyright`, `mypy`, and `ruff check` on `tests/Convert/Solidworks/PlainWriting/`
