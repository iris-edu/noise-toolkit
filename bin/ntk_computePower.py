#!/usr/bin/env python

import sys
import os
import math
import numpy as np
import importlib

# Import the Noise Toolkit libraries.
library_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
sys.path.append(library_path)

param_path = os.path.join(os.path.dirname(__file__), '..', 'param')
sys.path.append(param_path)

import msgLib as msg_lib
import staLib as sta_lib
import utilsLib as utils_lib

"""
  NAME:   ntk_computePower.py - a Python 3 script to calculate power of each PSD window over selected bin period bands

  Copyright (C) 2020  Product Team, IRIS Data Management Center

     This is a free software; you can redistribute it and/or modify
     it under the terms of the GNU Lesser General Public License as
     published by the Free Software Foundation; either version 3 of the
     License, or (at your option) any later version.

     This script is distributed in the hope that it will be useful, but
     WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
     Lesser General Public License (GNU-LGPL) for more details.  The
     GNU-LGPL and further information can be found here:
     http://www.gnu.org/

     You should have received a copy of the GNU Affero General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

  INPUT:

  PDF files

  HISTORY:
     2020-11-16 Manoch: V.2.0.0 Python 3 and adoption of PEP 8 style guide.
     2015-04-22 Manoch: file name correction
     2014-11-24 Manoch: Beta release (V.0.5) to compute power based on a combined PSD file
                with format similar to output of the ntk_extractPsdHour.py script (see NTK PSD/PDF bundle)
     2013-10-07 Manoch: revision for production test
     2013-03-14 Manoch: created

"""

version = 'V.2.0.0'
script = sys.argv[0]
script = os.path.basename(script)

# Initial mode settings.
timing = False
do_plot = False
verbose = False
mode_list = ['0', 'plot', 'time', 'verbose']
default_param_file = 'computePower'
if os.path.isfile(os.path.join(param_path, f'{default_param_file}.py')):
    param = importlib.import_module(default_param_file)
else:
    code = msg_lib.error(f'could not load the default parameter file  [param/{default_param_file}.py]', 2)
    sys.exit(code)


def usage():
    """ Usage message.
    """
    print(f'\n\n{script} version {version}\n\n'
          f'A Python 3 script to calculate power of each PSD window over selected bin period bands.'
          f'\n\nUsage:\n\t{script} to display the usage message (this message)'
          f'\n\t  OR'
          f'\n\t{script} param=FileName net=network sta=station loc=location chandir=channel directory'
          f' start=YYYY-MM-DDTHH:MM:SS end=YYYY-MM-DDTHH:MM:SS xtype=[period|frequency] verbose=[0|1]\n'
          f'\n\tto perform extraction where:'
          f'\n\t param\t\t[default: {default_param_file}] the configuration file name '
          f'\n\t net\t\t[required] network code'
          f'\n\t sta\t\t[required] station code'
          f'\n\t loc\t\t[required] location ID'
          f'\n\t chan\t\t[required] channel ID. '
          f'\n\t xtype\t\t[required, period or frequency] X-axis type for the PSD files.'
          f'\n\t start\t\t[required] start date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t end\t\t[required] end date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t verbose\t[0 or 1, default: {param.verbose}] to run in verbose mode set to 1'
          f'\n\t file\t\t[required] the "combined" PSD file (similar to the output of the ntk_extractPsdHour.py '
          f'script)to read.'
          f'\n\nInput: '
          f'\n\tThe input PSD file should have the same format as the output of the ntk_extractPsdHour.py script'
          f'\n\nOutput: '
          f'\n\tData file(s) with the file names provided at the end of the run.'
          f'\n\n\tThe output file name has the form:'
          f'\n\t\tnet.sta.loc.chan.start.end.xtype.txt'
          f'\n\tfor example:'
          f'\n\t\tTA.O18A.--.BHZ.2008-08-14.2008-08-14.period.txt'
          f'\n\nExamples:'
          f'\n\n\t-usage:'
          f'\n\tpython {script}'
          f'\n\n\t- assuming that you already have executed the following command "successfully" to generate PSD files:'
          f'\n\tpython ntk_extractPsdHour.py net=TA sta=O18A loc=DASH chan=BHZ start=2008-08-14T12:00:00 '
          f'end=2008-08-14T12:30:00 xtype=period'
          f'\n\n\tcompute power via:'
          f'\n\tpython {script} param={default_param_file} net=TA sta=O18A loc=DASH chan=BHZ xtype=period verbose=1  '
          f'file=TA.O18A.--.BHZ.2008-08-14.2008-08-14.period.txt'
          f'\n\n\n\n')


# Get the run arguments.
args = utils_lib.get_args(sys.argv, usage)
if not args:
    usage()
    sys.exit(0)

# Import the user-provided parameter file. The parameter file is under the param directory at the same level
# as the script directory.
param_file = utils_lib.get_param(args, 'param', default_param_file, usage)

if param_file is None:
    usage()
    code = msg_lib.error(f'{script}, parameter file is required', 2)
    sys.exit(code)

# Import the parameter file if it exists.
if os.path.isfile(os.path.join(param_path, f'{param_file}.py')):
    param = importlib.import_module(param_file)
else:
    usage()
    code = msg_lib.error(f'{script}, bad parameter file name [{param_file}]', 2)
    sys.exit(code)

# Bin ranges.
bin_start = list()
bin_end = list()
bins = param.bins

for _bin in bins:
    try:
        bin_start.append(param.binStart[_bin])
        bin_end.append(param.binEnd[_bin])
    except Exception as ex:
        code = msg_lib.error(f'bad band {_bin} in param file', 2)
        sys.exit(code)

if verbose > 0:
    msg_lib.info(f'PERIOD BIN START: {bin_start}')
    msg_lib.info(f'PERIOD BIN ENDis: {bin_end}')

network = utils_lib.get_param(args, 'net', None, usage)
station = utils_lib.get_param(args, 'sta', None, usage)
location = sta_lib.get_location(utils_lib.get_param(args, 'loc', None, usage))
channel = utils_lib.get_param(args, 'chan', None, usage)
xtype = utils_lib.get_param(args, 'xtype', None, usage)

# NOTE: the input PSD file is assumed to have the same format as the output of the ntk_extractPsdHour.py script
psd_file = utils_lib.get_param(args, 'file', None, usage)
psd_directory = os.path.join(param.dataDirectory, param.psdDirectory)
psd_file_name = os.path.join(psd_directory, ".".join([network, station, location]), channel, psd_file)

# Check to see if the PSD file exists.
if not os.path.isfile(psd_file_name):
    code = msg_lib.error(f'Could not find the PSD file [{psd_file_name}]', 2)
    sys.exit(code)

# Create the power directories as needed
power_directory = os.path.join(param.dataDirectory, param.powerDirectory)
if not os.path.exists(power_directory):
    os.makedirs(power_directory)

power_directory = os.path.join(power_directory, ".".join([network, station, location]))
if not os.path.exists(power_directory):
    os.makedirs(power_directory)

power_directory = os.path.join(power_directory, channel)
if not os.path.exists(power_directory):
    os.makedirs(power_directory)

# Open the power file.
power_file_name = os.path.join(power_directory, psd_file.replace(f'_{xtype}', '').replace(f'.{xtype}', ''))
out_file = open(power_file_name, 'w')

# Write the output header.
out_file.write('Period ranges\n')
out_file.write('%20s %20s' % ('Date', 'Time'))
for k in range(len(bin_start)):
    out_file.write('%20s' % f'{bins[k]} ({bin_start[k]}-{bin_end[k]})')
out_file.write('\n')

msg_lib.info(f'PSD FILE: {psd_file_name}')
msg_lib.info(f'POWER FILE: {power_file_name}')

# Loop through the PSD file, compute bin powers and write them out.
previous_date = None
previous_time = None

with open(psd_file_name) as in_file:
    # init the records
    period = list()
    psd = list()
    power = list()

    # rRad the entire PSD file.
    lines = in_file.readlines()

    # Find the last non-blank line.
    line_count = len(lines)
    for i in range(1, len(lines)):
        line = lines[-i].strip()
        if len(line) > 0:
            line_count = len(lines) - i + 1
            break
    if verbose:
        msg_lib.info(f'INPUT: {line_count} lines')

    # Process line by line.
    for i in range(line_count):
        line = lines[i]
        line = line.strip()
        # Each row, split columns.
        date, time, this_x, this_y = line.split()

        # Depending on type, recompute X if needed.
        if xtype == 'frequency':
            this_x = 1.0 / float(this_x)

        if previous_date is None:
            previous_date = date
            previous_time = time

        # Group lines based on date and time
        # save the period and value of interest.
        if (date == previous_date and time == previous_time) and i < line_count - 1:
            period.append(float(this_x))
            psd.append(float(this_y))

        # New date-time, jump out and compute power for the previous date-time.
        else:
            previous_line = line

            # Save the values from the last row, if we are at the end of the file
            if i == line_count - 1:
                period.append(float(this_x))
                psd.append(float(this_y))

            power = np.zeros(len(bins))

            # Compute power.
            if len(period) > 0:
                # Sort them to keep the code simple.
                period, psd = zip(*sorted(zip(period, psd)))

                """Go through the records and for each bin convert to power from dB
                   NOTE: PSD is equal to the power as the a measure point divided by the width of the bin
                        PSD = P / W
                        log(PSD) = Log(P) - log(W)
                        log(P) = log(PSD) + log(W)  here W is width in frequency
                        log(P) = log(PSD) - log(Wt) here Wt is width in period
                """
                for k in range(len(bins)):
                    if verbose > 1:
                        msg_lib.message(f' CHAN: {channel}, DATE": {previous_date} {previous_time}'
                                        f'PERIOD: {bins[k]} from {bin_start[k]} to {bin_end[k]}')

                    """
                      For each bin perform rectangular integration to compute power
                      power is assigned to the period at the begining of the interval
                           _   _
                          | |_| |
                          |_|_|_|
                    """

                    for j in range(0, len(psd) - 1):
                        # Since to calculate the area we take the width between point j and j+1, as a result we
                        # only accept the point if it falls before the end point, hence (<).
                        if float(bin_start[k]) <= float(period[j]) < float(bin_end[k]):

                            # Here we want to add the area just before the first sample if our window start
                            # does not fall on a data point. We set start of the band as the start of our window.
                            if j > 0 and (float(period[j]) > float(bin_start[k]) > float(period[j - 1])):
                                if verbose > 1:
                                    msg_lib.info(f'{j} ADJUST THE BAND START {period[j]} BAND NOW GOES'
                                                 f'   FROM 1: {bin_start[k]} to {period[j + 1]}')
                                bin_width_hz = abs((1.0 / float(bin_start[k])) - (1.0 / float(period[j + 1])))
                            elif j == 0 and float(period[j]) > float(bin_start[k]):
                                if verbose > 1:
                                    msg_lib.info(f'{j} ADJUST THE BAND START {period[j]} BAND NOW GOES'
                                                 f'   FROM 1: {bin_start[k]} to {period[j + 1]}')
                                bin_width_hz = abs((1.0 / float(bin_start[k])) - (1.0 / float(period[j + 1])))

                            # Here we want to adjust the width if our window end
                            # does not fall on a data point.
                            elif j < len(psd) - 1 and (float(period[j]) < float(bin_end[k]) <= float(period[j + 1])):
                                if verbose > 1:
                                    msg_lib.info(f'{j} ADJUST THE BAND END {period[j]} BAND NOW GOES'
                                                 f'    FROM 2: {period[j]} to {bin_end[k]}')
                                bin_width_hz = abs((1.0 / float(period[j])) - (1.0 / float(bin_end[k])))
                            elif j == len(psd) - 1 and float(period[j]) < float(bin_end[k]):
                                if verbose > 1:
                                    msg_lib.info(f'{j} ADJUST THE BAND END {period[j]} BAND NOW GOES'
                                                 f'    FROM 2: {period[j]} to {bin_end[k]}')
                                bin_width_hz = abs((1.0 / float(period[j])) - (1.0 / float(bin_end[k])))

                            # For the rest in between.
                            else:
                                if verbose > 1:
                                    msg_lib.info(f'{j} NO ADJUSTMENT BAND FROM 3: {period[j]} to {period[j + 1]}')
                                bin_width_hz = abs((1.0 / float(period[j])) - (1.0 / float(period[j + 1])))

                            if verbose > 1:
                                msg_lib.info(f'    BIN WIDTH {bin_width_hz} Hz')

                            power[k] += (math.pow(10.0, float(psd[j]) / 10.0) * bin_width_hz)
                            if verbose > 1:
                                msg_lib.info(
                                    f'POWER {psd[j]} ----> {math.pow(10.0, float(psd[j]) / 10.0) * bin_width_hz}')

                        else:
                            if verbose > 1:
                                msg_lib.info(f'{j} {period[j]} REJECTED')
                    if verbose > 1:
                        msg_lib.info(f'TOTAL POWER {power[k]}')
                out_file.write("%20s %20s" % (previous_date, previous_time))
                for index in range(0, len(bin_start)):
                    out_file.write("%20.5e" % (power[index]))
                out_file.write("\n")

                # Init the records.
                period = list()
                psd = list()
                power = list()

                # Capture the first line tht was left over from previous iteration.
                previous_line = previous_line.strip()
                date, time, this_x, this_y = previous_line.split()
                if type == 'frequency':
                    this_x = 1.0 / float(this_x)
                period.append(float(this_x))
                psd.append(float(this_y))
                previous_date = date
                previous_time = time
