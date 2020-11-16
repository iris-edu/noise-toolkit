#!/usr/bin/env python

import sys
import os

import datetime

import importlib
from obspy.core import UTCDateTime

import matplotlib.pyplot as plt

from matplotlib.dates import DateFormatter, \
    YearLocator, MonthLocator, DayLocator, WeekdayLocator, MONDAY

# Import the Noise Toolkit libraries.
library_path = os.path.join(os.path.dirname(__file__), '..', 'lib')
sys.path.append(library_path)

param_path = os.path.join(os.path.dirname(__file__), '..', 'param')
sys.path.append(param_path)

import msgLib as msg_lib
import fileLib as file_lib
import staLib as sta_lib
import utilsLib as utils_lib
import shared

"""
  ntk_plotPower.py - a Python 3 script to plot median power obtained from 
                    the median power file produced by ntk_medianPower.py

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

  HISTORY:
     2020-11-16 Manoch: V.2.0.0 Python 3 and adoption of PEP 8 style guide.
     2015-02-20 Manoch: addressed the output file naming issue
     2014-11-24 Manoch: V.0.5, modified the inpot format to read
                median power file produced by ntk_medianPower.py
     2013-10-07 Manoch: revision for production test
     2013-03-14 Manoch: created partially
"""

version = 'V.2.0.0'
script = sys.argv[0]
script = os.path.basename(script)

# Initial mode settings.
timing = False
do_plot = False
verbose = False
mode_list = ['0', 'plot', 'time', 'verbose']
default_param_file = 'plotPower'
if os.path.isfile(os.path.join(param_path, f'{default_param_file}.py')):
    param = importlib.import_module(default_param_file)
else:
    code = msg_lib.error(f'could not load the default parameter file  [param/{default_param_file}.py]', 2)
    sys.exit(code)

def usage():
    """ Usage message.
    """
    print(f'\n\n{script} version {version}\n\n'
          f'A Python 3 script to plot median power obtained from the median power file produced by '
          f'ntk_medianPower.py.'
          f'\n\nUsage:\n\t{script} to display the usage message (this message)'
          f'\n\t  OR'
          f'\n\t{script} param=FileName net=network sta=station loc=location chandir=channel _irectory'
          f' start=YYYY-MM-DDTHH:MM:SS end=YYYY-MM-DDTHH:MM:SS xtype=[period|frequency] verbose=[0|1] '
          f'xtype=[period|frequency]\n'
          f'\n\tto perform extraction where:'
          f'\n\t  param\t\t[default: {default_param_file}] the configuration file name '
          f'\n\t  net\t\t[required] network code'
          f'\n\t  sta\t\t[required] station code'
          f'\n\t  loc\t\t[required] location ID'
          f'\n\t  chan\t\t[required] channel ID'
          f'\n\t  bin\t\t[required] bin to process(name as defined in the parameter file)'
          f'\n\t  ymax\t\tmaximum value for the y-axis'
          f'\n\t  file\t\t[required] the median PSD power file '
          f'frequency for outputs and plots)'
          f'\n\t  start\t\t[required] start date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  end\t\t[required] end date-time (UTC) for extraction '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  verbose\t[0 or 1, default: {param.verbose}] to run in verbose mode set to 1'
          f'\n\n\t   INPUT:'
          f'\n\n\t   The PSD median power file created by ntk_medianPower.py \n'
          f'\n\n\t   The output windowed PDFs are stored under the corresponding window directory as follows:'
          f'\n\n\t   Win(h)     Dir'
          f'\n\n\t     6    ->  6h'
          f'\n\n\t    12    -> 12h'
          f'\n\n\t    24    ->  1d'
          f'\n\n\t    96    ->  4d'
          f'\n\n\t   384    -> 16d'
          f'\n\n\t  '
          f'\n\n\t period range index:'
          f'\n\n\t Index    Period range'
          f'\n\n\t 1        1-5 local microseism'
          f'\n\n\t 2       5-10 secondary microseism '
          f'\n\n\t 3      11-30 primary microseism'
          f'\n\n\t 4     50-200 Earth hum'
          f'\n\nExamples:'
          f'\n\n\t- usage:'
          f'\n\tpython {script}'
          f'\n\n\t- to plot power (note: the following example requires NM.SLM.--.BHZ.2009-03-01.2009-03-31.12h.txt as '
          f'the input file. If this file '
          f'does not exist):'
          f'\n\t\t 1) Generate PSDs:'
          f' \n\t\t\tpython ntk_computePSD.py param=computePSD net=NM sta=SLM  loc=DASH chan=BHZ '
          f'start=2009-03-01T00:00:00 end=2009-03-31T00:00:00 xtype=period plot=0 verbose=0'
          f'\n\t\t 2) Combine PSD files using the ntk_extractPsdHour.py script and note the output file name:'
          f' \n\t\t\tpython ntk_extractPsdHour.py net=NM sta=SLM loc=DASH chan=BHZ '
          f'start=2009-03-01T00:00:00 end=2009-03-31T00:00:00 xtype=period verbose=0'
          f'\n\t\t 3) Compute power using the combined PSD file generated at step 2 above:'
          f' \n\t\t\tpython ntk_computePower.py net=NM sta=SLM loc=DASH chan=BHZ '
          f'start=2009-03-01T00:00:00 end=2009-03-31T00:00:00 xtype=period '
          f'file=NM.SLM.--.BHZ.2009-03-01.2009-03-31.period.txt verbose=0'  
          f'\n\t\t 4) Compute 12-hour median power using the power file generated at step 3 above:'
          f' \n\t\t\tpython ntk_medianPower.py param=medianPower net=NM sta=SLM loc=DASH chan=BHZ '
          f'start=2009-03-01T00:00:00 end=2009-03-31T00:00:00 xtype=period win=12 '
          f'file=NM.SLM.--.BHZ.2009-03-01.2009-03-31.txt verbose=0'  
          f'\n\n\tNow, plot the Secondary Microseism, SM :'
          f'\n\t\tpython {script} param={default_param_file} param=plotPower net=NM sta=SLM loc=DASH chan=BHZ '
          f'start=2009-03-01T00:00:00 end=2009-03-31T00:00:00 win=12 bin=SM '
          f'file=NM.SLM.--.BHZ.2009-03-01.2009-03-31.12h.txt ymax=0.06 bin=SM'
          f'\n\n\n\n')


# See if user has provided the run arguments.
args = utils_lib.get_args(sys.argv, usage)

param_file = utils_lib.get_param(args, 'param', default_param_file, usage)

# Check and see if the param file exists.
if os.path.isfile(os.path.join(param_path, param_file + ".py")):
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'param'))
    param = importlib.import_module(param_file)
else:
    msg_lib.error(f'bad parameter file name {param_file}', 2)
    usage()
    sys.exit()

verbose = utils_lib.get_param(args, 'verbose', False, usage)

if verbose:
    msg_lib.info(f'script: {script} {len(sys.argv) - 1} args: {sys.argv}')

if len(sys.argv) < 9:
    code = msg_lib.error('not enough argument(s)', 1)
    usage()
    sys.exit(code)

# The run arguments.
network = utils_lib.get_param(args, 'net', None, usage)
station = utils_lib.get_param(args, 'sta', None, usage)
location = sta_lib.get_location(utils_lib.get_param(args, 'loc', None, usage))

# Set parameters for the time axis labeling.
# Every year.
years = YearLocator()
# Every month.
months = MonthLocator()
# Every day.
days = DayLocator()
weeks = WeekdayLocator(byweekday=MONDAY, interval=1)
yearsFmt = DateFormatter('%Y')
monthsFmt = DateFormatter('%Y-%m')
daysFmt = DateFormatter('%m-%d')

# Read the parameters from the configuration file.
columnTag = param.columnTag
columnLabel = param.columnLabel
dotColor = param.dotColor
dotSize = param.dotSize

network = utils_lib.get_param(args, 'net', None, usage)
station = utils_lib.get_param(args, 'sta', None, usage)
if verbose:
    msg_lib.info(f'NET: {network}  STA: {station}')

location = sta_lib.get_location(utils_lib.get_param(args, 'loc', None, usage))
channel = utils_lib.get_param(args, 'chan', None, usage)
start_date_time = utils_lib.get_param(args, 'start', None, usage)
end_date_time = utils_lib.get_param(args, 'end', None, usage)

# We always want to start_date_time from the beginning of the day, so we discard user hours, if any
start_datetime, start_year, start_month, start_day, start_doy = utils_lib.time_info(start_date_time)

# end_date_time is inclusive.
end_datetime, end_year, end_month, end_day, end_doy = utils_lib.time_info(end_date_time)

window_width_hour = utils_lib.get_param(args, 'win', None, usage)
ymax = utils_lib.get_param(args, 'ymax', None, usage)

# Moving window length in hours
#  - 6hrs 1d(24h) 4d(96h) 16d(384h) ...
window_tag = file_lib.get_window_tag(window_width_hour)
if verbose:
    msg_lib.info(f'WINDOW {window_width_hour}')

period_bin = utils_lib.get_param(args, 'bin', None, usage)
if period_bin not in param.bins:
    code = msg_lib.error(f'bad bin name [{period_bin}]', 2)
    sys.exit(code)

if verbose:
    msg_lib.info(f'PERIOD BIN {period_bin} from {param.binStart[period_bin]} to {param.binEnd[period_bin]}')

binIndex = param.binIndex[period_bin]
rangeLabel = param.rangeLabel[binIndex]
factor = param.factor[binIndex]
factorLabel = param.factorLabel[binIndex]
ymin = param.ymin[binIndex]
yticks = param.yticks[binIndex]
ytickLabels = param.ytickLabels[binIndex]
image_tag = param.imageTag[binIndex]

yLabel = rangeLabel + factorLabel

file_name = utils_lib.get_param(args, 'file', None, usage)
start_year = int(start_date_time.split("-")[0])
xStartL = start_date_time.split('T')[0]

end_date_time = end_date_time
end_year = int(end_date_time.split("-")[0])
xEndL = end_date_time.split('T')[0]

xminL = datetime.datetime(int(xStartL.split('-')[0]), int(xStartL.split('-')[1]), int(xStartL.split('-')[2]), 0, 0, 0)
xmaxL = datetime.datetime(int(xEndL.split('-')[0]), int(xEndL.split('-')[1]), int(xEndL.split('-')[2]), 0, 0, 0)

if verbose:
    msg_lib.info(f'START: {start_date_time} END: {end_date_time}  YMAX: {ymax}')

# Set the target for the Power directory. The associated window directory
# is under the corresponding power directory also
power_file_tag = list()
power_file_path = list()

title = " ".join([file_lib.get_tag(".", [network, station.replace(',', '+'), location]),
                  period_bin, "with", window_tag, "sliding window"])

# Plot bg color.
bgColor = (1, 1, 1)

# Start_date_time reading the PDF file.
# Initialize the limits.
X = list()
Y = list()
XLabel = list()
power_directory = os.path.join(param.dataDirectory, param.powerDirectory)
file_name = os.path.join(power_directory, ".".join([network, station, location]), channel, window_tag, file_name)
with open(file_name) as file:
    if verbose:
        msg_lib.info(f'OPENING: {file_name}')

    # Read the entire power file.
    lines = file.readlines()

    # Find the last non-blank line.
    line_count = len(lines)
    for i in range(1, len(lines)):
        line = lines[-i].strip()
        if len(line) > 0:
            line_count = len(lines) - i + 1
            break
    if verbose:
        msg_lib.info(f'INPUT: {line_count} lines')

    #
    # get the time of each line and the power, skip headers
    #
    powerTime = list()
    for i in range(2, line_count):
        line = lines[i]
        line = line.strip()
        values = line.split()
        this_time = UTCDateTime(values[0])
        if start_date_time <= this_time <= end_date_time:
            date, time = values[0].split('T')
            dateValues = date.split('-')
            timeValues = time.split(':')
            X.append(datetime.datetime(int(dateValues[0]), int(dateValues[1]),
                                       int(dateValues[2]), int(timeValues[0]), int(timeValues[1])))
            Y.append(float(values[binIndex]) * factor)

msg_lib.info(f'Maximum Y: {max(Y)}')
if len(X) <= 1:
    code = msg_lib.error("No data found", 2)
    sys.exit(code)

# Convert the column XYZ data to grid for plotting.
if verbose:
    msg_lib.info(f'PLOT SIZE: {param.plotSize}')

# The production label.
production_date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
production_label = f'{shared.production_label}'
production_label = f'{production_label} {script} {version}'
production_label = f'{production_label} {production_date} UTC'
production_label = f'{production_label} doi:{shared.ntk_doi}'

fig = plt.figure(figsize=param.plotSize)

plabel_x, plabel_y = shared.production_label_position

fig.set_facecolor('w')

xStart = datetime.datetime(int(xStartL.split('-')[0]), int(xStartL.split('-')[1]), int(xStartL.split('-')[2]), 0, 0, 0) \
         + datetime.timedelta(seconds=7200)
xEnd = datetime.datetime(int(xEndL.split('-')[0]), int(xEndL.split('-')[1]), int(xEndL.split('-')[2]), 00, 00, 00) \
       - datetime.timedelta(seconds=7200)

for i in range(0, 1):
    ax = fig.add_subplot(1, 1, i + 1)
    ax.text(plabel_x, 2 * plabel_y, production_label, horizontalalignment='left', fontsize=5, verticalalignment='top',
            transform=ax.transAxes)

    if verbose:
        msg_lib.info(f'DOT COLOR: {dotColor[i]}')
    ax.scatter(X, Y, s=dotSize[i], marker='o', alpha=1.0, color=dotColor[i], label=columnLabel[i + 1])

    # ".   " is added for proper spacing
    ax.text(xStart, 0.9 * float(ymax), ".    " + ".".join([network, station, channel]),
            horizontalalignment='left', fontsize=10, weight='bold', color=dotColor[i])

    # "   ." is added for proper spacing

    ax.set_xticklabels(list())
    ax.set_ylabel(yLabel, fontsize='small')
    plt.title(title)
    plt.ylim(ymin, float(ymax))
    plt.xlim(xminL, xmaxL)

# Format the ticks for the date axis depending on the duration.
ax.xaxis_date()
date_range = 15
if date_range < 21:
    ax.xaxis.set_major_locator(days)
    ax.xaxis.set_major_formatter(daysFmt)
elif date_range < 45:
    ax.xaxis.set_major_locator(weeks)
    ax.xaxis.set_major_formatter(daysFmt)
elif date_range < 90:
    ax.xaxis.set_major_locator(weeks)
    ax.xaxis.set_major_formatter(monthsFmt)
elif date_range < 400:
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(monthsFmt)
else:
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(yearsFmt)

#
# rotate the x labels by 60 degrees
#
for xlab in ax.get_xticklabels():
    xlab.set_rotation(60)

fig.subplots_adjust(top=0.95, right=0.95, bottom=0.2, hspace=0)
image_directory = os.path.join(param.ntkDirectory, param.imageDirectory)
file_lib.make_path(image_directory)
image_file = os.path.join(image_directory, "_".join([file_name.replace('.txt', ''), image_tag, window_tag]))
plt.savefig(f'{image_file}.eps', format="eps", dpi=300)
msg_lib.info(f'image file: {image_file}.eps')
plt.savefig(f'{image_file}.png', format="png", dpi=150)
msg_lib.info(f'image file: {image_file}.png')
plt.show()

