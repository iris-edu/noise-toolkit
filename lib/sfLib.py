import numpy as np
import math


def get_bin(x, y, xc, octave_half_window):
    """
    Gather y values that fall within octaveHalfWindow  on either side of the central x value

    HISTORY:
       2015-04-07  Manoch: Corrected the instrument correction for SAC files that would
                           apply sensitivity in addition to instrument correction
       2014-02-07 Manoch: created
    """
    bin_list = list()
    shift = math.pow(2.0, octave_half_window)

    # The bin is octaveHalfWindow around xc.
    x1 = xc / shift
    x2 = xc * shift
    xs = min(x1, x2)
    xe = max(x1, x2)

    # Gather the values that fall within the range >=Xs and <= Xe.
    for i, _x in enumerate(x):
        if xs <= _x <= xe:
            bin_list.append(float(y[i]))
    return bin_list


def smooth_nyquist(xtype, xi, yi, sampling_rate, octave_window_width, octave_window_shift, x_limit):
    """
    Smoothing starting frequency/period = (Nyquist= Nyquist frequency, 1= 1Hz/1Sec)
    Smooth the yi in the xi domain

    smoothing is based on McNamara (2005)

    the y at the extract xi is taken as average of all yi points within
    octave_window_width / 2 on either side of xi.

    We want the first sample to be at the Nyquist

     w  = octave_window_width <-- full window width
     hw = 0.5 * octave_window_width <-- half window width

    HISTORY:
        2014-02-07 Manoch: created

    """
    x = list()
    y = list()

    # The shortest period (highest frequency) center of the window starts  at the Nyquist.
    window_width = octave_window_width
    half_window = float(window_width / 2.0)
    window_shift = octave_window_shift

    # Shift of each fc.
    shift = math.pow(2.0, window_shift)

    # The first center x at the Nyquist
    if xtype == "frequency":
        xc = float(sampling_rate) / float(2.0)  # Nyquist frequency
    else:
        xc = float(2.0) / float(sampling_rate)  # Nyquist period

    while True:
        # Do not go below the minimum frequency.
        # Do not go above the maximum period

        if (xtype == "frequency" and xc < x_limit) or (xtype == "period" and xc > x_limit):
            x, y = (list(t) for t in zip(*sorted(zip(x, y))))
            return x, y

        bin_list = get_bin(xi, yi, xc, half_window)

        # Bin should not be empty.
        if len(bin_list) > 0:
            y.append(np.mean(bin_list))
            x.append(xc)
        else:
            y.append(float('NAN'))
            x.append(xc)

        # Move the center frequency to the right by half of the window_width.
        # Move the center period to the left by half of the window_width.
        if xtype == "frequency":
            xc /= shift
        else:
            xc *= shift

    #
    # Sort on x and return.
    #
    x, y = (list(t) for t in zip(*sorted(zip(x, y))))
    return x, y


def smooth_frequency(frequency, power, sampling_rate, octave_window_width, octave_window_shift, min_frequency, x_start):
    """Sooth the spectra in the frequency domain

     respect to XStart defined by user and not the Nyquist frequency

     HISTORY:
        2014-02-07 Manoch: created

    """
    freq = list()  # <-- frequency container
    this_power = list()  # <-- power container

    # sort on frequency
    frequency, power = (list(t) for t in zip(*sorted(zip(frequency, power))))

    half_window = float(octave_window_width / 2.0)
    window_shift = octave_window_shift

    # maximum frequency at the Nyquist
    max_frequency = float(sampling_rate) / 2.0

    # x_start is set by user so that output remains independent of sample rate, the multiples are always with
    # respect to x_start
    fc = x_start

    # do the lower frequencies (<= x_start & >= min_frequency)
    shift = math.pow(2.0, window_shift)
    while fc >= min_frequency:

        bin_list = get_bin(frequency, power, fc, half_window)

        # bin should not be empty
        if len(bin_list) > 0:
            this_power.append(np.mean(bin_list))
            freq.append(fc)
        else:
            this_power.append(float('NAN'))
            freq.append(fc)

        # move the center frequency to the left by half of the window_width
        fc /= shift

    # do higher frequencies (> x_start & <= Nyquist)
    fc = x_start * shift

    while fc <= max_frequency:

        bin_list = get_bin(frequency, power, fc, half_window)

        # bin should not be empty
        if len(bin_list) > 0:
            this_power.append(np.mean(bin_list))
            freq.append(fc)
        else:
            this_power.append(float('NAN'))
            freq.append(fc)

        # move the center frequency to the right by half of the window_width
        fc *= shift

    # sort on frequency and return
    freq, this_power = (list(t) for t in zip(*sorted(zip(freq, this_power))))
    return freq, this_power


def smooth_frequency_angular(frequency, power, sampling_rate, octave_window_width, octave_window_shift,
                             min_frequency, x_start, rotation):
    """Smooth the spectra in the frequency domain for angular quantities

    Smoothing starting frequency/period = (Nyquist= Nyquist frequency, 1= 1Hz/1Sec)

     smoothing is based on McNamara (2005) but with smaller window
     length for better resolution and done in the frequency domain

     The optimum sampling window appears to be 1/4 octave (dB value at
     extract frequency taken as average of all points 1/8 octave either side).

     The highest frequency center of the window is at the Nyquist frequency

     To make the output independent of sample rate, the multiples are always with
     respect to a period of 1.0 seconds

     w  = octave_window_width       <-- full window width
     hw = 0.5 * octave_window_width <-- half window width
     fc <= samplingFrequency/2.0   <-- the last sample at the Nyquist frequency
     Fe = fc * 2^hw               <-- center frequency is 1/2 window width away from the end
     Fs = fc / 2^hw
     Fe = Fs * (2^w)

     rotation tells the function how the angles are measure, 0 from horizontal
              and 90 from vertical. This should not make much difference but
              wanted to be consistent in our calculations

     HISTORY:
        2015-06-01 Manoch: made the start frequency selectable to support Nyquist or 1 as the start frequency,
                           like smooth_frequency
        2014-02-07 Manoch: created


    """

    freq = list()  # <-- frequency container
    this_power = list()  # <-- power container

    # sort on frequency
    frequency, power = (list(t) for t in zip(*sorted(zip(frequency, power))))

    half_window = float(octave_window_width / 2.0)
    window_shift = octave_window_shift
    # maximum frequency at the Nyquist
    max_frequency = float(sampling_rate) / 2.0

    # To make the output independent of sample rate, the multiples are always with
    # respect to a period of 1.0 seconds
    fc = x_start

    # do the lower frequencies (<= 1.0 & >= min_frequency)
    shift = math.pow(2.0, window_shift)
    while fc >= min_frequency:

        bin_list = get_bin(frequency, power, fc, half_window)

        # bin should not be empty
        if len(bin_list) > 0:
            # place the points on a unit circle and find the mean of components
            sum_sin = 0
            sum_cos = 0
            for i in range(0, len(bin_list)):
                rotated = rotation - bin_list[i]
                sum_sin += math.sin(rotated * math.pi / 180.0)
                sum_cos += math.cos(rotated * math.pi / 180.0)

            mean_sin = float(sum_sin) / float(len(bin_list))
            mean_cos = float(sum_cos) / float(len(bin_list))

            # The point of atan2() is that the signs of both inputs are known to it, so it can compute
            # the correct quadrant for the angle. For example, atan(1) and atan2(1, 1) are both pi/4,
            # but atan2(-1, -1) is -3*pi/4.
            this_power.append(rotation - (math.atan2(mean_sin, mean_cos) * 180.0 / math.pi))
            freq.append(fc)
        else:
            this_power.append(float('NAN'))
            freq.append(fc)

        # move the center frequency to the left by half of the window_width
        fc /= shift

    # do higher frequencies (> 1.0 & <= Nyquist)
    fc = x_start * shift

    while fc <= max_frequency:

        bin_list = get_bin(frequency, power, fc, half_window)

        # bin should not be empty
        if len(bin_list) > 0:
            # place the points on a unit circle and find the mean of components
            sum_sin = 0
            sum_cos = 0
            for i in range(0, len(bin_list)):
                rotated = rotation - bin_list[i]
                sum_sin += math.sin(rotated * math.pi / 180.0)
                sum_cos += math.cos(rotated * math.pi / 180.0)

            mean_sin = float(sum_sin) / float(len(bin_list))
            mean_cos = float(sum_cos) / float(len(bin_list))

            # The point of atan2() is that the signs of both inputs are known to it, so it can compute
            # the correct quadrant for the angle. For example, atan(1) and atan2(1, 1) are both pi/4,
            # but atan2(-1, -1) is -3*pi/4.
            this_power.append(rotation - (math.atan2(mean_sin, mean_cos) * 180.0 / math.pi))
            freq.append(fc)
        else:
            this_power.append(float('NAN'))
            freq.append(fc)

        # move the center frequency to the right by half of the window_width
        fc *= shift

    # sort on frequency and return
    freq, this_power = (list(t) for t in zip(*sorted(zip(freq, this_power))))
    return freq, this_power


def smooth_period(period, power, sampling_rate, octave_window_width, octave_window_shift, max_period, period_start):
    """Smooth the spectra in the period domain

     To make the output independent of sample rate, the multiples are always with
     respect to pStart period defined by user

     HISTORY:
        2014-02-07 Manoch: created


    """

    per = list()  # <-- period container
    this_power = list()  # <-- power container

    # sort on period
    period, power = (list(t) for t in zip(*sorted(zip(period, power))))

    half_window = float(octave_window_width / 2.0)
    window_shift = octave_window_shift

    # minimum period at the Nyquist
    min_period = 2.0 / float(sampling_rate)

    # To make the output independent of sample rate, the multiples are always with
    # respect to period pStart set by user
    tc = period_start

    # do lower periods (<= pStart & >= min_period)
    shift = math.pow(2.0, window_shift)
    print("TC", tc, min_period, max_period)
    while tc >= min_period:
        bin_list = get_bin(period, power, tc, half_window)
        # bin should not be empty
        if len(bin_list) > 0:
            this_power.append(np.mean(bin_list))
            per.append(tc)
        else:
            this_power.append(float('NAN'))
            per.append(tc)

        # move the center period to the left by half of the window_width
        tc /= shift

    # do higher periods (> pStart and <= maxPeriod)
    tc = period_start * shift

    while tc <= max_period:

        bin_list = get_bin(period, power, tc, half_window)

        # bin should not be empty
        if len(bin_list) > 0:
            this_power.append(np.mean(bin_list))
            per.append(tc)
        else:
            this_power.append(float('NAN'))
            per.append(tc)

        # move the center period to the right by half of the window_width
        tc *= shift

    # sort on period and return
    per, this_power = (list(t) for t in zip(*sorted(zip(per, this_power))))
    return per, this_power


def smooth_nyquest_angular(xtype, xi, yi, sampling_rate, octave_window_width, octave_window_shift, x_limit, rotation):
    """Smooth the yi in the xi domain for angular quantities

     To make the output independent of sample rate, the multiples are always with

     smoothing is based on McNamara (2005)

     the y at the extract xi is taken as average of all yi points within
     octave_window_width/2 on either side of xi.

     we want the first sample to be at the Nyquist

     w  = octave_window_width <-- full window width
     hw = 0.5 * octave_window_width <-- half window width

     rotation tells the function how the angles are measure, 0 from horizontal
              and 90 from vertical. This should not make much difference but
              wanted to be consistent in our calculations

     HISTORY:
        2015-06-01 Manoch: created for polarization support

    """

    x = list()
    y = list()

    # shortest period (highest frequency) center of the window
    # starts  at the Nyquist
    window_width = octave_window_width
    half_window = float(window_width / 2.0)
    window_shift = octave_window_shift
    shift = math.pow(2.0, window_shift)  # shift of each fc

    # the first center x at the Nyquist
    if xtype == "frequency":
        xc = float(sampling_rate) / float(2.0)  # Nyquist frequency
    else:
        xc = float(2.0) / float(sampling_rate)  # Nyquist period

    while True:
        # do not go below the minimum frequency
        # do not go above the maximum period
        if (xtype == "frequency" and xc < x_limit) or (xtype == "period" and xc > x_limit):
            break

        bin_list = get_bin(xi, yi, xc, half_window)

        # bin should not be empty
        if len(bin_list) > 0:
            # place the points on a unit circle and find the mean of components
            sum_sin = 0
            sum_cos = 0
            for i in range(0, len(bin_list)):
                rotated = rotation - bin_list[i]
                sum_sin += math.sin(rotated * math.pi / 180.0)
                sum_cos += math.cos(rotated * math.pi / 180.0)

            mean_sin = float(sum_sin) / float(len(bin_list))
            mean_cos = float(sum_cos) / float(len(bin_list))

            # The point of atan2() is that the signs of both inputs are known to it, so it can compute
            # the correct quadrant for the angle. For example, atan(1) and atan2(1, 1) are both pi/4,
            # but atan2(-1, -1) is -3*pi/4.
            y.append(rotation - (math.atan2(mean_sin, mean_cos) * 180.0 / math.pi))
            x.append(xc)

        else:
            y.append(float('NAN'))
            x.append(xc)

        # move the center frequency to the right by half of the window_width
        # move the center period to the left by half of the window_width
        if xtype == "frequency":
            xc /= shift
        else:
            xc *= shift

    # sort on x and return
    x, y = (list(t) for t in zip(*sorted(zip(x, y))))
    return x, y


def smooth_period_angular(period, power, sampling_rate, octave_window_width, octave_window_shift,
                          maxPeriod, pStart, rotation):
    """Smooth the spectra in the period domain

     smoothing is based on McNamara (2005) but with smaller window
     length for better resolution and done in the period domain

     The optimum sampling window appears to be 1/4 octave (dB value at
     extract frequency taken as average of all points 1/8 octave either side).

     The lowest period center of the window is at the 1.0 /Nyquist frequency

     To make the output independent of sample rate, the multiples are always with
     respect to a period of 1.0 seconds

     w  = octave_window_width       <-- full window width
     hw = 0.5 * octave_window_width <-- half window width
     tc <= 2.0/samplingFrequency  <-- the last sample at the Nyquist frequency
     Te = tc * 2^hw               <-- center frequency is 1/2 window width away from the end
     Ts = tc / 2^hw
     Te = Ts * (2^w)

     rotation tells the function how the angles are measure, 0 from horizontal
              and 90 from vertical. This should not make much difference but
              wanted to be consistent in our calculations
     HISTORY:
        2015-06-01 Manoch: made the start period selectable to support Nyquist or 1 as the start period, like smooth_period
        2014-02-07 Manoch: created


    """

    per = list()  # <-- period container
    this_power = list()  # <-- power container

    # sort on period
    period, power = (list(t) for t in zip(*sorted(zip(period, power))))

    half_window = float(octave_window_width / 2.0)
    window_shift = octave_window_shift

    # minimum period at the Nyquist
    min_period = 2.0 / float(sampling_rate)

    # To make the output independent of sample rate, the multiples are always with
    # respect to a period of 1.0 seconds
    tc = pStart

    # do lower periods (<= 1.0 & >= min_period)
    shift = math.pow(2.0, window_shift)
    while tc >= min_period:
        bin_list = get_bin(period, power, tc, half_window)
        # bin should not be empty
        if len(bin_list) > 0:
            #
            # place the points on a unit circle and find the mean of components
            #
            sum_sin = 0
            sum_cos = 0
            for i in range(0, len(bin_list)):
                rotated = 90.0 - angles[i]
                sum_sin += math.sin(rotated * math.pi / 180.0)
                sum_cos += math.cos(rotated * math.pi / 180.0)

            mean_sin = float(sum_sin) / float(len(bin_list))
            mean_cos = float(sum_cos) / float(len(bin_list))

            # The point of atan2() is that the signs of both inputs are known to it, so it can compute
            # the correct quadrant for the angle. For example, atan(1) and atan2(1, 1) are both pi/4,
            # but atan2(-1, -1) is -3*pi/4.
            this_power.append(rotation - (math.atan2(mean_sin, mean_cos) * 180.0 / math.pi))
            per.append(tc)
        else:
            this_power.append(float('NAN'))
            per.append(tc)

        # move the center period to the left by half of the window_width
        tc /= shift

    # do higher periods (> 1.0)
    tc = pStart * shift

    while tc <= maxPeriod:

        bin_list = get_bin(period, power, tc, half_window)

        # bin should not be empty
        if len(bin_list) > 0:
            # place the points on a unit circle and find the mean of components
            sum_sin = 0
            sum_cos = 0
            for i in range(0, len(bin_list)):
                sum_sin += math.sin((rotation - bin_list[i]) * math.pi / 180.0)
                sum_cos += math.cos((rotation - bin_list[i]) * math.pi / 180.0)

            mean_sin = float(sum_sin) / float(len(bin_list))
            mean_cos = float(sum_cos) / float(len(bin_list))

            # The point of atan2() is that the signs of both inputs are known to it, so it can compute
            # the correct quadrant for the angle. For example, atan(1) and atan2(1, 1) are both pi/4,
            # but atan2(-1, -1) is -3*pi/4.
            this_power.append(rotation - (math.atan2(mean_sin, mean_cos) * 180.0 / math.pi))
            per.append(tc)
        else:
            this_power.append(float('NAN'))
            per.append(tc)

        # move the center period to the right by half of the window_width
        tc *= shift

    # sort on period and return
    per, this_power = (list(t) for t in zip(*sorted(zip(per, this_power))))
    return per, this_power
