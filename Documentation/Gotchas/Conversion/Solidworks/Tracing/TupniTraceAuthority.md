# API hook logs do not establish instruction-level taint

## Expectation

Logging native archive reads provides the complete input dependency information
needed to apply Tupni automatically.

## Actual behavior

An archive API hook can observe calls, input cursor movement and native call
sites. It does not observe every instruction that later uses a decoded value.
It therefore cannot alone recover all branch predicates, nested loop structure
or symbolic field dependencies. A Python codec log has an additional limit: it
observes Kit's implemented schema rather than the vendor parser.

## Workaround

Label each capture by its actual authority, preserve missing information and
combine bounded native traces with explicit static dataflow. Add instruction
provenance only when a supporting engine captured it. For compressed streams,
use a decompressed input identity and retain refill-aware logical offsets.
Keep clean vendor acceptance separate from instrumented research. See the
[playbook](../../../../../re/Playbook/Tupni.md) and its first-use ledger.
