from enum import Enum


# local import history needs distinct system activation and local body attachment events
class ImportEvent(Enum):
    KActivation = "activation"
    KLocalAttach = "local attachment"
