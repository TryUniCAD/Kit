# Pull-request base branch tip

A pull-request response's `base.sha` can lag the current base branch ref during concurrent work. Comparing only that snapshot can make a real merge conflict appear contradictory.

During [PR #123](https://github.com/TryUniCAD/Kit/pull/123), head `6ce028b3f15777d94983542fb267a450210bc5d7` included the API-reported base `df1158d58ca7b8a67cef1f10528709dd2ca098a0` as an ancestor, while GitHub reported the PR as dirty. The remote branch ref had already advanced to `e34bd010e28429bc43e9e9d5a0e5fc5d42c73513`. Fetching that actual tip exposed two documentation conflicts. Merging it and preserving both sides restored mergeability at head `22a78891631498e176274289b2cafb00abc6b764`.

Resolve the base branch's current ref as well as the PR snapshot. Fetch and inspect the current tip, merge base and conflicts before interpreting an ancestor check or claiming readiness. A compare result against the older snapshot does not establish compatibility with the current target.
