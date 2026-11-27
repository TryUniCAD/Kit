# Replay retained vendor boss evidence from exact inputs

The [replay manifest](../../../../re/solidworks/measurements/2026/VendorBossCorpus/ReplayInputs.json)
pins a 34-file private archive. It contains the nine discovery CAD files and
their authoring definitions, the revealed body-proof holdout and its authoring
definition, the warmed PMI corpus and records, and the saved Kit presentation
contrast and its native records.

The exact native archives include local account and machine metadata. Their
independent retention copy is `D:/KitRuns/A12bResearchReplay20261125/VendorBossReplayInputs.zip`
on the acquisition host. The manifest and replay code are tracked. Exact
replay through another host requires access to the private bundle. All
future writing and annotation holdouts are outside the bundle.

## Replay

Use the retained bundle and the pinned dependency checkout recorded in the
[body evidence](../../../../re/solidworks/records/VendorBlindBossSourceAdmission.md).
Choose a fresh ignored output folder whose parent exists.

```powershell
python -B re/solidworks/EncoderBoundary/ReadVendorBossReplay.py `
  --manifest re/solidworks/measurements/2026/VendorBossCorpus/ReplayInputs.json `
  --bundle $privateBundle --output .rescratch/VendorBossReplayInputs

python -B re/solidworks/EncoderBoundary/InspectVendorBodyOwners.py `
  --dependency-root $pinnedPr121Checkout `
  --source-record .rescratch/VendorBossReplayInputs/Author04/Record.json `
  --source-record .rescratch/VendorBossReplayInputs/Discovery01/Author/Record.json `
  --output .rescratch/VendorBossDiscoveryReplay.json

python -B re/solidworks/EncoderBoundary/InspectVendorBodyOwners.py `
  --dependency-root $pinnedPr121Checkout `
  --source-record .rescratch/VendorBossReplayInputs/BodyHeldout/Author/Record.json `
  --output .rescratch/VendorBossHeldoutReplay.json
```

The four-case census also accepts the unpacked `Author04` directory. The
[PMI verifier](VendorBossPmiReadback.md) accepts the unpacked `Discovery02`
directory. The producer's SDK and observation digests remain the originals.

## Verification

The unpacker verifies the bundle digest, complete member inventory, byte
counts and member digests before creating the destination. It verified and
unpacked all 34 original files. A one-byte change to the bundle returned
exit code 3 before output creation. The nine-case body report and the
held-out body report reproduced their original SHA-256 digests from the
unpacked files. All five PMI annotation values matched again. These replays
launched no native CAD process.
