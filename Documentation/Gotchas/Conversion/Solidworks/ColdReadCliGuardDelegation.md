# Cold part qualification differs from generic portable qualification

Expected: the same measured cold SOLIDWORKS part accepted by the SDK can pass ordinary CLI conversion with the same exact measurement.

Observed: the CLI rejected `NativeFeature`, then retained source metadata, before reaching the already-qualified writer. Both measured Skew and Step parts reproduced the difference. Exempting only the first native-feature check left the retained-metadata refusal intact.

The CLI delegates only the actual SOLIDWORKS part writer plus typed cold-read identity to its complete regenerated-document comparison and exact measured-output gate. A cold identity marker alone does not authorize publication. Other writer routes retain generic opaque-record and retained-byte refusals; never strip the source state or weaken its writer comparison to obtain parity.

[Change and process verification](../../../Changes/Commands/Parts/SolidworksColdReadParity.md)
