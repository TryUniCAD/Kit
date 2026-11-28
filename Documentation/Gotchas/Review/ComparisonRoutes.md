# GitHub comparison routes contain three dots

The API route guard rejected any `..` sequence to prevent traversal.
GitHub's commit comparison endpoint requires `BASE...HEAD`, so the same guard rejected valid merge-base lookup.
Live preparation exposed the error when selecting an old stacked PR.

Allow only the comparison segment containing two exact 40-character lowercase commit hashes before applying the traversal check.
Keep the traversal rejection for every other segment.
The source collector uses the resulting merge base without checking out or executing PR code.
