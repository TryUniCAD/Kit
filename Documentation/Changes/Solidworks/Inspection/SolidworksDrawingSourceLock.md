# SOLIDWORKS drawing source lock

The SOLIDWORKS 2026 research harness authors an empty single-sheet drawing and ordinary model views of a pinned single-body part. It verifies save, fresh reopen, rebuild, reference resolution and an in-memory view move, with independent native part controls before and after. It records source and tool hashes and keeps detailed measurements outside the checkout.

Run `AuthorDrawingSources.py` with the absolute path to a drawing source job. The job pins the installed template, reference part, independent control and case specification. The default discovery cases hold the orientation and scale constant while varying position. The oracle owner can add two sealed layouts using a private specification.

The CLI and discovery specification validate on macOS. Native qualification awaits the pinned Windows oracle. This is a research source generator for one sheet and an ordinary part view. The [drawing archive discovery ledger](../../../../re/solidworks/records/DrawingArchiveDiscovery2026.md) records usage, native boundaries and qualification work.
