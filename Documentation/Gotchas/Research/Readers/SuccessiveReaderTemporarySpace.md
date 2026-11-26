# Successive reader temporary space

Replaying multiple SOLIDWORKS reader proposals in parallel source copies exhausted temporary disk space in a local turbine-wheel run. A subprocess failure during strict decoding can also look like a rejected proposal if the caller ignores its exit diagnostics.

The run now copies the SDK into a private baseline once and links unchanged files from that baseline. It replaces the changed file in each candidate before decoding. Platforms without hard links use ordinary copies. Unexpected process exits propagate to the caller so the run can be retried after freeing space.
