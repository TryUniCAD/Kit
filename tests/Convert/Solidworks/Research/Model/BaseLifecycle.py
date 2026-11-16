from __future__ import annotations

# owner flag transitions need evidence because dirty state must remain separate from stamp allocation
KBaseLifecycle = """
BaseFlagTrace = [BaseGraph.part["f0c"]]
ClearModelUpdate(model=BaseGraph.part)
BaseFlagTrace.append(BaseGraph.part["f0c"])
MarkModelUpdate(model=BaseGraph.part)
BaseFlagTrace.append(BaseGraph.part["f0c"])
"""
