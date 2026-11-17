# Construct the ordinary self record for a generated child part

The SOLIDWORKS 2026 research part builder accepts an optional `output`
mapping with `path_name` and a Unix `saved_at` value. It constructs a
part's own file record from its generated model, active configuration,
creation time and explicit save event. Both file headers serialize the
record. The configuration archive registers its actual header object.
The builder also emits `Contents/CMgrHdr2` from the actual configuration
manager, the active part configuration, and the supplied save event.

The part and assembly builders share the file-record construction rule.
The guarded part process builds and reads back a four-edge boss with
different model and output names. It checks both headers, archive slot
3, the lightweight manager's save event and stamps, all part stream round
trips and the runtime read boundary. Seven targeted process cases passed
locally. Vendor results are pending.

The [child timestamp trace](../../../../../../re/solidworks/records/AssemblyConstruction2026.md#child-directory-timestamp-sources)
explains how a parent can use both records. Populated parent construction
remains in development.
