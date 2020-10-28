from   obspy.core import UTCDateTime, read
import numpy as np
import math,copy

def getBin(X,Y,Xc,octaveHalfWindow):
   #
   ##########################################################################
   # gather Y values that fall within octaveHalfWindow  on either side of the
   # centeral X value 
   # 
   # HISTORY:
   #    2015-04-07  Manoch: Corrected the instrument correction for SAC files that would
   #                        apply sensitivity in addition to instrument correction
   #    2014-02-07 Manoch: created
   # 
   ##########################################################################
   # 
   thisBin = []
   shift = math.pow(2.0,octaveHalfWindow)

   #
   # the bin is octaveHalfWindow around Xc
   #
   X1 = Xc / shift
   X2 = Xc * shift
   Xs = min(X1,X2)
   Xe = max(X1,X2)

   #
   # gather the values that fall within the range >=Xs and <= Xe
   #
   for i in xrange(0,len(X)):
      if X[i] >= Xs and X[i] <= Xe:
         thisBin.append(float(Y[i]))
   return thisBin

def smoothNyquist(type,Xi,Yi,samplingRate,octaveWindowWidth,octaveWindowShift,xLimit):
   #
   ##########################################################################
   # smooth the Yi in the Xi domain
   #
   # smoothing is based on McNamara (2005)
   #
   # the Y at the extract Xi is taken as average of all Yi points within
   # octaveWindowWidth/2 on either side of Xi.
   #
   # we want the first sample to be at the Nyquist
   #
   # w  = octaveWindowWidth <-- full window width
   # hw = 0.5 * octaveWindowWidth <-- half window width
   #
   # HISTORY:
   #    2014-02-07 Manoch: created
   # 
   #
   ##########################################################################
   # 
   X  = []
   Y  = []

   #
   # shortest period (highest frequency) center of the window
   # starts  at the Nyquist
   #
   windowWidth = octaveWindowWidth
   halfWindow  = float(windowWidth / 2.0)
   windowShift = octaveWindowShift 
   shift       = math.pow(2.0,windowShift)        # shift of each Fc

   #
   # the first center X at the Nyquist
   #
   if type == "frequency":
      Xc       = float(samplingRate) / float(2.0) # Nyquist frequency
   else:
      Xc       = float(2.0) /float(samplingRate)  # Nyquist period

   while (True):
      #
      # do not go below the minimum frequency
      # do not go above the maximum period
      #
      if (type == "frequency" and Xc < xLimit) or (type == "period" and Xc > xLimit):
         break

      thisBin = getBin(Xi,Yi,Xc,halfWindow)

      #
      # bin should not be empty
      #
      if (len(thisBin) > 0):
         Y.append(np.mean(thisBin))
         X.append(Xc)
      else:
         Y.append(float('NAN'))
         X.append(Xc)

      #
      # move the center frequency to the right by half of the windowWidth
      # move the center period to the left by half of the windowWidth
      #
      if type == "frequency":
        Xc /= shift
      else:
        Xc *= shift

   #
   # sort on X and return
   #
   X,Y = (list(t) for t in zip(*sorted(zip(X,Y))))
   return (X,Y)

def smoothF (frequency,power,samplingRate,octaveWindowWidth,octaveWindowShift,minFrequency,xStart):
   #
   ##########################################################################
   # smooth the spectra in the frequency domain
   #
   # To make the output independent of sample rate, the multiples are always with 
   # respect to XStart defined by user and not the Nyquist frequency
   #
   # HISTORY:
   #    2014-02-07 Manoch: created
   # 
   #
   ##########################################################################
   # 
   F     = [] # <-- frequency container
   P     = [] # <-- power container

   #
   # sort on frequency
   #
   frequency,power = (list(t) for t in zip(*sorted(zip(frequency,power))))

   halfWindow    = float(octaveWindowWidth / 2.0)
   windowShift   = octaveWindowShift

   #
   # maximum frequency at the Nyquist
   #
   maxFrequency = float(samplingRate) / 2.0

   #
   # xStart is set by user so that output remains independent of sample rate, the multiples are always with 
   # respect to xStart
   #
   Fc = xStart

   #
   # do the lower frequencies (<= xStart & >= minFrequency)
   #
   shift = math.pow(2.0,windowShift)
   while Fc >= minFrequency:

      thisBin = getBin(frequency,power,Fc,halfWindow)

      #
      # bin should not be empty
      #
      if (len(thisBin) > 0):
         P.append(np.mean(thisBin))
         F.append(Fc)
      else:
         P.append(float('NAN'))
         F.append(Fc)

      #
      # move the center frequency to the left by half of the windowWidth
      #
      Fc /= shift

   #
   # do higher frequencies (> xStart & <= Nyquist)
   #
   Fc = xStart * shift

   while Fc <= maxFrequency:

      thisBin = getBin(frequency,power,Fc,halfWindow)

      #
      # bin should not be empty
      #
      if (len(thisBin) > 0):
         P.append(np.mean(thisBin))
         F.append(Fc)
      else:
         P.append(float('NAN'))
         F.append(Fc)

      #
      # move the center frequency to the right by half of the windowWidth
      #
      Fc *= shift

   #
   # sort on frequency and return
   #
   F,P = (list(t) for t in zip(*sorted(zip(F,P))))
   return (F,P)

def smoothAngleF (frequency,power,samplingRate,octaveWindowWidth,octaveWindowShift,minFrequency,rotation):
   #
   ##########################################################################
   # smooth the spectra in the frequency domain for angular quantities
   #
   # smoothing is based on McNamara (2005) but with smaller window 
   # length for better resolution and done in the frequency domain
   #
   # The optimum sampling window appears to be 1/4 octave (dB value at 
   # extract frequency taken as average of all points 1/8 octave either side).
   #
   # The highest frequency center of the window is at the Nyquist frequency
   #
   # To make the output independent of sample rate, the multiples are always with 
   # respect to a period of 1.0 seconds
   #
   # w  = octaveWindowWidth       <-- full window width
   # hw = 0.5 * octaveWindowWidth <-- half window width
   # Fc <= samplingFrequency/2.0   <-- the last sample at the Nyquist frequency
   # Fe = Fc * 2^hw               <-- center frequency is 1/2 window width away from the end
   # Fs = Fc / 2^hw
   # Fe = Fs * (2^w)
   #
   # rotation tells the function how the angles are measure, 0 from horizontal
   #          and 90 from vertical. This should not make much difference but
   #          wanted to be consistent in our calculations
   #
   # HISTORY:
   #    2014-02-07 Manoch: created
   # 
   #
   ##########################################################################
   # 
   F     = [] # <-- frequency container
   P     = [] # <-- power container

   #
   # sort on frequency
   #
   frequency,power = (list(t) for t in zip(*sorted(zip(frequency,power))))

   halfWindow    = float(octaveWindowWidth / 2.0)
   windowShift   = octaveWindowShift

   #
   # maximum frequency at the Nyquist
   #
   maxFrequency = float(samplingRate) / 2.0

   #
   # To make the output independent of sample rate, the multiples are always with 
   # respect to a period of 1.0 seconds
   #
   Fc = 1.0

   #
   # do the lower frequencies (<= 1.0 & >= minFrequency)
   #
   shift = math.pow(2.0,windowShift)
   while Fc >= minFrequency:

      thisBin = getBin(frequency,power,Fc,halfWindow)

      #
      # bin should not be empty
      #
      if (len(thisBin) > 0):
         #
         # place the points on a unit circle and find the mean of components
         #
         sumSin = 0
         sumCos = 0
         for i in xrange(0,len(thisBin)):
            rotated = rotation - thisBin[i] 
            sumSin += math.sin(rotated*math.pi/180.0)
            sumCos += math.cos(rotated*math.pi/180.0)

         meanSin = float(sumSin)/float(len(thisBin))
         meanCos = float(sumCos)/float(len(thisBin))

         #
         # The point of atan2() is that the signs of both inputs are known to it, so it can compute 
         # the correct quadrant for the angle. For example, atan(1) and atan2(1, 1) are both pi/4, but atan2(-1, -1) is -3*pi/4.
         #
         P.append(rotation -(math.atan2(meanSin,meanCos)*180.0/math.pi))
         F.append(Fc)
      else:
         P.append(float('NAN'))
         F.append(Fc)

      #
      # move the center frequency to the left by half of the windowWidth
      #
      Fc /= shift

   #
   # do higher frequencies (> 1.0 & <= Nyquist)
   #
   Fc = 1.0 * shift

   while Fc <= maxFrequency:

      thisBin = getBin(frequency,power,Fc,halfWindow)

      #
      # bin should not be empty
      #
      if (len(thisBin) > 0):
         #
         # place the points on a unit circle and find the mean of components
         #
         sumSin = 0
         sumCos = 0
         for i in xrange(0,len(thisBin)):
            rotated = rotation - thisBin[i] 
            sumSin += math.sin(rotated*math.pi/180.0)
            sumCos += math.cos(rotated*math.pi/180.0)

         meanSin = float(sumSin)/float(len(thisBin))
         meanCos = float(sumCos)/float(len(thisBin))

         #
         # The point of atan2() is that the signs of both inputs are known to it, so it can compute 
         # the correct quadrant for the angle. For example, atan(1) and atan2(1, 1) are both pi/4, but atan2(-1, -1) is -3*pi/4.
         #
         P.append(rotation -(math.atan2(meanSin,meanCos)*180.0/math.pi))
         F.append(Fc)
      else:
         P.append(float('NAN'))
         F.append(Fc)

      #
      # move the center frequency to the right by half of the windowWidth
      #
      Fc *= shift

   #
   # sort on frequency and return
   #
   F,P = (list(t) for t in zip(*sorted(zip(F,P))))
   return (F,P)
         
def smoothT(period,power,samplingRate,octaveWindowWidth,octaveWindowShift,maxPeriod,pStart):
   #
   ##########################################################################
   # smooth the spectra in the period domain
   #
   # To make the output independent of sample rate, the multiples are always with 
   # respect to pStart period defined by user
   #
   # HISTORY:
   #    2014-02-07 Manoch: created
   # 
   #
   ##########################################################################
   # 
   T     = [] # <-- period container
   P     = [] # <-- power container

   #
   # sort on period
   #
   period,power = (list(t) for t in zip(*sorted(zip(period,power))))

   halfWindow    = float(octaveWindowWidth / 2.0)
   windowShift   = octaveWindowShift

   #
   # minimum period at the Nyquist
   #
   minPeriod = 2.0 / float(samplingRate)

   #
   # To make the output independent of sample rate, the multiples are always with 
   # respect to period pStart set by user
   #
   Tc = pStart

   #
   # do lower periods (<= pStart & >= minPeriod)
   #
   shift = math.pow(2.0,windowShift)
   while Tc >= minPeriod:
      thisBin = getBin(period,power,Tc,halfWindow)
      #
      # bin should not be empty
      #
      if (len(thisBin) > 0):
         P.append(np.mean(thisBin))
         T.append(Tc)
      else:
         P.append(float('NAN'))
         T.append(Tc)
         
      #
      # move the center period to the left by half of the windowWidth
      #
      Tc /= shift

   #
   # do higher periods (> pStart and <= maxPeriod)
   #
   Tc = pStart * shift

   while Tc <= maxPeriod:
      
      thisBin = getBin(period,power,Tc,halfWindow)
      
      #
      # bin should not be empty
      #
      if (len(thisBin) > 0):
         P.append(np.mean(thisBin))
         T.append(Tc)
      else:
         P.append(float('NAN'))
         T.append(Tc)

      #
      # move the center period to the right by half of the windowWidth
      #
      Tc *= shift

   #
   # sort on period and return
   #
   T,P = (list(t) for t in zip(*sorted(zip(T,P))))
   return (T,P)

def smoothAngleT(period,power,samplingRate,octaveWindowWidth,octaveWindowShift,maxPeriod,rotation):
   #
   ##########################################################################
   # smooth the spectra in the period domain
   #
   # smoothing is based on McNamara (2005) but with smaller window 
   # length for better resolution and done in the period domain
   #
   # The optimum sampling window appears to be 1/4 octave (dB value at 
   # extract frequency taken as average of all points 1/8 octave either side).
   #
   # The lowest period center of the window is at the 1.0 /Nyquist frequency
   #
   # To make the output independent of sample rate, the multiples are always with 
   # respect to a period of 1.0 seconds
   #
   # w  = octaveWindowWidth       <-- full window width
   # hw = 0.5 * octaveWindowWidth <-- half window width
   # Tc <= 2.0/samplingFrequency  <-- the last sample at the Nyquist frequency
   # Te = Tc * 2^hw               <-- center frequency is 1/2 window width away from the end
   # Ts = Tc / 2^hw
   # Te = Ts * (2^w)
   #
   # rotation tells the function how the angles are measure, 0 from horizontal
   #          and 90 from vertical. This should not make much difference but
   #          wanted to be consistent in our calculations
   # HISTORY:
   #    2014-02-07 Manoch: created
   # 
   #
   ##########################################################################
   # 
   T     = [] # <-- period container
   P     = [] # <-- power container

   #
   # sort on period
   #
   period,power = (list(t) for t in zip(*sorted(zip(period,power))))

   halfWindow    = float(octaveWindowWidth / 2.0)
   windowShift   = octaveWindowShift

   #
   # minimum period at the Nyquist
   #
   minPeriod = 2.0 / float(samplingRate)

   #
   # To make the output independent of sample rate, the multiples are always with 
   # respect to a period of 1.0 seconds
   #
   Tc = 1.0
   #
   # do lower periods (<= 1.0 & >= minPeriod)
   #
   shift = math.pow(2.0,windowShift)
   while Tc >= minPeriod:
      thisBin = getBin(period,power,Tc,halfWindow)
      #
      # bin should not be empty
      #
      if (len(thisBin) > 0):
         #
         # place the points on a unit circle and find the mean of components
         #
         sumSin = 0
         sumCos = 0
         for i in xrange(0,len(thisBin)):
            rotated = 90.0 - angles[i]
            sumSin += math.sin(rotated*math.pi/180.0)
            sumCos += math.cos(rotated*math.pi/180.0)

         meanSin = float(sumSin)/float(len(thisBin))
         meanCos = float(sumCos)/float(len(thisBin))

         #
         # The point of atan2() is that the signs of both inputs are known to it, so it can compute 
         # the correct quadrant for the angle. For example, atan(1) and atan2(1, 1) are both pi/4, but atan2(-1, -1) is -3*pi/4.
         #
         P.append(rotation -(math.atan2(meanSin,meanCos)*180.0/math.pi))
         T.append(Tc)
      else:
         P.append(float('NAN'))
         T.append(Tc)

      #
      # move the center period to the left by half of the windowWidth
      #
      #print Tc,">=",minPeriod
      Tc /= shift

   #
   # do higher periods (> 1.0)
   #
   Tc = 1.0 * shift

   while Tc <= maxPeriod:

      thisBin = getBin(period,power,Tc,halfWindow)

      #
      # bin should not be empty
      #
      if (len(thisBin) > 0):
         #
         # place the points on a unit circle and find the mean of components
         #
         sumSin = 0
         sumCos = 0
         for i in xrange(0,len(thisBin)):
            sumSin += math.sin((rotation-thisBin[i])*math.pi/180.0)
            sumCos += math.cos((rotation-thisBin[i])*math.pi/180.0)

         meanSin = float(sumSin)/float(len(thisBin))
         meanCos = float(sumCos)/float(len(thisBin))

         #
         # The point of atan2() is that the signs of both inputs are known to it, so it can compute 
         # the correct quadrant for the angle. For example, atan(1) and atan2(1, 1) are both pi/4, but atan2(-1, -1) is -3*pi/4.
         #
         P.append(rotation -(math.atan2(meanSin,meanCos)*180.0/math.pi))
         T.append(Tc)
      else:
         P.append(float('NAN'))
         T.append(Tc)

      #
      # move the center period to the right by half of the windowWidth
      #
      Tc *= shift

   #
   # sort on period and return
   #
   T,P = (list(t) for t in zip(*sorted(zip(T,P))))
   return (T,P)
