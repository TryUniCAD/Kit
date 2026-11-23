# Provider cancellation waits for the acknowledged turn

The Windows hosted transport probe starts a fresh provider process and
waits for the client to receive the `turn/start` acknowledgement before
cancelling. A separate five-second timer covered process startup, model
discovery, thread creation and the acknowledgement. The request still
had time remaining when the probe failed on the hosted platform shard.
[Hosted failure](https://github.com/TryUniCAD/Kit/actions/runs/45088096048/job/137411458356)

Derive the acknowledgement deadline from the same ten seconds supplied
to the generation call. Close the session only after the actual turn
acknowledgement. The existing status, owned-process cleanup and total
elapsed assertions still run.
