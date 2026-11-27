from math import pi


def rim_mass(radius,height,fillet):
    if not 0<fillet<min(radius,height): raise ValueError('Rim dimensions outside qualified domain')
    a=radius-fillet;z=height-fillet;f=fillet;r=radius
    j0=a*a*f+pi*a*f*f/2+2*f**3/3
    j1=a*a*f*f/2+2*a*f**3/3+f**4/4
    j2=a*a*f**3/3+pi*a*f**4/8+2*f**5/15
    j4=a**4*f+pi*a**3*f*f+4*a*a*f**3+3*pi*a*f**4/4+8*f**5/15
    volume=pi*(r*r*z+j0);mz=pi*(r*r*z*z/2+z*j0+j1)
    qx=pi*(r**4*z+j4)/4;qz=pi*(r*r*z**3/3+z*z*j0+2*z*j1+j2)
    return dict(volume=volume,area=pi*r*r+2*pi*r*z+pi*a*a+pi*pi*a*f+2*pi*f*f,centroid=(0.,0.,mz/volume),moi=(qx+qz,qx+qz,2*qx),cross=(0.,0.,0.),lower=(-r,-r,0.),upper=(r,r,height))
