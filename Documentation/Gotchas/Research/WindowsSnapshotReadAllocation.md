# Maximum-size buffered reads slow Windows source hashing

Expected: reading a small source file under a 256 MiB safety limit costs roughly its actual file size.

Observed: `stream.read(limit + 1)` spent most of its time in the buffered read when verification hashed thousands of small SDK files on Windows.
The [queue CLI job](https://github.com/TryUniCAD/Kit/actions/runs/44962146215/job/137023195551) failed three reader commands at their 300-second limits, despite all thirteen saved-prism controls passing quickly.
Profiling on the existing Windows host isolated buffered reads as the hot path.
For 100 reads, retaining the complete native snapshot checks but requesting the observed size plus one byte reduced elapsed time from 4.6743715 seconds to 0.0250773 seconds with identical bytes.

Bound the request by the verified file size plus one byte and keep the independent maximum-size and before/after identity checks.
Do not remove native snapshot validation or raise timeouts to conceal this cost.
Increasing pytest workers alone does not repair the per-command read allocation.
