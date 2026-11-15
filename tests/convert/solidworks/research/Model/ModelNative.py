from __future__ import annotations

# native codecs need explicit imports because this boundary must exercise the shared serializer
KNative = """
from codecs import lookup as FindCodec
from Core import Obj as NativeObj
from Classes import registry as NewRegistry
from Streams import StreamDoc, store_rooted as StoreRooted, load_rooted as LoadRooted
"""
