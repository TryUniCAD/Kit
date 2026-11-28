# Verify the PMI value for a vendor-saved SOLIDWORKS boss

The [verification command](../../../../re/solidworks/EncoderBoundary/VerifyVendorBossPmi.py)
checks the single PMI annotation in each warmed source from the
[vendor boss corpus](VendorBossCorpusContrasts.md). It verifies the source
archive and fresh native observation digests, then compares the full PMI
value with the typed driver and its native component reference. The command
reads the archive and observations in place and returns their hashes with
each result.

```powershell
python -B re/solidworks/EncoderBoundary/VerifyVendorBossPmi.py `
  --index re/solidworks/measurements/2026/VendorBossCorpus/SourceContrasts.json `
  --capture $warmedCapture
```

Use the retained `Discovery02` folder for `$warmedCapture`. It contains the
original `Author` archives and the fresh reopen records. The verifier applies
the measured full-reference grammar to `D1@Boss-Extrude1` in `Prism.SLDPRT`.
It returns exit code 3 for inconsistent source, scope, or native evidence.
This command verifies source annotation values. It adds no production reader
or writer support.

All five values reproduced byte-for-byte with Python 3.14.6. Four values
contained the 13.371 mm driver and the independent depth contrast contained
21.463 mm. An index that substituted the rounded 21.46 mm value was refused
with exit code 3. A separate read-only UnQLite cursor independently opened the
three embedded databases in all five files, with no change to any input.
The [PMI evidence](../../../../re/solidworks/records/VendorBlindBossAdmission2026.md#pmi-and-exchange-records)
and [full-reference gotcha](../../../Gotchas/Conversion/Solidworks/Archive/Metadata/WarmedBossPmiCanKeepFullReference.md)
record the measured source boundary.
