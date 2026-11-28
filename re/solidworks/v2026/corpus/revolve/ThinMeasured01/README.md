# Disclosed thin revolve evidence

`DisclosedEvidence.json.gz` contains six exact UTF-8 JSON texts, grouped
into two independently authored model specs and their associated native
inspection jobs and terminal receipts. It contains research data only
and is never opened by the SDK writer. Its SHA-256 is
`f72de5faf4bc7f849dd0bc48443312700b06641d6cd06aa817f8249bac06edba`.
Each decompressed text has a separate pin. The bundle is unchanged from
Kit PR #247 revision `7fc0bcdc25b2a68427e86ec30e65a955fa5f2d41`.

The exact SOLIDWORKS 2026 SP05.2 build was `34.5.2.0604`. The Front
batch is `SdkThinGenerated01`. The Top and Right batch is
`SdkThinPlaneGenerated01`. Both contain disclosed discovery cases.
The complete-suite worker uses the unequal two-wall Front case and the
Right midplane case. A candidate is reconstructed from its authored
neutral model in each worker. The report binds the complete measured
candidate SHA-256. [Procedure and custody](../../../../records/AggregateMeasuredThin2026.md)
