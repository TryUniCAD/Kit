# Uninitialized Fusion reflection values can contain persisted fields

## Expectation

An uninitialized member set with no reflected members might indicate an empty value or require an opaque payload fallback.

## Actual behavior

`ProgenitorAuxDataValueMetaType`, GUID `BE7E2847-FBC4-4898-A6E7-632A559A7F89`, remained uninitialized in the captured version-zero reflection catalog. Its native lazy registration nevertheless declares one persisted member, `tag`, of type `unsigned int`. The value occupies four wire bytes even though the runtime object occupies 32 bytes.

This affected 38 named metadata values in the corpus: 36 sweep-face progenitor records and two entity progenitor records.

## Workaround and evidence

Recover the member declaration from lazy initialization code and the ordinary persistence option mask. Do not infer wire size from runtime allocation size, and do not treat an uninitialized schema as an empty schema. [The registration evidence](../../../../re/Fusion/Reconstruction/EntityGraph/ProgenitorEvidence.json) records the native addresses and types; [the corpus summary](../../../../re/Fusion/Reconstruction/CorpusSemantics/Summary.json) records complete subsequent consumption.
