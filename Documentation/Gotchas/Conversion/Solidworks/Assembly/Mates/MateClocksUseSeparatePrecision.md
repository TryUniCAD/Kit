# Mate clocks use separate precision

## Expectation

A document clock can supply every mate revision, including an independently authored native save.

## Actual behavior

The disclosed SOLIDWORKS 2026 SP05.2 A22 original contains three independent mate FILETIMEs. All three have nonzero 100 ns remainders. The corresponding `moStamp_c.f18` in each header stores only its mate's whole Unix seconds. Two mates share a whole second while keeping different feature FILETIMEs. Both native headers store a document modification field older than the mate events. [Typed comparison](../../../../../../re/solidworks/measurements/2026/SharedMateCreationClocks01.json)

## Workaround

Use the mate's authored creation event where the constructor supports it. Match the log's actual owner ID and name to the mate in the linked list. Keep document clocks independent. Fractional source events require a separately proved input representation before any claim of complete source-clock transfer. [Constructor and scope](../../../../../../re/solidworks/records/SharedMateCreationClocks2026.md)
