from math import isfinite as IsFinite
from struct import Struct

from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderWords

# the optional box is framed by a native unsigned presence word
KBoundsPresence = KHeaderWords["I"]

# absent bounds do not consume a numeric payload
KBoundsAbsent = 0

# present bounds carry the complete numeric payload
KBoundsPresent = 1

# the final scalar is an independent sphere radius
KBoundsRadiusIndex = 9

# centre and extrema precede the radius in the native box
KBoundsCount = KBoundsRadiusIndex + 1

# both directions use the same number and width of little endian scalars
KHeaderBox = Struct(f"<{KBoundsCount}d")


# both read and write reject nonfinite bounds before exposing geometry
def HasFiniteBounds(Values: tuple[object, ...]) -> bool:
    return len(Values) == KBoundsCount and all(
        isinstance(Value, (int, float)) and IsFinite(Value) for Value in Values
    )
