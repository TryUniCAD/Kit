# Duplicate patches consume the source context budget

A pull request can fit both file-count and per-source limits while redundant diff text makes the encoded context exceed its total budget. The earlier collector then discarded the current file's before, after and target snapshots even when all complete source text would fit without patches.

At PR #225 head `c6c80926e1666229844a02bdba38221557372b50`, 39 complete sources and the pinned policy required 763,020 encoded bytes without duplicate patches, compared with 922,939 bytes with them. This is a measured input snapshot, not a claim that every later revision fits.

The collector now drops only duplicate patch text before applying source-budget omissions. Every source snapshot stays unchanged. The forty-file limit, per-source size and binary checks, complete-review requirement and native approval gate remain active. Larger or unverified contexts still need separate work.

[Source budget change](../../Changes/Review/CompleteSourceBudget.md)
