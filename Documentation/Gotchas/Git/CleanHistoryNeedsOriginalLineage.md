# Clean history needs original capture lineage

## Expectation

An automation-only copy with identical final files might appear to retain the capture audit's results automatically.

## Actual behavior

The intake derives receipt introductions from Git additions and verifies authoring-source ancestry. A new short history changes those introductions. The original historical corpus also names blobs that are absent from main's current tree. Copying receipts or rebinding their source revisions would misstate provenance.

The original capture authority remains `f5b23031c4163528a2e4f5029ab34102133b983e`. Its 130-file input roster has digest `ca44feca3f2ca32cd852f32e4afde2e5a2b334a8c83a150e813d8256f6c106b6`. The former incoming graph also contains vendor DLL additions, so merging that graph is not a compliant preservation mechanism.

## Workaround

Use the [sealed history binding](../../Changes/Research/Automation/CaptureHistoryBinding.md): acquire metadata and explicit permitted research inputs from the existing pinned source ref, compare current modes and blob IDs, audit original provenance on the original graph and check current global aliases separately. Preserve original receipt pins and blockers. Do not check out the old graph, copy vendor software, replace receipts or claim newly established native acceptance.
