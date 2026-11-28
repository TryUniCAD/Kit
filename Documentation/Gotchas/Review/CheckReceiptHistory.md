# Same-name checks hide earlier request receipts

Review request receipts need to remain visible after another check with the same name is published.
GitHub's check-run listing defaults to `filter=latest`, which hides older same-name checks.
Reading only that view can repeat previously handled mention requests.

Receipt discovery uses `filter=all`, app and check-name filters, and pagination.
It refuses inventories beyond its configured bound instead of treating an incomplete inventory as unhandled.
GitHub retains at most 1,000 same-name checks per check suite, so receipts depend on retained check history.
See [GitHub's check-run API](https://docs.github.com/en/rest/checks/runs#list-check-runs-for-a-git-reference).
