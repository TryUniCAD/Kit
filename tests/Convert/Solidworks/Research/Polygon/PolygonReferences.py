from __future__ import annotations

# graph links must survive decoding beyond merely matching numeric field values
KRefs = """
PointRefs = []
for Index, Entry in enumerate(Sketch['points']):
    Point = Entry['point']
    First = Point['h1']['idx'] if Point['h1']['idx'] < 0x777f else Point['h1']['f18']
    Second = Point['h2']['idx'] if Point['h2']['idx'] < 0x777f else Point['h2']['f18']
    Expected = (0, len(Vertices) - 1) if Index == 0 else (Index - 1, Index)
    PointRefs.append((First, Second) == Expected and Point['fe8'] == 2)
LineRefs = []
for Index, Entry in enumerate(Sketch['lines']):
    Line = Entry['line']
    Start = Line['fc8_s'] if Line['fc8_s'] < 0xffff else Line['fc8']
    Finish = Line['fcc_s'] if Line['fcc_s'] < 0xffff else Line['fcc']
    LineRefs.append((Start, Finish) == (Index, (Index + 1) % len(Vertices)))
"""
