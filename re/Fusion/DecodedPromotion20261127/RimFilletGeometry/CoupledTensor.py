from convert.adapters.Fusion.Native.Circular.RotaryMass import CacheNumbers
from convert.adapters.Fusion.Native.Graph.GraphValues import ObjectFields,PointCoords,NumberValue


def central(volume,center,diagonal,cross):
    return (tuple(diagonal[i]-volume*sum(center[j]**2 for j in range(3) if j!=i) for i in range(3)),tuple(value+volume*center[a]*center[b] for value,(a,b) in zip(cross,((0,1),(0,2),(1,2)),strict=True)))


def check_tensor(cache,volume,area,center,diagonal,cross):
    actual_v=NumberValue(cache['volume']);actual_c=PointCoords(cache['cog']);actual_d=PointCoords(cache['moi']);actual_x=PointCoords(cache['moiOffDiag'])
    CacheNumbers((actual_v,NumberValue(cache['area'])),(volume,area));CacheNumbers(actual_c,center)
    actual=central(actual_v,actual_c,actual_d,actual_x);expected=central(volume,center,diagonal,cross)
    CacheNumbers(actual[0],expected[0]);CacheNumbers(actual[1],expected[1])
    return dict(actual_central=actual,expected_central=expected,central_cross_errors=[a-b for a,b in zip(actual[1],expected[1],strict=True)])
