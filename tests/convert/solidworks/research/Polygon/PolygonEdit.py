from __future__ import annotations

KEdit = """
Parameters[0]['f58'] = Depth * 1.75
EditedStore = Store(registry=Registry, version=19000, ctx=Context)
EditedStore.obj(End)
EditedLoad = Load(bytes(EditedStore.out), registry=Registry, version=19000, ctx=Context)
Edited = EditedLoad.obj()
"""
