# Part header counters skip reserved persistent IDs

The persistent allocator's last assigned ID can be followed by one or
more reservations. The next Header ID follows the same reservation
walk as the next allocation. An authored graph ending at ID 7 with
8 and 9 reserved publishes 10 in both Header streams. Its next
allocation returns 10 and its separate manager directory stays exact.
If no allocatable ID remains in the signed domain, construction refuses
before writing a Header.
[Guarded process evidence](../../../../../../re/solidworks/records/FreshPartHeaders2026.md)
