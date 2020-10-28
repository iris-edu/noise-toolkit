import os,sys,math
import numpy as np

#
# compute complex amplitude
#
def cAmp(c):
   #return np.sqrt(c.real*c.real + c.imag*c.imag)
   return np.abs(c)

#
# compute complex phase
#
def cPhase(c):
   #print ">>>>"+str(c)
   if(np.sqrt(c.real*c.real + c.imag*c.imag)<1.0e-6):
      return(0.0)

   if(np.abs(c.real)<1.0e-6):
      if(c.imag>0.0):
          phs=math.pi/2.0;
      else:
          phs=3.0*math.pi/2.0;
   else:
      phs=math.atan2(c.imag,c.real)

   if(phs<-math.pi):
      phs+=2.0*math.pi
   elif(phs>math.pi):
      phs-=2.0*math.pi

   return(phs);

