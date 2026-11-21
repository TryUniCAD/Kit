from collections.abc import Callable
from typing import TypeAlias

from convert.adapters.solidworks.Drawing.Definition.FieldScope import FieldScope

# the native read grammar contains immutable class branch and field descriptions
KRuleShape: TypeAlias = tuple[object, ...]


# nested reader callbacks keep the same cursor map and independent condition scope
KRuleRunner: TypeAlias = Callable[[FieldScope, KRuleShape], None]
