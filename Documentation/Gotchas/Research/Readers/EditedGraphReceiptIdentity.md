# Edited graph readers need the receipt identity

Generated edited-depth readers and file-driven graph receipts should produce identical JSON.
The original reconciliation result omitted `source_sha256`, while the file-driven report added it.
The full-output comparison therefore failed although the candidate document and updates matched.
See the [failed reader replay](https://github.com/TryUniCAD/Kit/actions/runs/44832321036/job/136620268798).

Reconciliation now computes the hash from the current input bytes.
Both output paths retain the input identity and the complete graph comparison.
