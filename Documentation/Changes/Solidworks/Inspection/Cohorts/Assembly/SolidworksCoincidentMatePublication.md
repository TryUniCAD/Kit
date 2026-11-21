# Map coincident mate registration and stream owners

SOLIDWORKS registers the ordinary coincident mate under the actual mate
group and allocates one feature ID. Its separate mate-list stream
inherits the resolved archive map. The two document headers record the
same-ID creation log and the active configuration tracks ID progress.
The resolved plane wrappers consume a separate assembly-wide counter
which the model persists in Config-0.

The traced assembly load, store and registration functions come from
build 34.5.2.0604. The disclosed A17 archive corroborates the stream owners
and allocator values. The saved feature flag transition and native
qualification of generated mates remain open.

[Registration and wire proof](../../../../../../re/solidworks/records/CoincidentMatePublication2026.md)
