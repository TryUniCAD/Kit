# A split test can inherit an obsolete license declaration

The repository LICENSE and contribution policy specify MIT.
A transport test split from an older compiler test initially copied its PolyForm header.
That copied header conflicts with the governing project license.
The steering checker accepts only the complete historical header when it encounters that comment block.
A shortened SPDX block also fails its comment policy.

The new focused test inherits the repository MIT license without adding the obsolete per-file declaration.
The original source notice, root LICENSE, copyright attribution and third-party notices remain intact.
Do not copy a legacy license declaration merely to satisfy the comment checker.
