# Future body loading has its own context gate

**Expectation:** a positively bound part partition loader can be used as the ordinary cold-open entry without resolving its caller's context predicate.

**Actual behavior:** `moModel_c::loadFutureModelBodies` requires actual context virtual `+0xa20`, bound through the base/model-document context tables to `getIsFutureVersionDocument`. Ordinary `SolidStorage::LoadModel` instead calls `moPart::loadExternalBodies` under its not-future branch. That path reaches context `+0x540` and storage `+0x500` before kernel receive and feature/atom publication.

**Workaround:** preserve both actual receiver identities and all caller guards. Use the ordinary path to diagnose ordinary files, and retain its still-unmeasured stream, receive, active-mark and publication outcomes. A decoded partition, a matching virtual displacement on another class or a successful explicit rebuild cannot establish that initial path succeeded. [Original-image evidence](../../../../../../re/solidworks/records/OrdinaryPartPartitionLoad2026.md)
