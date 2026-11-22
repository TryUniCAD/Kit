# A distance-cut schema does not evaluate retained geometry

A valid DistanceCut definition checks owned extent parameters and target history. It does not prove that a stored B-rep reflects those controls. Removing the source read-only marker or editing a live distance must therefore never grant an application-usable export attestation.

The [review finding](https://github.com/TryUniCAD/Kit/pull/241#discussion_r4658676225) identified that gap in generic JSON export. Shared and direct writer checks now reject the type until its geometry evaluator is qualified; the public file helper rejects it independently of metadata. Complete raw JSON remains available for inspection. A public compatibility replay changes the cut distance, round-trips neutral JSON, and checks that streams and existing files remain unchanged, including nested documents and disabled optional validation. The replay awaits remote execution.
