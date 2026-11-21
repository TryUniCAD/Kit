# External reference list index and configuration ID are different owners

The ordinary `moExtObject_c.f78` value can resemble an active configuration ID. Exact exported accessors identify it as `IndexInRefList` instead.

A fresh object starts at `-1`. The actual external-object list starts its maximum at `-1`; insertion calls `setExtObjToIndex`, allocating the next maximum only for an unindexed object. Reused indexed objects retain their value. The first new entry is therefore 0 only in a fresh list.

The name and ID of the referenced configuration are separate embedded state at runtime `+0x18`. The local `createExtObject` path updates them from the actual selected configuration when partition rollback is enabled. The pinned selected backend constructor defaults rollback enabled, but the runtime setting can be changed.

Derive the list index from actual modeled list state and derive the configuration pair from its separate owner and condition. Do not transplant the header self-file role's counters/save epoch or conflate list index 0 with config ID 0.

The [source record](../../../../../../re/solidworks/records/DownstreamLocalOwnerContext2026.md) binds the constructors, call chain, list setter, configuration setter and current serializer; the [receipt](../../../../../../re/solidworks/measurements/2026/DownstreamLocalOwnerSource01.json) is source-only.
