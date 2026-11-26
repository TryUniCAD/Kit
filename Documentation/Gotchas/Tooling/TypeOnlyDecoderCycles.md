# Type-only decoder imports can fail CodeQL

A `TYPE_CHECKING` guard avoids a runtime import, but the queue CodeQL analysis can still report the decoder dependency cycle.
The failed PR 204 candidate reported eight cyclic imports across count readers and the native decoder.
See the [failed Python analysis](https://github.com/TryUniCAD/Kit/actions/runs/44832321126/job/136620060432).

Keep shared record definitions in modules that do not import their consumers.
Import those definitions directly from the reader and decoder.
Do not suppress the cycle or disable the analysis.
