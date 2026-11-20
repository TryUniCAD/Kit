# The archived research tree already contains its preparer

The same-locator width-to-depth packet extracts the research subtree
from an explicit Git object. That subtree already contains the
preparer in its original directory. An exclusive copy from the live
checkout collides with the extracted path and can break the exact
revision binding.

Invoke the extracted preparer from the frozen tree. The host
orchestrator supplies the nominated revision and the explicit
creation event for the SDK recipe.

[Frozen packet preparer](../../../../../../re/tooling/sw2026/equations/PrepareWidthDepthSameLocator.py)
