from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat


# a verified difference between two readable assembly owners is a format error
class IndexConflict(SldprtFormat):
    KSlots = ()
