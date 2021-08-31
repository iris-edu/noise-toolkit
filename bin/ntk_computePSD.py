#!/usr/bin/env python

import os
import sys
import math
import importlib

import matplotlib
from matplotlib.mlab import csd

from obspy.core import UTCDateTime
from obspy.signal.spectral_estimation import get_nlnm, get_nhnm

from time import time
import datetime
import matplotlib.pyplot as plt
import numpy as np

# Import the Noise Toolkit libraries.
ntk_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

param_path = os.path.join(ntk_directory, 'param')
lib_path = os.path.join(ntk_directory, 'lib')

sys.path.append(param_path)
sys.path.append(lib_path)

import msgLib as msg_lib
import fileLib as file_lib
import staLib  as sta_lib
import sfLib as sf_lib
import tsLib as ts_lib
import utilsLib as utils_lib
import shared as shared

"""
 Name: ntk_computePSD.py - a Python 3 script to calculate the average power spectral density for a given station.

 Copyright (C) 2021  Product Team, IRIS Data Management Center

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

 History:

    2021-08-31 Manoch: v.2.1.0 This patch addresses the output file naming issue when data were read from files.
                       The bug was causing output to be written under the same file name. This patch also adds the 
                       script version to the log file.
    2021-06-23 Manoch: v.2.0.1 Fixed the issue with processing beyond requested time window when multiple local
                       files exist.
    2020-11-16 Manoch: v.2.0.0 Python 3, use of Fedcatalog, adoption of CSD changes and adoption of PEP 8 style guide.
    2019-09-09 Robert Anthony (USGS, Albuquerque Seismological Laboratory): 
                       Using CSD to compute the cross spectral density of two signals
    2017-01-18 Manoch: v.0.9.5 support for reading data and metadata from files only with no Internet requirement
    2016-11-01 Manoch: v.0.9.0 support for obtaining channel responses from local station XML response files
    2016-01-25 Manoch: v.0.8.1 support for restricted data, if user and password parameters are provided (see 
                       RestrictedData Access under http://service.iris.edu/fdsnws/dataselect/1/)
    2015-04-07 Manoch: added check for all parameter values to inform user if they are not defined. Corrected the 
                       instrument correction for SAC files that would apply
                       sensitivity in addition to instrument correction
    2015-04-06 Manoch: addressed the variable maximum period issue that was changing based on the smoothing 
                       window length
    2015-04-02 Manoch: based on feedback from Robert Anthony, in addition to nan values other non-numeric values 
                       may exist. The write that contains a flot() conversion
                       is placed in a try block so we can catch any non-numeric conversion issue and report it as 
                       user-defined NAN
    2015-03-30 Manoch: added a check to number of samples to aviod log of zero (reported by Rob Anthony)
    2015-03-17 Manoch: added the 'waterLevel' parameter to provide user with more control on how the ObsPy module 
                       shrinks values under water-level of max spec amplitude
                       when removing the instrument response.
    2015-02-24 Manoch: introduced two new parameters (performInstrumentCorrection, applyScale) to allow user avoid 
                       instrument correction also now user can turn od decon. filter
    2014-10-22 Manoch: added support for Windows installation
    2014-05-20 Manoch: added some informative message about data retrieval
                       changed format to output each channel to a separate directory and save files
                       under DOY in preparation for PQLX-type output
    2014-03-19 Manoch: added option to read waveforms from file
    2014-01-29 Manoch: created as part of the Noise Toolkit product

"""

version = 'v.2.1.0'
script = sys.argv[0]
script = os.path.basename(script)

# Initial mode settings.
timing = False
do_plot = False
verbose = False
mode_list = ['0', 'plot', 'time', 'verbose']
default_param_file = 'computePSD'
if os.path.isfile(os.path.join(param_path, f'{default_param_file}.py')):
    param = importlib.import_module(default_param_file)
else:
    code = msg_lib.error(f'could not load the default parameter file  [param/{default_param_file}.py]', 2)
    sys.exit(code)


def usage():
    """ Usage message.
    """
    sw_width = param.octaveWindowWidth
    sw_shift = param.octaveWindowShift
    print(f'\n\n{script} version {version}\n\n'
          f'A Python 3 script that calculates average power spectral densities for a given station. '
          f'The script:'
          f'\n\t- identifies the FDSN data provider for the requested station using the Fedcatalog service '
          f'\n\t  from IRIS (https://service.iris.edu/irisws/fedcatalog/1/)'
          f'\n\t- requests waveform and response data for the given station(s)/channels(s) using '
          f'ObsPy\'s FDSN client'
          f'\n\t  OR\n\t- reads user-supplied waveform data files in SAC, MSEED, CSS, etc. format from a local disk'
          f'\n\n\t  Then\n\t- computes PSDs for the waveform data and '
          f'populates a file-based PSD database'
          f'\n\nUsage:\n\t{script} to display the usage message (this message)'
          f'\n\t  OR'
          f'\n\t{script} param=FileName client=[FDSN|FILES] net=network sta=station loc=location chan=channel(s)'
          f' start=YYYY-MM-DDTHH:MM:SS end=YYYY-MM-DDTHH:MM:SS xtype=[period|frequency] plot=[0|1] verbose=[0|1]'
          f' timing=[0|1]\n'
          f'\n\tto perform computations where:'
          f'\n\t  param\t\t[default: {default_param_file}] the configuration file name '
          f'\n\t  client\t[default: {param.requestClient}] client to use to make data/metadata requests '
          f'(FDSN or FILES) '
          f'\n\t  net\t\t[required] network code'
          f'\n\t  sta\t\t[required] station code'
          f'\n\t  loc\t\t[required] location ID'
          f'\n\t  chan\t\t[default: {param.channel}] channel ID(s); separate multiple channel '
          f'codes by comma (no space)'
          f'\n\t  xtype\t\t[period or frequency, default: {param.xtype[0]}] X-axis type (period or '
          f'frequency for outputs and plots)'
          f'\n\t  start\t\t[required] start date-time (UTC) of the interval for which PSDs to be computed '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  end\t\t[required] end date-time (UTC) of the interval for which PSDs to be computed '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  sw_width\t[default: '
          f'{sw_width}] Smoothing window width in octave'
          f'\n\t  sw_shift\t[default: '
          f'{sw_shift}'
          f'] Smoothing window shift in fraction of octave'
          f'\n\t  plotnm\t[0 or 1, default {param.plotNm}] plot the New High/Low Noise Models [0|1]'
          f'\n\t  plot\t\t[0 or 1, default: {param.plot}] to run in plot mode set to 1'
          f'\n\t  timing\t[0 or 1, default: {param.timing}] to run in timing mode (set to 1 to output run times for '
          f'different segments of the script)'
          f'\n\t  verbose\t[0 or 1, default: {param.verbose}] to run in verbose mode set to 1'
          f'\n\nOutput: Data file(s) and/or plot(s) as indicated in the parameter file and by the plot option. The '
          f'complete path to each output file is displayed during the run.'
          f'\n\n\tThe output file name has the form:'
          f'\n\t\tnet.sta.loc.chan.start.window-length.xtype.txt'
          f'\n\tfor example:'
          f'\n\t\tNM.SLM.--.BHZ.2009-03-24T23:30:00.3600.period.txt'
          f'\n\nExamples:'
          f'\n\n\t- usage:'
          f'\n\tpython {script}'
          f'\n\n\t- minimum required parameters for 1.5 hour window with PSDs saved to files:'
          f'\n\tpython {script} net=TA sta=O18A loc=DASH start=2008-08-14T12:00:00 end=2008-08-14T13:30:00'
          f'\n\n\t- limit channel to BHZ, process only one hour (default) and plot the PSD:'
          f'\n\tpython {script} net=TA sta=O18A loc=DASH chan=BHZ start=2008-08-14T12:00:00 '
          f'end=2008-08-14T13:00:00 xtype=period plot=1'
          f'\n\n\t- limit channel to BHZ, process only one hour (default) and plot the PSD with more smoothing:'
          f'\n\tpython {script} param=computePSD net=TA sta=O18A loc=DASH chan=BHZ start=2008-08-14T12:00:00 '
          f'end=2008-08-14T13:00:00 xtype=period sw_width=0.5 sw_shift=0.25 plot=1'
          f'\n\n\t- limit channel to BHZ, process only one hour (default) and plot the PSD with even more smoothing:'
          f'\n\tpython {script} param=computePSD net=TA sta=O18A loc=DASH chan=BHZ start=2008-08-14T12:00:00 '
          f'end=2008-08-14T13:30:00 xtype=period sw_width=1 plot=1'
          f'\n\n\t- limit channel to BHZ but process many days of data:'
          f' \n\tpython ntk_computePSD.py param=computePSD net=NM sta=SLM  loc=DASH chan=BHZ '
          f'start=2009-03-01T00:00:00 end=2009-03-31T00:00:00 xtype=period plot=0 verbose=0'
          f'\n\n\t- try other stations and time intervals:'
          f'\n\tpython {script} net=NM sta=SLM loc=DASH chan=BHZ start=2009-11-01T12:00:00 '
          f'end=2009-11-01T14:00:00 xtype=period plot=1'
          f'\n\tpython {script} param=computePSD net=TA sta=959A loc=DASH start=2013-10-01T11:00:00 '
          f'end=2013-10-01T13:00:00 xtype=period plot=1'
          f'\n\n\t- BHZ channel for GR.BFO with data from a data center other than IRIS:'
          f'\n\tpython {script} param=computePSD net=GR sta=BFO loc=DASH chan=BHZ start=2020-10-01T00:00:00 '
          f'end=2020-10-01T01:00:00 xtype=period plot=1'
          f'\n\n\t- reads data from files by changing the client (make sure data files exist) and gets the '
          f'response from IRIS (to read responses from files, set fromFileOnly parameter to True'
          f'\n\tpython {script}  net=TA sta=W5 loc=DASH start=2014-03-17T04:30:00 end=2014-03-17T05:30:00 type=period '
          f'client=FILES plot=1'
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
    code = msg_lib.error(f' parameter file is required', 2)
    sys.exit(code)

# Import the parameter file if it exists.
if os.path.isfile(os.path.join(param_path, f'{param_file}.py')):
    param = importlib.import_module(param_file)
else:
    usage()
    code = msg_lib.error(f'bad parameter file name [{param_file}]', 2)
    sys.exit(code)

# Run parameters.
window_length = utils_lib.param(param, 'windowLength').windowLength
if not utils_lib.is_number(window_length):
    code = msg_lib.error(f'Invalid window_length  [{window_length}] in the parameter file', 2)
    sys.exit(code)

request_channel = utils_lib.get_param(args, 'chan', utils_lib.param(param, 'channel').channel, usage)
xtype = utils_lib.get_param(args, 'xtype', utils_lib.param(param, 'xtype').xtype[0], usage)
if xtype not in param.xtype:
    usage()
    code = msg_lib.error(f'Invalid xtype  [{xtype}]', 2)
    sys.exit(code)

# Set the run mode.
do_plot = utils_lib.get_param(args, 'plot', utils_lib.param(param, 'plot').plot, usage)
do_plot = utils_lib.is_true(do_plot)

plot_nm = utils_lib.get_param(args, 'plotnm', utils_lib.param(param, 'plotNm').plotNm, usage)
do_plot_nnm = utils_lib.is_true(plot_nm)

verbose = utils_lib.get_param(args, 'verbose', utils_lib.param(param, 'verbose').verbose, usage)
verbose = utils_lib.is_true(verbose)

timing = utils_lib.get_param(args, 'timing', utils_lib.param(param, 'timing').timing, usage)
timing = utils_lib.is_true(timing)

msg_lib.info(f'script: {script} {version} {len(sys.argv) - 1} args: {sys.argv}')

octaveWindowWidth = float(1.0 / 2.0)
octaveWindowShift = float(1.0 / 8.0)  # Smoothing window shift : float(1.0/8.0)= 1/8 octave shift;
# float(1.0/8.0) 1/8 octave shift, etc.

""" Smoothing window width in octave.
    For test against PQLX use 1 octave width.
    Smoothing window width : float(1.0/1.0)= 1 octave smoothing;
    float(1.0/4.0) 1/4 octave smoothing, etc."""
octave_window_width = float(utils_lib.get_param(args, 'sw_width',
                                                utils_lib.param(param, 'octaveWindowWidth').octaveWindowWidth, usage))

# Smoothing window shift : float(1.0/4.0)= 1/4 octave shift; float(1.0/8.0) 1/8 octave shift, etc.
octave_window_shift = float(utils_lib.get_param(args, 'sw_shift',
                                                utils_lib.param(param, 'octaveWindowShift').octaveWindowShift, usage))

smoothing_label = f'{octave_window_width} octave smoothing \n{octave_window_shift} octave shift'

# Turn off the display requirement if running without the plot option.
if not do_plot:
    matplotlib.use('agg')

from_file_only = utils_lib.param(param, 'fromFileOnly').fromFileOnly
request_client = utils_lib.get_param(args, 'client', utils_lib.param(param, 'requestClient').requestClient, usage)
if request_client not in ('FILES', 'FDSN'):
    usage()
    code = msg_lib.error(f'Invalid request client "{request_client}"', 3)
    sys.exit(code)
internet = not (request_client == 'FILES' and from_file_only)
msg_lib.info(f'Use Internet to get metadata: {internet}')

if internet:
    from obspy.clients.fdsn import Client

    # IRIS web service clients.
    from obspy.clients.iris import Client as IrisClient

# R 0.9.5 support for no Internet connection when from_file_only flag is set
iris_client = None
client = None
user = None
password = None
if internet:
    # If user and password parameters are provided, use them
    # R 0.8.1 support for restricted data
    iris_client = IrisClient(user_agent=utils_lib.param(param, 'userAgent').userAgent)
    if 'user' in dir(param) and 'password' in dir(param):
        user = param.user
        password = param.password

    if user is None or password is None:
        msg_lib.info('accessing no logon client')
        client = Client(user_agent=utils_lib.param(param, 'userAgent').userAgent)
    else:
        msg_lib.info(f'accessing logon client as {user}')
        client = Client(user_agent=utils_lib.param(param, 'userAgent').userAgent, user=user, password=password)
    response_directory = None
else:
    msg_lib.info('[INFO] data and metadata from files')
    response_directory = utils_lib.param(param, 'respDirectory').respDirectory

# Keep track of what you are doing.
action = str()

# Runtime arguments.
t0 = time()
t1 = utils_lib.time_it('START', t0)
msg_lib.message('START')

request_network = utils_lib.get_param(args, 'net', None, usage)
request_station = utils_lib.get_param(args, 'sta', None, usage)
request_location = sta_lib.get_location(utils_lib.get_param(args, 'loc', None, usage))

# Maximum period needed to compute value at maxT period point.
max_period = utils_lib.param(param, 'maxT').maxT * pow(2, octave_window_width / 2.0)

# Minimum frequency  needed to compute value at 1.0/maxT frequency point.
min_frequency = 1.0 / float(max_period)

if timing:
    t0 = utils_lib.time_it('ARGS', t0)

if verbose:
    msg_lib.info(f'MAX PERIOD: {utils_lib.param(param, "maxT").maxT}')
    msg_lib.info(f'CALL: {sys.argv}')

inventory = None

# Less than 3 characters station name triggers wildcards.
if len(request_station) <= 2:
    if request_client == 'IRIS':
        code = msg_lib.error('Invalid station name (for IRIS client, wildcards are not accepted. '
                             'Please use full station name)', 2)
        sys.exit(code)

    request_station = f'*{request_station}*'

# Specific start and end date and times from user.
request_start_date_time = utils_lib.get_param(args, 'start', None, usage)
try:
    request_start_datetime = UTCDateTime(request_start_date_time)
except Exception as ex:
    usage()
    code = msg_lib.error(f'Invalid start ({request_start_date_time})\n{ex}', 2)
    sys.exit(code)

request_end_date_time = utils_lib.get_param(args, 'end', None, usage)
try:
    request_end_datetime = UTCDateTime(request_end_date_time)
except Exception as ex:
    usage()
    code = msg_lib.error(f'Invalid end ({request_end_date_time})\n{ex}', 2)
    sys.exit(code)

if timing:
    t0 = utils_lib.time_it('request info', t0)

msg_lib.info(f'Requesting {request_network}.{request_location}.{request_station}.'
             f'{request_channel} from  {request_start_date_time}  to  {request_end_date_time}')

# Processing parameters.
# What the x-axis should represent.
try:
    plot_index = utils_lib.param(param, 'xtype').xtype.index(xtype)
except Exception as e:
    usage()
    code = msg_lib.error(f'Invalid plot type ({xtype})\n{e}', 2)
    sys.exit(code)

if timing:
    t0 = utils_lib.time_it('parameters', t0)

if verbose:
    msg_lib.info(f'Window From {request_start_date_time} to '
                 f'{request_end_date_time}\n')

# Window duration.
try:
    duration = int(request_end_datetime - request_start_datetime)
except Exception as e:
    msg_lib.error(f'Invalid date-time [{request_start_date_time} - {request_end_date_time}]\n{e}', 1)
    usage()
    sys.exit()

if timing:
    t0 = utils_lib.time_it('window info', t0)

if verbose:
    msg_lib.info(f'PLOTINDEX: {plot_index}\n'
                 f'Window Duration: {duration}\n'
                 f'[PAR] XLABEL: {utils_lib.param(param, "xlabel").xlabel[xtype]}\n'
                 f'[PAR] XLIM({utils_lib.param(param, "xlimMin").xlimMin}, '
                 f'{utils_lib.param(param, "xlimMax").xlimMax})'
                 f'[PAR] YLIM({utils_lib.param(param, "ylimLow").ylimLow}, '
                 f'{utils_lib.param(param, "ylimHigh").ylimHigh})')

# Request date information.
try:
    year, week, weekday = request_start_datetime.isocalendar()
except Exception as e:
    msg_lib.error(f'Invalid start date-time [{request_start_date_time}]\n{e}', 1)
    usage()
    sys.exit()

psd_db_directory = utils_lib.mkdir(utils_lib.param(param, 'psdDbDirectory').psdDbDirectory)
data_directory = utils_lib.mkdir(utils_lib.param(param, 'dataDirectory').dataDirectory)
if request_client == 'FILES':
    cat = {'Files': {'bulk': utils_lib.param(param, 'fileTag').fileTag}}
else:
    # Initiate Fedcatalog request for data.
    request_query = utils_lib.get_fedcatalog_url(request_network, request_station, request_location,
                                                 request_channel, request_start_date_time,
                                                 request_end_date_time)

    fedcatalog_url = f'{shared.fedcatalog_url}{request_query}'
    cat = ts_lib.get_fedcatalog_station(fedcatalog_url, request_start_date_time,
                                        request_end_date_time, shared.chunk_length, chunk_count=shared.chunk_count)

# Production label.
production_date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
production_label = f'{shared.production_label}'
production_label = f'{production_label} {script} {version}'
production_label = f'{production_label}\n{production_date} UTC'
production_label = f'{production_label}\ndoi:{shared.ntk_doi}'

# Get data from each Data Center.
stream = None
for _key in cat:
    st = None
    if verbose:
        msg_lib.info('Sending requests for:')
        if type(cat[_key]['bulk']) == str:
            msg_lib.info(cat[_key]['bulk'])
        else:
            for line in cat[_key]['bulk']:
                msg_lib.info(line)

    if not cat[_key]['bulk']:
        msg_lib.warning(f'Skipping data request from {_key}, no stations to request!\n')
        continue

    if request_client == 'FILES':
        msg_lib.info(f'Reading data from {cat[_key]["bulk"]}')
    else:
        msg_lib.info(f'Requesting data from {_key} via {ts_lib.get_service_url(cat, _key)}\n')

        # Set the client up for this data center.
        try:
            client = Client(ts_lib.get_service_url(cat, _key))
            st = client.get_waveforms_bulk(cat[_key]['bulk'], attach_response=True)
        except Exception as ex:
            msg_lib.warning(script, ex)

    """Start processing time segments.

      work on each window duration (1-hour)

      LOOP: WINDOW
      RA - note here we are defining the number of time-steps as the number of window shifts
      that exist within the length of the request-time

      flag to only process segments that start at the begining of the window
    """
    enforce_window_start = bool(utils_lib.param(param, 'enforceWindowStart').enforceWindowStart)

    # We only want to read as much data as we have in the stream.
    if st is not None:
        # When requesting data.
        st_starttime = max([tr.stats.starttime for tr in st])
        max_starttime = max(st_starttime, request_start_datetime)

        st_endtime = max([tr.stats.endtime for tr in st])
        min_endtime = min(st_endtime, request_end_datetime)
    else:
        # When reading files.
        max_starttime = request_start_datetime
        min_endtime = request_end_datetime

    give_warning = True
    for t_step in range(0, int(duration), int(utils_lib.param(param, 'windowShift').windowShift)):
        if timing:
            t0 = utils_lib.time_it('start WINDOW', t0)

        t_start = max_starttime + t_step
        t_end = t_start + window_length
        if t_end > min_endtime:
            t_end = min_endtime
        if t_end - t_start < window_length:
            if give_warning:
                msg_lib.warning(script, f'Interval from {t_start} to {t_end} is shorter than the '
                                        f'windowLength parameter {window_length} seconds, will skip.')
                give_warning = False
            continue

        segment_start = t_start.strftime('%Y-%m-%d %H:%M:%S.0')
        segment_start_year = t_start.strftime('%Y')
        segment_start_doy = t_start.strftime('%j')
        segment_end = t_end.strftime('%Y-%m-%d %H:%M:%S.0')
        if request_client == 'FILES':
            file_tag = file_lib.get_tag(".", [request_network, request_station, request_location, request_channel])
            msg_lib.info(f'Reading '
                         f'{file_tag} '
                         f'from {segment_start} to {segment_end} '
                         f'from {utils_lib.param(param, "requestClient").requestClient} stream')
        else:
            file_tag = file_lib.get_tag(".", [request_network, request_station, request_location, request_channel])
            msg_lib.info(f'Reading '
                         f'{file_tag} '
                         f'from {segment_start} to {segment_end} '
                         f'from {utils_lib.param(param, "requestClient").requestClient} stream')

        # Read from files but request response via Files and/or WS.
        if request_client == 'FILES':
            useClient = client
            if not internet:
                useClient = None
            inventory, st = ts_lib.get_channel_waveform_files(request_network, request_station,
                                                              request_location, request_channel,
                                                              segment_start, segment_end, useClient,
                                                              utils_lib.param(param, 'fileTag').fileTag,
                                                              resp_dir=response_directory)
        stream = st.slice(starttime=t_start, endtime=t_end, keep_empty_traces=False, nearest_sample=True)

        if stream is None or not stream:
            code = msg_lib.error(f'No data in stream', 4)
            sys.exit(code)
        else:
            st_starttime = min([tr.stats.starttime for tr in stream])
            st_endtime = max([tr.stats.endtime for tr in stream])
            if request_start_datetime >= st_endtime or request_end_datetime <= st_starttime:
                msg_lib.warning(script, f'Stream time from {st_starttime} to {st_endtime} is outside the '
                                        f'request window {request_start_datetime} to {request_end_datetime}')
                continue
            else:
                msg_lib.info(f'{script} {str(stream)}')

        for tr in stream:

            if request_start_datetime >= tr.stats.endtime or request_end_datetime <= tr.stats.starttime:
                msg_lib.warning(script, f'Trace time from {tr.stats.starttime} to {tr.stats.endtime} is outside the '
                                        f'request window {request_start_datetime} to {request_end_datetime}')
                continue
            network = tr.stats.network
            station = tr.stats.station
            location = sta_lib.get_location(tr.stats.location)
            channel = tr.stats.channel
            if verbose:
                msg_lib.info(f'Response: {tr.stats}')
            if channel == 'BDF':
                powerUnits = utils_lib.param(param, 'powerUnits').powerUnits['PA']
            else:
                powerUnits = utils_lib.param(param, 'powerUnits').powerUnits[
                    tr.stats.response.instrument_sensitivity.input_units]

            xUnits = utils_lib.param(param, 'xlabel').xlabel[xtype.lower()]
            traceKey = file_lib.get_tag('.', [network, station, location, channel])

            # We first need to define the length of sub-windows based on the user-specified parameters

            n_points = tr.stats.npts
            sampling_frequency = tr.stats.sampling_rate
            delta = float(tr.stats.delta)

            # Number of samples per window is obtained by dividing the total number of samples
            # by the number of side-by-side time windows along the trace

            # First calculate the number of points needed based on the run parameters
            #
            # AR + RA - Integer operation will always round down - so add 1
            this_n_samp = int((window_length / delta + 1) / utils_lib.param(param, 'nSegWindow').nSegWindow)
            n_samp_needed = 2 ** int(math.log(this_n_samp, 2))  # make sure it is power of 2
            if verbose:
                msg_lib.info(f'nSamp Needed:{n_samp_needed}')

            # Next calculate the number of points needed based on the trace parameters.
            this_n_samp = int(n_points / utils_lib.param(param, 'nSegWindow').nSegWindow)

            # Avoid log of bad numbers.
            if this_n_samp <= 0:
                msg_lib.warning('FFT',
                                f'needed {n_samp_needed}'
                                ' smples but no samples are available, will skip this trace')
                continue
            nfft = 2 ** int(math.log(this_n_samp, 2))  # make sure it is power of 2

            if verbose:
                msg_lib.info(f'nSamp Available: {nfft}')

            if nfft < n_samp_needed:
                msg_lib.warning('FFT', f'needed {n_samp_needed} samples but only '
                                       f'{nfft} samples are available, will skip this trace')
                continue

            # see if segment starts within less than a sample from the beginning of window
            if enforce_window_start and abs(tr.stats.starttime - t_start) > delta:
                msg_lib.warning('FFT', f'parameter enforce_window_start is set '
                                       f'and the segment does not start within less '
                                       f'than a sample from the beginning of window, will skip this trace')
                continue

            # Define sub-window overlap based on user specified parameters - convert to decimal percentage
            windlap = utils_lib.param(param, 'percentOverlap').percentOverlap * (1. / 100)
            csd_label = f'power spectral density \n{window_length} s window / {windlap * 100}% overlap'

            # Do the CSD
            power, freq = csd(tr.data, tr.data, NFFT=nfft,
                              noverlap=nfft * windlap, Fs=1. / delta,
                              scale_by_freq=True)

            # Remove first Point
            freq = freq[1:]
            power = power[1:]

            period = 1. / freq

            # make power a real quantity
            power = np.abs(power)

            # Remove the Response
            resp, freqs = tr.stats.response.get_evalresp_response(delta,
                                                                  nfft, output=utils_lib.param(param, 'unit').unit)
            resp = abs(resp)
            resp = resp[1:]

            power = power / (np.abs(resp) ** 2)

            smooth_x = []
            smooth_psd = []

            # Smoothing.
            if timing:
                t0 = utils_lib.time_it('start SMOOTHING ', t0)

            msg_lib.info(f'SMOOTHING window {octave_window_width} shift '
                         f'{octave_window_shift}')
            if xtype == 'period':
                #
                if str(utils_lib.param(param, 'xStart').xStart[plot_index]) == 'Nyquist':
                    smooth_x, smooth_psd = sf_lib.smooth_nyquist(xtype, period, power, sampling_frequency,
                                                                 octave_window_width,
                                                                 octave_window_shift,
                                                                 utils_lib.param(param, 'maxT').maxT)
                else:
                    smooth_x, smooth_psd = sf_lib.smooth_period(period, power, sampling_frequency,
                                                                octave_window_width,
                                                                octave_window_shift,
                                                                utils_lib.param(param, 'maxT').maxT,
                                                                float(utils_lib.param(param, 'xStart').xStart[
                                                                          plot_index]))
            else:
                frequency = np.array(np.arange(1, (nfft / 2) + 1) / float(nfft * delta))

                if str(utils_lib.param(param, 'xStart').xStart[plot_index]) == 'Nyquist':
                    smooth_x, smooth_psd = sf_lib.smooth_nyquist(xtype, frequency, power, sampling_frequency,
                                                                 octave_window_width,
                                                                 octave_window_shift,
                                                                 min_frequency)
                else:
                    smooth_x, smooth_psd = sf_lib.smooth_frequency(frequency, power, sampling_frequency,
                                                                   octave_window_width,
                                                                   octave_window_shift,
                                                                   min_frequency,
                                                                   float(
                                                                       utils_lib.param(param, 'xStart').xStart[
                                                                           plot_index]))

            if timing:
                t0 = utils_lib.time_it(
                    f'SMOOTHING window {octave_window_width} shift '
                    f'{octave_window_shift} DONE', t0)

            # get the response information

            msg_lib.info(tr.stats.response)

            # Convert to dB.
            power = 10.0 * np.log10(power)
            smooth_psd = 10.0 * np.log10(smooth_psd)

            # Create output paths if they do not exist.
            if utils_lib.param(param, 'outputValues').outputValues > 0:
                filePath, psd_file_tag = file_lib.get_dir(data_directory,
                                                          psd_db_directory,
                                                          network,
                                                          station, location, channel)
                filePath = os.path.join(filePath, segment_start_year, segment_start_doy)
                file_lib.make_path(filePath)

                # Output is based on the xtype.
                if verbose:
                    msg_lib.info(f'trChannel.stats: {tr.stats} '
                                 f'REQUEST: {segment_start} '
                                 f'TRACE: {tr.stats.starttime.strftime("%Y-%m-%dT%H:%M:%S")} '
                                 f'DELTA: {tr.stats.delta} '
                                 f'SAMPLES: '
                                 f'{int(window_length / float(tr.stats.delta) + 1)} ')

                trace_time = tr.stats.starttime
                # Avoid file names with 59.59.
                trace_time += datetime.timedelta(microseconds=10)
                time_label = trace_time.strftime('%Y-%m-%dT%H:%M:%S')
                tagList = [psd_file_tag, time_label,
                           f'{window_length}', xtype]
                output_file_name = file_lib.get_file_name(utils_lib.param(
                    param, 'namingConvention').namingConvention, filePath, tagList)
                msg_lib.message(f'OUTPUT: writing to {output_file_name}')

                with open(output_file_name, 'w') as output_file:

                    # Output the header.
                    output_file.write('%s %s\n' % (xUnits, powerUnits))

                    # Output data.
                    for i_x, v_x in enumerate(smooth_x):
                        output_file.write(f'{float(smooth_x[i_x]):11.6f} {float(smooth_psd[i_x]):11.4f}\n')

            # Start plotting.
            if (utils_lib.param(param, 'plotSpectra').plotSpectra > 0 or utils_lib.param(param,
                                                                                         'plotSmooth').plotSmooth > 0) \
                    and do_plot:
                action = 'Plot 2'

                if timing:
                    t0 = utils_lib.time_it('start PLOT ', t0)

                if verbose:
                    msg_lib.info('POWER: ' + str(len(power)) + '\n')

                fig = plt.figure()
                fig.subplots_adjust(hspace=.2)
                fig.subplots_adjust(wspace=.2)
                fig.set_facecolor('w')

                ax311 = plt.subplot(111)
                ax311.set_xscale('log')
                plabel_x, plabel_y = shared.production_label_position
                ax311.text(plabel_x, plabel_y, production_label, horizontalalignment='left', fontsize=5,
                           verticalalignment='top',
                           transform=ax311.transAxes)

                if do_plot_nnm:
                    nlnm_x, nlnm_y = get_nlnm()
                    nhnm_x, nhnm_y = get_nhnm()
                    if xtype != 'period':
                        nlnm_x = 1.0 / nlnm_x
                        nhnm_x = 1.0 / nhnm_x
                    plt.plot(nlnm_x, nlnm_y, lw=1, ls=':', c='k', label='NLNM, NHNM')
                    plt.plot(nhnm_x, nhnm_y, lw=1, ls=':', c='k')

                # Period for the x-axis.
                if xtype == 'period':
                    if utils_lib.param(param, 'plotSpectra').plotSpectra:
                        plt.plot(period, power, utils_lib.param(param, 'colorSpectra').colorSpectra, label=csd_label)
                    if utils_lib.param(param, 'plotSmooth').plotSmooth:
                        plt.plot(smooth_x, smooth_psd, color=utils_lib.param(param, 'colorSmooth').colorSmooth,
                                 label=smoothing_label)

                # Frequency for the x-axis.
                else:
                    if utils_lib.param(param, 'plotSpectra').plotSpectra:
                        plt.plot(frequency, power, utils_lib.param(param, 'colorSpectra').colorSpectra, label=csd_label)
                    if utils_lib.param(param, 'plotSmooth').plotSmooth:
                        plt.plot(smooth_x, smooth_psd, color=utils_lib.param(param, 'colorSmooth').colorSmooth,
                                 label=smoothing_label)

                plt.xlabel(xUnits)
                try:
                    plt.xlim(utils_lib.param(param, 'xlimMin').xlimMin[channel][plot_index],
                             utils_lib.param(param, 'xlimMax').xlimMax[channel][plot_index])
                except Exception as ex:
                    msg_lib.warning(script, f'xlimMin, xlimMax parameter error {ex}')

                plt.ylabel(channel + ' ' + powerUnits)

                try:
                    plt.ylim(
                        [utils_lib.param(param, 'ylimLow').ylimLow[channel],
                         utils_lib.param(param, 'ylimHigh').ylimHigh[channel]])
                except Exception as ex:
                    msg_lib.warning(script, f'ylimLow, ylimHigh parameter error {ex}')

                plt.title(f'{network}.{station}.{location}.{channel} from  {segment_start} to {segment_end}', size=10)

                if timing:
                    t0 = utils_lib.time_it('show PLOT ', t0)
                x, y = shared.production_label_position
                ax311.legend(frameon=False, prop={'size': 6})
                plt.show()
t0 = t1
t0 = utils_lib.time_it('END', t0)
