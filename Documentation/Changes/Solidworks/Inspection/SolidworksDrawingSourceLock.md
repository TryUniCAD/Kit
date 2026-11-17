# SOLIDWORKS drawing source lock

The SOLIDWORKS 2026 research harness authors an empty single-sheet drawing and ordinary model views of a pinned single-body part. It verifies save, fresh reopen, rebuild, reference resolution and an in-memory view move, with independent native part controls before and after. It records source and tool hashes and keeps detailed measurements outside the checkout.

Run `AuthorDrawingSources.py` with the absolute path to a drawing source job. The job pins the installed template, reference part, independent control and case specification. The default discovery cases hold the orientation and scale constant while varying position. The oracle owner can add two sealed layouts using a private specification.

The CLI and discovery specification validate on macOS. The corrected source lock qualified all five cases in twelve fresh native processes with healthy controls and immutable inputs. Populated drawing cases passed the in-memory view move and rebuild check. This is a research source generator for one sheet and an ordinary part view. [Drawing archive discovery ledger](../../../../re/solidworks/records/DrawingArchiveDiscovery2026.md), [Source lock](../../../../re/solidworks/v2026/heldout/DrawingSourceLock01.json)
