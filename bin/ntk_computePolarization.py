#!/usr/bin/env python

import os
import sys
import importlib

import matplotlib.pyplot as plt
import numpy as np
from numpy import linalg as eigen

import math
from obspy.core import UTCDateTime
from obspy.signal.spectral_estimation import get_nlnm, get_nhnm

from time import time
import datetime

# Import the Noise Toolkit libraries.
ntk_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

param_path = os.path.join(ntk_directory, 'param')
lib_path = os.path.join(ntk_directory, 'lib')

sys.path.append(param_path)
sys.path.append(lib_path)

import msgLib as msg_lib
import staLib as sta_lib
import tsLib as ts_lib
import utilsLib as utils_lib
import fileLib as file_lib
import polarLib as polar_lib
import shared as shared
import sfLib as sf_lib

"""
  Name: ntk_computePolarization.py - a ObsPy 3 script to calculate polarization parameters
        for a given station 

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

  HISTORY:

    2021-08-31 Manoch: v.2.1.0 This patch addresses the output file naming issue when data were read from files.
                       The bug was causing output to be written under the same file name. This patch also makes some 
                       PEP 8 style fixes and adds the script version to the log file.
    2021-06-23 Manoch: v.2.0.1 Fixed the issue with processing beyond requested time window when multiple local
                       files exist.
     2020-11-16 Manoch: v.2.0.0 Python 3, use of Fedcatalog and adoption of PEP 8 style guide.
     2020-09-25 Timothy C. Bartholomaus, University of Idaho: conversion to python 3
     2017-01-18 Manoch: v.0.6.5 support for reading data and metadata from files only with no Internet requirement
     2016-11-01 Manoch: v.0.6.0 support for obtaining channel responses from local station XML response files
     2016-01-25 Manoch: v.0.5.1 added support for accessing restricted data via user and password
     2015-09-02 Manoch: v.0.5.0 ready for release
     2015-06-16 Manoch: updated based on the latest ntk_computePSD.py
     2015-04-07 Manoch: added check for all parameter values to inform user if they are not defined. Corrected the 
                        instrument correction for SAC files that would apply
                        sensitivity in addition to instrument correction
     2015-04-06 Manoch: addressed the variable maximum period issue that was changing based on the smoothing window 
                        length
     2015-04-02 Manoch: based on feedback from Robert Anthony, in addition to nan values other non-numeric values may 
                        exist. The write that contains a flot() conversion
                        is placed in a try block so we can catch any non-numeric conversion issue and report it as 
                        user-defined NAN
     2015-03-30 Manoch: added a check to number of samples to aviod log of zero (reported by Rob Anthony)
     2015-03-17 Manoch: added the "waterLevel" parameter to provide user with more control on how the ObsPy module 
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
default_param_file = 'computePolarization'
if os.path.isfile(os.path.join(param_path, f'{default_param_file}.py')):
    param = importlib.import_module(default_param_file)
else:
    code = msg_lib.error(f'could not load the default parameter file  [param/{default_param_file}.py]', 2)
    sys.exit(code)


def usage():
    """ Usage message.
    """

    print(f'\n\n{script} version {version}\n\n'
          f'A Python 3 script to calculate polarization parameters for a given station as described by: '
          f'\n\n\tKoper, K.D., Hawley, V.L. Frequency dependent polarization analysis of ambient seismic noise recorded'
          f'\n\tat a broadband seismometer in the central United States. Earthq Sci 23, 439–447 (2010). '
          f'\n\thttps://doi.org/10.1007/s11589-010-0743-5\n\n'
          f'\tThis script is a standalone script that directly computes the spectra of the input waveform data in order'
          f'\n\tto form the corresponding spectra covariance matrix for polarization analysis.'
          f'\n\n\tTo perform polarization computations, the script:'
          f'\n\t- identifies the FDSN data provider for the requested station using the Fedcatalog service '
          f'\n\t  from IRIS (https://service.iris.edu/irisws/fedcatalog/1/)'
          f'\n\t- then requests waveform and response data for the given station(s)/channels(s) using the '
          f'ObsPy\'s FDSN client'
          f'\n\t  OR\n\t- reads user-supplied waveform data files in SAC, MSEED, CSS, etc. format from a local disk'
          f'\n\n\t  Then\n\t- computes the spectra of the input waveform data'
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
          f'\n\t  xtype\t\t[period or frequency, default: {param.xType[0]}] X-axis type (period or '
          f'frequency for outputs and plots)'
          f'\n\t  start\t\t[required] start date-time (UTC) of the interval for which PSDs to be computed '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  end\t\t[required] end date-time (UTC) of the interval for which PSDs to be computed '
          f'(format YYYY-MM-DDTHH:MM:SS)'
          f'\n\t  sw_width\t[default: '
          f'{param.octaveWindowWidth}'
          f'] Smoothing window width in octave'
          f'\n\t  sw_shift\t[default: '
          f'{param.octaveWindowShift}'
          f'] Smoothing window shift in fraction of octave'
          f'\n\t  plot\t\t[0 or 1, default: {param.plot}] to run in plot mode set to 1'
          f'\n\t  plotnm\t[0 or 1, default {param.plotNm}] plot the New High/Low Noise Models [0|1]'
          f'\n\t  timing\t[0 or 1, default: {param.timing}] to run in timing mode (set to 1 to output run times for '
          f'different segments of the script)'
          f'\n\t  verbose\t[0 or 1, default: {param.verbose}] to run in verbose mode set to 1'
          f'\n\nOutput: Polarization sata file(s) are stored under the Polarization Database directory(data/polarDb/)'
          f'complete path to each output file is displayed during the run.'
          f'\n\n\tThe output file name has the form:'
          f'\n\t\tnet.sta.loc.channels.start.window-length.xtype.txt'
          f'\n\tfor example:'
          f'\n\t\tTA.O18A.--.BHZ_BHE_BHN.2008-08-14T12:00:00.3600.period.txt'
          f'\n\nExamples:'
          f'\n\n\t-usage:'
          f'\n\tpython {script}'
          f'\n\n\t- compute and output polarization parameters to files:'
          f'\n\tpython {script} net=TA sta=O18A loc=DASH start=2008-08-14T12:00:00 end=2008-08-14T13:30:00'
          f'\n\n\t- compute and output polarization parameters (as a function of  frequency) '
          f'to files and also plot them:'
          f'\n\tpython {script} net=TA sta=O18A loc=DASH start=2008-08-14T12:00:00 '
          f'end=2008-08-14T13:00:00 xtype=frequency plot=1'
          f'\n\n\t- apply more smoothing:'
          f'\n\tpython {script} param={default_param_file} net=TA sta=O18A loc=DASH start=2008-08-14T12:00:00 '
          f'end=2008-08-14T13:00:00 xtype=period sw_width=0.5 sw_shift=0.25 plot=1'
          f'\n\tpython {script} param={default_param_file} net=TA sta=O18A loc=DASH start=2008-08-14T12:00:00 '
          f'end=2008-08-14T13:30:00 xtype=period sw_width=1 plot=1'
          f'\n\tpython {script} param={default_param_file} net=TA sta=959A loc=DASH start=2013-10-01T11:00:00 '
          f'end=2013-10-01T13:00:00 xtype=period plot=1'
          f'\n\n\t- read data from files by changing the client (make sure data files exist)'
          f'\n\tpython {script} net=TA sta=O18A loc=DASH start=2008-08-14T12:00:00 end=2008-08-14T13:30:00 type=period '
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
    code = msg_lib.error(f'{script}, parameter file is required', 2)
    sys.exit(code)

# Import the parameter file if it exists.
if os.path.isfile(os.path.join(param_path, f'{param_file}.py')):
    param = importlib.import_module(param_file)
else:
    usage()
    code = msg_lib.error(f'{script}, bad parameter file name [{param_file}]', 2)
    sys.exit(code)

# Run parameters.
window_length = utils_lib.param(param, 'windowLength').windowLength
if not utils_lib.is_number(window_length):
    code = msg_lib.error(f'{script}, Invalid window_length  [{window_length}] in the parameter file', 2)
    sys.exit(code)

request_channel = utils_lib.get_param(args, 'chan', utils_lib.param(param, 'channel').channel, usage)
xtype = utils_lib.get_param(args, 'xtype', utils_lib.param(param, 'xType').xType[0], usage)
if xtype not in param.xType:
    usage()
    code = msg_lib.error(f'{script}, Invalid xtype  [{xtype}]', 2)
    sys.exit(code)

# Set the run mode.
do_plot = utils_lib.get_param(args, 'plot', utils_lib.param(param, 'plot').plot, usage)
do_plot = utils_lib.is_true(do_plot)

plot_nnm = utils_lib.get_param(args, 'plotnm', utils_lib.param(param, 'plotNm').plotNm, usage)
do_plot_nnm = utils_lib.is_true(plot_nnm)

verbose = utils_lib.get_param(args, 'verbose', utils_lib.param(param, 'verbose').verbose, usage)
verbose = utils_lib.is_true(verbose)
msg_lib.info(f'Verbose: {verbose}')

timing = utils_lib.get_param(args, 'timing', utils_lib.param(param, 'timing').timing, usage)
timing = utils_lib.is_true(timing)

if verbose:
    msg_lib.info(f'{script}, script: {script} {len(sys.argv) - 1} args: {sys.argv}')

""" Smoothing window width in octave.
    For test against PQLX use 1 octave width.
    Smoothing window width : float(1.0/1.0)= 1 octave smoothing;
    float(1.0/4.0) 1/4 octave smoothing, etc."""
octave_window_width = float(utils_lib.get_param(args, 'sw_width',
                                                utils_lib.param(param, 'octaveWindowWidth').octaveWindowWidth, usage))
octave_window_shift = float(utils_lib.get_param(args, 'sw_shift',
                                                utils_lib.param(param, 'octaveWindowShift').octaveWindowShift, usage))

from_file_only = utils_lib.param(param, 'fromFileOnly').fromFileOnly
request_client = utils_lib.get_param(args, 'client',
                                     utils_lib.param(param, 'requestClient').requestClient, usage)
if request_client not in ('FILES', 'FDSN'):
    usage()
    code = msg_lib.error(f'{script}, Invalid request client "{request_client}"', 3)
    sys.exit(code)
internet = not (request_client == 'FILES' and from_file_only)
msg_lib.info(f'{script}, Use Internet to get metadata: {internet}')

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
        msg_lib.info(f'{script}, accessing no logon client')
        client = Client(user_agent=utils_lib.param(param, 'userAgent').userAgent)
    else:
        msg_lib.info(f'{script}, accessing logon client as {user}')
        client = Client(user_agent=utils_lib.param(param, 'userAgent').userAgent, user=user, password=password)
    response_directory = None
else:
    msg_lib.info(f'{script}, data and metadata from files')
    response_directory = utils_lib.param(param, 'respDirectory').respDirectory

# Keep track of what you are doing.
action = str()

# Runtime arguments.
t0 = time()
t1 = utils_lib.time_it(f'START', t0)
msg_lib.message(f'{script} {version}, START')

request_network = utils_lib.get_param(args, 'net', None, usage)
request_station = utils_lib.get_param(args, 'sta', None, usage)
request_location = sta_lib.get_location(utils_lib.get_param(args, 'loc', None, usage))

inventory = None

# Get a sorted list of valid channels to be used for stream QC later.
try:
    sorted_channel_list = list()
    for i in range(len(param.channelGroups)):
        sorted_channel_list.append(sorted(param.channelGroups[i]))
except Exception as e:
    code = msg_lib.error(f'{script}, check the channelGroups parameter in the parameter file {e}', 2)
    sys.exit(code)

# Maximum period needed to compute value at maxT period point.
max_period = utils_lib.param(param, 'maxT').maxT * pow(2, octave_window_width / 2.0)

# Minimum frequency  needed to compute value at 1.0/maxT frequency point.
min_frequency = 1.0 / float(max_period)

if timing:
    t0 = utils_lib.time_it('ARGS', t0)

if verbose:
    msg_lib.info(f'{script}, MAX PERIOD: {max_period}')
    msg_lib.info(f'{script}, CALL: {sys.argv}')

inventory = None

# Less than 3 characters station name triggers wildcards.
if len(request_station) <= 2:
    if request_client == 'IRIS':
        msg_lib.error(f'{script}, Invalid station name (for IRIS client, wildcards are not accepted. '
                      'Please use full station name)', 2)
        sys.exit()

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
    code = msg_lib.error(f'Invalid end ({request_end_datetime})\n{ex}', 2)
    sys.exit(code)

if timing:
    t0 = utils_lib.time_it('request info', t0)

msg_lib.info(f'{script}, Requesting {request_network}.{request_location}.{request_station}.'
             f'{request_channel} from  {request_start_date_time}  to  {request_end_date_time}')

# Production label.
production_date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
production_label = f'{shared.production_label}'
production_label = f'{production_label} {script} {version}'
production_label = f'{production_label}\n{production_date} UTC'
production_label = f'{production_label}\ndoi:{shared.ntk_doi}'

# Processing parameters.
# What the x-axis should represent.
try:
    plot_index = utils_lib.param(param, 'xType').xType.index(xtype)
except Exception as e:
    msg_lib.error(f'{script}, Invalid plot type ({xtype})\n{e}', 2)
    usage()
    sys.exit()

if timing:
    t0 = utils_lib.time_it('parameters', t0)

if verbose:
    msg_lib.info(f'{script}, Window From {request_start_date_time} to '
                 f'{request_end_date_time}\n')

# Window duration.
try:
    duration = int(request_end_datetime - request_start_datetime)
except Exception as e:
    msg_lib.error(f'{script}, Invalid date-time [{request_start_date_time} - {request_end_date_time}]\n{e}', 1)
    usage()
    sys.exit()

if timing:
    t0 = utils_lib.time_it('window info', t0)

if verbose:
    msg_lib.info(f'{script}, plot_index: {plot_index} '
                 f'Window Duration: {duration} '
                 f'[PAR] XLABEL: {utils_lib.param(param, "xlabel").xlabel[xtype]} '
                 f'[PAR] XLIM({utils_lib.param(param, "xlimMin").xlimMin}, '
                 f'{utils_lib.param(param, "xlimMax").xlimMax})'
                 f'[PAR] YLIM({utils_lib.param(param, "ylimLow").ylimLow}, '
                 f'{utils_lib.param(param, "ylimHigh").ylimHigh})')

# Request date information.
try:
    year, week, weekday = request_start_datetime.isocalendar()
except Exception as e:
    msg_lib.error(f'{script}, Invalid start date-time [{request_start_date_time}]\n{e}', 1)
    usage()
    sys.exit()

if request_client == 'FILES':
    cat = {'Files': {'bulk': utils_lib.param(param, 'fileTag').fileTag}}
else:
    # Initiate Fedcatalog request for data.
    request_query = utils_lib.get_fedcatalog_url(request_network, request_station, request_location,
                                                 request_channel, request_start_date_time,
                                                 request_end_date_time)

    fedcatalog_url = f'{shared.fedcatalog_url}{request_query}'
    cat = ts_lib.get_fedcatalog_station(fedcatalog_url, request_start_date_time,
                                        request_end_date_time, shared.chunk_length)

# Production label.
production_date = datetime.datetime.utcnow().replace(microsecond=0).isoformat()
production_label = f'{shared.production_label}'
production_label = f'{production_label} {script} {version}'
production_label = f'{production_label} {production_date} UTC'
production_label = f'{production_label} doi:{shared.ntk_doi}'

# Get data from the data center and put them all in one stream.
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
        msg_lib.warning(f'{script}, Skipping data request from {_key}, no stations to request!\n')
        continue

    if request_client == 'FILES':
        msg_lib.info(f'{script}, Reading data from {cat[_key]["bulk"]}')
    else:
        msg_lib.info(f'{script}, Requesting data from {_key} via {ts_lib.get_service_url(cat, _key)}\n')

        # Set the client up for this data center.
        try:
            client = Client(ts_lib.get_service_url(cat, _key))
            st = client.get_waveforms_bulk(cat[_key]['bulk'], attach_response=True)
            if stream is None:
                stream = st.copy()
            else:
                # We can only append a single Trace object to the current Stream object.
                for tr in st:
                    stream.append(tr.copy())
        except Exception as ex:
            msg_lib.warning(f'{script}, {ex}')

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

    """Start processing time segments.
    
      work on each window duration (1-hour)
    
      LOOP: WINDOW
      RA - note here we are defining the number of time-steps as the number of window shifts
      that exist within the length of the request-time
    
      flag to only process segments that start at the begining of the window
    """
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
        title = f'{file_lib.get_tag(".", [request_network, request_station, request_location])} {request_channel} ' \
                f'from {segment_start} to {segment_end}'

        if param.doSmoothing:
            title = f'{title}\nSmoothing window width {octave_window_width} octave; shift {octave_window_shift} octave'

        msg_lib.message(title)
        if request_client == 'FILES':
            file_tag = file_lib.get_tag(".", [request_network, request_station, request_location, request_channel])
            msg_lib.info(f'{script}, Reading '
                         f'{file_tag} '
                         f'from {segment_start} to {segment_end} '
                         f'from {utils_lib.param(param, "requestClient").requestClient}')
        else:
            file_tag = file_lib.get_tag(".", [request_network, request_station, request_location, request_channel])
            msg_lib.info(f'{script}, Requesting '
                         f'{file_tag} '
                         f'from {segment_start} to {segment_end} '
                         f'from {utils_lib.param(param, "requestClient").requestClient}')

        # Read from files but request response via Files and/or WS.
        if request_client == 'FILES':
            useClient = client
            if not internet:
                useClient = None
            inventory, stream = ts_lib.get_channel_waveform_files(request_network, request_station,
                                                                  request_location, request_channel,
                                                                  segment_start, segment_end, useClient,
                                                                  utils_lib.param(param, 'fileTag').fileTag,
                                                                  resp_dir=response_directory)

        st = stream.slice(starttime=t_start, endtime=t_end, keep_empty_traces=False, nearest_sample=True)
        msg_lib.message(f'Slice stream between {t_start} and {t_end}')

        # Did we manage to get the data?
        if st is None or not st:
            msg_lib.warning('Channel Waveform', f'No data available for '
                                                f'{request_network}.{request_station}.{request_location}.'
                                                f'{request_channel}')
            continue
        else:
            st_starttime = min([tr.stats.starttime for tr in st])
            st_endtime = max([tr.stats.endtime for tr in st])
            if request_start_datetime >= st_endtime or request_end_datetime <= st_starttime:
                msg_lib.warning(script, f'Stream time from {st_starttime} to {st_endtime} is outside the '
                                        f'request window {request_start_datetime} to {request_end_datetime}')
                continue
            else:
                qc_records = ts_lib.qc_3c_stream(st, param.windowLength,
                                                 utils_lib.param(param, 'nSegWindow').nSegWindow,
                                                 sorted_channel_list, param.channelGroups, verbose)
            if verbose:
                msg_lib.info(f'{script}, stream length: {len(st)}s')
                msg_lib.info(f'{script}, QC-passed records: {qc_records}')

        trace_key_List = list()
        traceChannel = [None, None, None]
        channel = [None, None, None]
        num_points = [None, None, None]

        # For stream_index in qc_records:
        frequency = list()
        period = list()
        stChannel = None
        channel_tr = list()
        channel = list()

        # Get traces for the 3 channels.
        for _i in qc_records:
            channel_tr.append(st[_i])
            channel.append(channel_tr[-1].stats.channel)
        if not channel_tr:
            continue
        # Correct for instrument response.
        for _i in range(len(channel_tr)):
            try:
                if param.demean:
                    channel_tr[_i].detrend("demean")

                # Remove the instrument response?
                if param.performInstrumentCorrection:
                    msg_lib.info(f'Removing response from {channel[_i]}')
                    if param.deconFilter1 <= 0 and param.deconFilter2 <= 0 \
                            and param.deconFilter3 <= 0 and param.deconFilter4 <= 0:
                        msg_lib.info(f'NO DECON FILTER APPLIED')
                        channel_tr[_i].remove_response(output=param.unit, pre_filt=None, taper=False, zero_mean=False,
                                                       water_level=param.waterLevel)
                    else:
                        msg_lib.info(f'DECON FILTER {param.deconFilter} APPLIED')
                        channel_tr[_i].remove_response(output=param.unit,
                                                       pre_filt=param.deconFilter,
                                                       taper=False, zero_mean=False, water_level=param.waterLevel)
                # Do not remove the instrument response but apply the sensitivity.
                elif param.applyScale:
                    msg_lib.info(f'Not removing response from {channel[_i]} but applying sensitivity '
                                 f'{channel_tr[_i].stats.response.instrument_sensitivity.value}')
                    channel_tr[_i].data /= float(channel_tr[_i].stats.response.instrument_sensitivity.value)

            except Exception as ex:
                code = msg_lib.error(f'Removing response from {channel[_i]} failed: {ex}')
                sys.exit(4)

        t0 = utils_lib.time_it('Removed response', t0)

        # net, sta, loc should be the same, get them from the 1st channel.
        network = channel_tr[0].stats.network
        station = channel_tr[0].stats.station
        location = sta_lib.get_location(channel_tr[0].stats.location)

        if verbose:
            msg_lib.info(f'{script}, received: CHANNEL 1 {channel_tr[0].stats}')
            msg_lib.info(f'{script}, received: CHANNEL 2 {channel_tr[1].stats}')
            msg_lib.info(f'{script}, received: CHANNEL 3 {channel_tr[2].stats}')

        power_units = utils_lib.param(param, 'powerUnits').powerUnits[
            channel_tr[0].stats.response.instrument_sensitivity.input_units.upper()]

        x_units = utils_lib.param(param, 'xlabel').xlabel[xtype.lower()]
        header = utils_lib.param(param, 'header').header[xtype.lower()]

        # Create a or each channel.
        trace_key_1 = file_lib.get_tag(".", [network, station, location, channel[0]])
        trace_key_2 = file_lib.get_tag(".", [network, station, location, channel[1]])
        trace_key_3 = file_lib.get_tag(".", [network, station, location, channel[2]])
        channelTag = '_'.join([channel[0], channel[1], channel[2]])

        if verbose:
            msg_lib.info(f'{script}, processing {trace_key_1}, {trace_key_2}, {trace_key_3}')

        if timing:
            t0 = utils_lib.time_it('got WAVEFORM', t0)

        # Get the shortest trace length.
        num_points = np.min([channel_tr[0].stats.npts, channel_tr[1].stats.npts, channel_tr[2].stats.npts])

        # Sampling should be the same, get it from the 1st channel.
        sampling_frequency = channel_tr[0].stats.sampling_rate
        delta = float(channel_tr[0].stats.delta)

        # Construct the time array.
        trace_time = np.arange(num_points) / sampling_frequency

        if timing:
            t0 = utils_lib.time_it('build trace time', t0)

        if verbose:
            msg_lib.info(f'{script}, got number of points as {num_points}')
            msg_lib.info(f'{script}, got sampling frequency as {sampling_frequency}')
            msg_lib.info(f'{script}, got sampling interval as {delta}')
            msg_lib.info(f'{script}, got time as {trace_time}')

        # Calculate FFT parameters
        # Number of samples per window is obtained by dividing the total number of samples
        # by the number of side-by-side time windows along the trace

        # First calculate the number of points needed based on the run parameters.
        this_num_sample = int((float(utils_lib.param(param, 'windowLength').windowLength) / delta + 1) /
                              utils_lib.param(param, 'nSegWindow').nSegWindow)
        num_samples_needed = 2 ** int(math.log(this_num_sample, 2))  # make sure it is power of 2
        msg_lib.info(f'{script}, num_samples Needed: {num_samples_needed}')

        # Next calculate the number of points needed based on the trace parameters.
        this_num_sample = int(num_points / utils_lib.param(param, 'nSegWindow').nSegWindow)

        # Avoid log of bad numbers.
        if this_num_sample <= 0:
            msg_lib.warning('FFT',
                            f'needed {num_samples_needed} smples but no samples are available, will skip this trace')
            continue
        num_samples = 2 ** int(math.log(this_num_sample, 2))  # make sure it is power of 2
        msg_lib.info(f'{script}, num_samples Available: {num_samples}')

        if num_samples < num_samples_needed:
            msg_lib.warning("FFT", f'needed {num_samples_needed} samples but only {num_samples}'
                                   f' samples are available, will skip this trace')
            continue

        n_shift = int(num_samples * (1.0 - float(utils_lib.param(param, 'percentOverlap').percentOverlap) / 100.0))

        if verbose:
            msg_lib.info(f'{script}, FFT param.nSegWindow, num_samples,n_shift: '
                         f'{utils_lib.param(param, "nSegWindow").nSegWindow}, {num_samples}, {n_shift}')

        # initialize the spectra
        # The size of m11 is half of the num_samples, as data are real and
        # and we only need the positive frequency portion
        action = "initialize the spectra"
        spec_length = int(num_samples / 2) + 1
        m11 = np.zeros(spec_length, dtype=np.complex)
        m12 = np.zeros(spec_length, dtype=np.complex)
        m13 = np.zeros(spec_length, dtype=np.complex)
        m22 = np.zeros(spec_length, dtype=np.complex)
        m23 = np.zeros(spec_length, dtype=np.complex)
        m33 = np.zeros(spec_length, dtype=np.complex)

        # Build the tapering window.
        action = "taper"
        taper_window = np.hanning(num_samples)

        # Loop through windows and calculate the spectra.
        action = "loop"
        start_index = 0
        end_index = 0

        # Go through segment.
        if verbose:
            msg_lib.info(f'{script}, num_samples: {num_samples}')
            msg_lib.info(f'{script}, DELTA: {delta}')

        segments_count = 0
        for n in range(0, utils_lib.param(param, 'nSegments').nSegments):
            if timing:
                t0 = utils_lib.time_it('segment ' + str(n), t0)

            # Each segment starts at start_index and ends at end_index-1.
            end_index = start_index + num_samples

            if verbose:
                msg_lib.info(f'{script}, start_index: {start_index}')
                msg_lib.info(f'{script}, end_index: {end_index}')

            time_segment = list()
            channel_segment_ = list()

            # Extract the segments
            # using Welch's method. Segments are length num_samples with each segment
            # int(num_samples * (1.0-(param.percentOverlap / 100))) units apart.
            action = "extract the segments"
            try:
                # Load start_index through end_index - 1.
                if verbose:
                    msg_lib.info(f'{script}, TIME SEGMENT: {start_index}, {end_index}, {trace_time[start_index]}, '
                                 f'{trace_time[end_index]}')
                time_segment = trace_time[start_index:end_index]

                if verbose:
                    msg_lib.info(f'{script}, CHANNEL SEGMENT: {start_index}, {end_index}')
                channel_segment_1 = channel_tr[0].data[start_index:end_index]
                channel_segment_2 = channel_tr[1].data[start_index:end_index]
                channel_segment_3 = channel_tr[2].data[start_index:end_index]
                segments_count += 1

            except Exception as ex:
                code = msg_lib.error(
                    f'{script}, failed to extract segment from location {start_index} to {end_index} {ex}', 4)
                sys.exit(code)

            # Remove the mean.
            action = "remove mean"
            channel_segment_1 = channel_segment_1 - np.mean(channel_segment_1)
            channel_segment_2 = channel_segment_2 - np.mean(channel_segment_2)
            channel_segment_3 = channel_segment_3 - np.mean(channel_segment_3)

            # Apply the taper.
            action = "apply the taper"
            if verbose:
                msg_lib.info(f'{action}, {len(channel_segment_1)}, {len(taper_window)}')
                msg_lib.info(f'{action}, {len(channel_segment_2)}, {len(taper_window)}')
                msg_lib.info(f'{action}, {len(channel_segment_3)}, {len(taper_window)}')
            channel_segment_1 = channel_segment_1 * taper_window
            channel_segment_2 = channel_segment_2 * taper_window
            channel_segment_3 = channel_segment_3 * taper_window

            # FFT
            # data values are real, so the output of FFT is Hermitian symmetric,
            # i.e. the negative frequency terms are just the complex conjugates of
            # the corresponding positive-frequency terms
            # We only need the first half, so doing np.fft.rfft is more efficient
            if timing:
                t0 = utils_lib.time_it('start FFT ', t0)

            action = "FFT"
            FFT1 = np.zeros(spec_length, dtype=np.complex)
            FFT2 = np.zeros(spec_length, dtype=np.complex)
            FFT3 = np.zeros(spec_length, dtype=np.complex)

            FFT1 = np.fft.rfft(channel_segment_1)
            FFT2 = np.fft.rfft(channel_segment_2)
            FFT3 = np.fft.rfft(channel_segment_3)

            # The matrix.
            action = "matrix"
            m11 += FFT1[0:spec_length] * np.conjugate(FFT1[0:spec_length])
            m12 += FFT2[0:spec_length] * np.conjugate(FFT1[0:spec_length])
            m13 += FFT3[0:spec_length] * np.conjugate(FFT1[0:spec_length])
            m22 += FFT2[0:spec_length] * np.conjugate(FFT2[0:spec_length])
            m23 += FFT3[0:spec_length] * np.conjugate(FFT2[0:spec_length])
            m33 += FFT3[0:spec_length] * np.conjugate(FFT3[0:spec_length])

            if timing:
                t0 = utils_lib.time_it('got POWER ', t0)

            # Shift the start index for the next segment with overlap.
            action = "shift the start index"
            start_index += n_shift

            # Plot the waveform and the selected segment.
            if utils_lib.param(param, 'plotTraces').plotTraces > 0 and do_plot > 0:
                action = "Plot"
                plt.subplot(311)
                plt.plot(trace_time, channel_tr[0].data, utils_lib.param(param, 'colorTrace').colorTrace)
                plt.plot(time_segment, channel_segment_1, utils_lib.param(param, 'colorSmooth').colorSmooth)
                plt.ylabel(f'{channel[0]} [{param.unitLabel}]', fontsize=6)
                plt.xlim(0, utils_lib.param(param, 'windowLength').windowLength)
                plt.xlabel('Time [s]')

                plt.subplot(312)
                plt.plot(trace_time, channel_tr[1].data, utils_lib.param(param, 'colorTrace').colorTrace)
                plt.plot(time_segment, channel_segment_2, utils_lib.param(param, 'colorSmooth').colorSmooth)
                plt.ylabel(f'{channel[1]} [{param.unitLabel}]', fontsize=6)
                plt.xlim(0, utils_lib.param(param, 'windowLength').windowLength)
                plt.xlabel('Time [s]')

                plt.subplot(313)
                plt.plot(trace_time, channel_tr[2].data, utils_lib.param(param, 'colorTrace').colorTrace)
                plt.plot(time_segment, channel_segment_3, utils_lib.param(param, 'colorSmooth').colorSmooth)
                plt.ylabel(f'{channel[2]} [{param.unitLabel}]', fontsize=6)
                plt.xlim(0, utils_lib.param(param, 'windowLength').windowLength)
                plt.xlabel('Time [s]')

                plt.show()

        # END LOOP SEGMENT, segments are done
        # average the spectra matrix over the sub-windows
        action = "average the spectra matrix"

        # To convert FFT to  average spectral covariance matrix
        norm = 4.0 * delta / float(num_samples)

        if verbose:
            msg_lib.info(f'{script}, DELTA: {delta}')
            msg_lib.info(f'{script}, num_samples: {num_samples}')
            msg_lib.info(f'{script}, NORM: {norm}')

        msg_lib.info(f'{script}, DELTA: {delta}')
        msg_lib.info(f'{script}, segments_count: {segments_count}')

        # The averages.
        m11 /= float(segments_count)
        m12 /= float(segments_count)
        m13 /= float(segments_count)
        m22 /= float(segments_count)
        m23 /= float(segments_count)
        m33 /= float(segments_count)

        # If power is not populated, skip LOOP WINDOW or this 1 -hour window
        if len(m11) <= 0:
            continue

        variable = dict()
        for var in param.variables:
            variable[var] = list()

        for ii in range(0, spec_length):
            #
            # form the average spectral covariance matrix, it is a complex  hermitian matrix
            #
            spectra_matrix = list()
            spectra_matrix = np.array([[m11[ii], m12[ii], m13[ii]],
                                       [m12[ii].conjugate(), m22[ii], m23[ii]],
                                       [m13[ii].conjugate(), m23[ii].conjugate(), m33[ii]]])

            action = "eigen.eigenvalues"

            """
               Return the eigenvalues and eigenvectors of a Hermitian or symmetric matrix.
    
                 This function computes the eigenvalues and eigenvectors of the complex
                 hermitian matrix A.The imaginary parts of the diagonal are assumed to be
                 zero and are not referenced. The eigenvalues are stored in the vector
                 eval and are unordered. The corresponding complex eigenvectors are
                 stored in the columns of the matrix evec. For example, the eigenvector
                 in the first column corresponds to the first eigenvalue. The
                 eigenvectors are guaranteed to be mutually orthogonal and normalised to
                 unit magnitude.
            """
            eig_values, eig_vectors = eigen.eigh(spectra_matrix)

            # using max_eig_value_index in above, we know that max_eig_value_index = 1
            max_eig_value_index = 0
            max_eig_value = float(eig_values[max_eig_value_index])
            for i in range(1, len(eig_values)):
                if float(eig_values[i]) > max_eig_value:
                    max_eig_value = float(eig_values[i])
                    max_eig_value_index = i
            """
              Eigenvectors of the maximum eigenvalue
              The corresponding complex eigenvectors are
              stored in the columns of the matrixDA. evec.
            """
            z1, z2, z3 = eig_vectors[:, max_eig_value_index]
            thetah, phihh, thetav, phivh = polar_lib.polarization_angles(z1, z2, z3)

            # Print results.
            action = "print values"
            variable["powerUD"] = np.append(variable["powerUD"], norm * abs(m11[ii]))
            variable["powerEW"] = np.append(variable["powerEW"], norm * abs(m22[ii]))
            variable["powerNS"] = np.append(variable["powerNS"], norm * abs(m33[ii]))

            """
              power spectrum of the primary eigenvalue (Lambda).
              Variation of this spectrum is very similar to that of
              the individual components
            """
            variable["powerLambda"] = np.append(variable["powerLambda"], norm * max_eig_value)
            variable["betaSquare"] = np.append(variable["betaSquare"],
                                               polar_lib.polarization_degree(m11[ii], m12[ii], m13[ii], m22[ii],
                                                                             m23[ii], m33[ii]))
            variable["thetaH"] = np.append(variable["thetaH"], thetah)
            variable["phiHH"] = np.append(variable["phiHH"], phihh)
            variable["thetaV"] = np.append(variable["thetaV"], thetav)
            variable["phiVH"] = np.append(variable["phiVH"], phivh)

        # END LOOP SEGMENT, segments are done

        smooth_x = list()
        smooth = dict()
        for var in param.variables:
            smooth[var] = list()

        # Smoothing.
        if timing:
            t0 = utils_lib.time_it('start SMOOTHING ', t0)

        if param.doSmoothing:
            msg_lib.info(f'{script}, SMOOTHING window: {octave_window_width}/{octave_window_shift} octave')
        else:
            msg_lib.info(f'{script}, SMOOTHING is off')

        if xtype == "period":
            # 10.0*maxT to avoid 1.0/0.0 at zero frequency
            period = np.append([10.0 * max_period],
                               1.0 / (np.arange(1.0, spec_length) / float(num_samples * delta)))
            if param.doSmoothing:
                # Nyquist.
                if str(utils_lib.param(param, 'xStart').xStart[plot_index]) == 'Nyquist':
                    # Regular smoothing with no angles involved.
                    smooth_x, smooth["powerUD"] = \
                        sf_lib.smooth_nyquist(xtype, period, variable["powerUD"], sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              max_period)
                    smooth_x, smooth["powerEW"] = \
                        sf_lib.smooth_nyquist(xtype, period, variable["powerEW"],
                                              sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              max_period)
                    smooth_x, smooth["powerNS"] = \
                        sf_lib.smooth_nyquist(xtype, period, variable["powerNS"],
                                              sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              max_period)
                    smooth_x, smooth["powerLambda"] = \
                        sf_lib.smooth_nyquist(xtype, period, variable["powerLambda"],
                                              sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              max_period)
                    smooth_x, smooth["betaSquare"] = \
                        sf_lib.smooth_nyquist(xtype, period, variable["betaSquare"],
                                              sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              max_period)

                    # Smoothing of angular quantities.
                    smooth_x, smooth["thetaH"] = \
                        sf_lib.smooth_nyquest_angular(xtype, period, variable["thetaH"],
                                                      sampling_frequency,
                                                      octave_window_width, octave_window_shift,
                                                      max_period, 0.0)
                    for ii in range(len(smooth["thetaH"])):
                        if smooth["thetaH"][ii] < 0.0:
                            smooth["thetaH"][ii] += 360.0

                    smooth_x, smooth["thetaV"] = \
                        sf_lib.smooth_nyquest_angular(xtype, period, variable["thetaV"],
                                                      sampling_frequency,
                                                      octave_window_width, octave_window_shift,
                                                      max_period, 90.0)

                    smooth_x, smooth["phiVH"] = \
                        sf_lib.smooth_nyquest_angular(xtype, period, variable["phiVH"],
                                                      sampling_frequency,
                                                      octave_window_width, octave_window_shift,
                                                      max_period, 90.0)
                    for ii in range(len(smooth["phiVH"])):
                        if smooth["phiVH"][ii] > 90.0:
                            smooth["phiVH"][ii] -= 180.0
                        elif smooth["phiVH"][ii] < -90.0:
                            smooth["phiVH"][ii] += 180.0

                    smooth_x, smooth["phiHH"] = \
                        sf_lib.smooth_nyquest_angular(xtype, period, variable["phiHH"],
                                                      sampling_frequency,
                                                      octave_window_width, octave_window_shift,
                                                      max_period, 90.0)
                    for ii in range(len(smooth["phiHH"])):
                        if smooth["phiHH"][ii] > 180.0:
                            smooth["phiHH"][ii] -= 360.0
                        elif smooth["phiHH"][ii] < -180.0:
                            smooth["phiHH"][ii] += 360.0
                # Not Nyquist.
                else:
                    smooth_x, smooth["powerUD"] = \
                        sf_lib.smooth_period(period, variable["powerUD"], sampling_frequency,
                                             octave_window_width, octave_window_shift,
                                             max_period,
                                             float(utils_lib.param(param, 'xStart').xStart[plot_index]))
                    smooth_x, smooth["powerEW"] = \
                        sf_lib.smooth_period(period, variable["powerEW"], sampling_frequency,
                                             octave_window_width, octave_window_shift,
                                             max_period,
                                             float(utils_lib.param(param, 'xStart').xStart[plot_index]))
                    smooth_x, smooth["powerNS"] = \
                        sf_lib.smooth_period(period, variable["powerNS"], sampling_frequency,
                                             octave_window_width, octave_window_shift,
                                             max_period,
                                             float(utils_lib.param(param, 'xStart').xStart[plot_index]))
                    smooth_x, smooth["powerLambda"] = \
                        sf_lib.smooth_period(period, variable["powerLambda"], sampling_frequency,
                                             octave_window_width, octave_window_shift,
                                             max_period,
                                             float(utils_lib.param(param, 'xStart').xStart[plot_index]))
                    smooth_x, smooth["betaSquare"] = \
                        sf_lib.smooth_period(period, variable["betaSquare"], sampling_frequency,
                                             octave_window_width, octave_window_shift,
                                             max_period,
                                             float(utils_lib.param(param, 'xStart').xStart[plot_index]))

                    # Smoothing of angular quantities.
                    smooth_x, smooth["thetaH"] = \
                        sf_lib.smooth_period_angular(period, variable["thetaH"], sampling_frequency,
                                                     octave_window_width, octave_window_shift,
                                                     max_period,
                                                     float(utils_lib.param(param, 'xStart').xStart[plot_index]), 0.0)
                    for ii in range(len(smooth["thetaH"])):
                        if smooth["thetaH"][ii] < 0.0:
                            smooth["thetaH"][ii] += 360.0

                    smooth_x, smooth["thetaV"] = \
                        sf_lib.smooth_period_angular(period, variable["thetaV"], sampling_frequency,
                                                     octave_window_width, octave_window_shift,
                                                     max_period,
                                                     float(utils_lib.param(param, 'xStart').xStart[plot_index]), 90.0)

                    smooth_x, smooth["phiVH"] = \
                        sf_lib.smooth_period_angular(period, variable["phiVH"], sampling_frequency,
                                                     octave_window_width, octave_window_shift,
                                                     max_period, 90.0)
                    for ii in range(0, len(smooth["phiVH"])):
                        if smooth["phiVH"][ii] > 90.0:
                            smooth["phiVH"][ii] -= 180.0
                        elif smooth["phiVH"][ii] < -90.0:
                            smooth["phiVH"][ii] += 180.0

                    smooth_x, smooth["phiHH"] = \
                        sf_lib.smooth_period_angular(xtype, period, variable["phiHH"],
                                                     sampling_frequency,
                                                     octave_window_width, octave_window_shift,
                                                     max_period, 90.0)
                    for ii in range(0, len(smooth["phiHH"])):
                        if smooth["phiHH"][ii] > 180.0:
                            smooth["phiHH"][ii] -= 360.0
                        elif smooth["phiHH"][ii] < -180.0:
                            smooth["phiHH"][ii] += 360.0
            else:
                smooth_x = period
                smooth["powerUD"] = variable["powerUD"]
                smooth["powerEW"] = variable["powerEW"]
                smooth["powerNS"] = variable["powerNS"]
                smooth["powerLambda"] = variable["powerLambda"]
                smooth["betaSquare"] = variable["betaSquare"]
                smooth["thetaH"] = variable["thetaH"]
                smooth["thetaV"] = variable["thetaV"]
                smooth["phiVH"] = variable["phiVH"]
                smooth["phiHH"] = variable["phiHH"]
        else:
            frequency = np.array(np.arange(0, spec_length) / float(num_samples * delta))
            # Nyquist.
            if param.doSmoothing:
                if str(utils_lib.param(param, 'xStart').xStart[plot_index]) == 'Nyquist':
                    smooth_x, smooth["powerUD"] = \
                        sf_lib.smooth_nyquist(xtype, frequency, variable["powerUD"],
                                              sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              min_frequency)
                    smooth_x, smooth["powerEW"] = \
                        sf_lib.smooth_nyquist(xtype, frequency, variable["powerEW"],
                                              sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              min_frequency)
                    smooth_x, smooth["powerNS"] = \
                        sf_lib.smooth_nyquist(xtype, frequency, variable["powerNS"],
                                              sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              min_frequency)
                    smooth_x, smooth["powerLambda"] = \
                        sf_lib.smooth_nyquist(xtype, frequency, variable["powerLambda"],
                                              sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              min_frequency)
                    smooth_x, smooth["betaSquare"] = \
                        sf_lib.smooth_nyquist(xtype, frequency, variable["betaSquare"],
                                              sampling_frequency,
                                              octave_window_width, octave_window_shift,
                                              min_frequency)
                    # Smoothing of angular quantities
                    smooth_x, smooth["thetaH"] = \
                        sf_lib.smooth_nyquest_angular(xtype, frequency, variable["thetaH"],
                                                      sampling_frequency,
                                                      octave_window_width, octave_window_shift,
                                                      min_frequency, 0.0)
                    for ii in range(0, len(smooth["thetaH"])):
                        if smooth["thetaH"][ii] < 0.0:
                            smooth["thetaH"][ii] += 360.0

                    smooth_x, smooth["thetaV"] = \
                        sf_lib.smooth_nyquest_angular(xtype, frequency, variable["thetaV"],
                                                      sampling_frequency,
                                                      octave_window_width, octave_window_shift,
                                                      min_frequency, 90.0)

                    smooth_x, smooth["phiVH"] = \
                        sf_lib.smooth_nyquest_angular(xtype, frequency, variable["phiVH"],
                                                      sampling_frequency,
                                                      octave_window_width, octave_window_shift,
                                                      min_frequency, 90.0)
                    for ii in range(0, len(smooth["phiVH"])):
                        if smooth["phiVH"][ii] > 90.0:
                            smooth["phiVH"][ii] -= 180.0
                        elif smooth["phiVH"][ii] < -90.0:
                            smooth["phiVH"][ii] += 180.0

                    smooth_x, smooth["phiHH"] = \
                        sf_lib.smooth_nyquest_angular(xtype, frequency, variable["phiHH"],
                                                      sampling_frequency,
                                                      octave_window_width, octave_window_shift,
                                                      min_frequency, 90.0)
                    for ii in range(0, len(smooth["phiHH"])):
                        if smooth["phiHH"][ii] > 180.0:
                            smooth["phiHH"][ii] -= 360.0
                        elif smooth["phiHH"][ii] < -180.0:
                            smooth["phiHH"][ii] += 360.0
                # Not Nyquist.
                else:
                    smooth_x, smooth["powerUD"] = \
                        sf_lib.smooth_frequency(frequency, variable["powerUD"], sampling_frequency,
                                                octave_window_width, octave_window_shift,
                                                min_frequency,
                                                float(utils_lib.param(param, 'xStart').xStart[plot_index]))
                    smooth_x, smooth["powerEW"] = \
                        sf_lib.smooth_frequency(frequency, variable["powerEW"], sampling_frequency,
                                                octave_window_width, octave_window_shift,
                                                min_frequency,
                                                float(utils_lib.param(param, 'xStart').xStart[plot_index]))
                    smooth_x, smooth["powerNS"] = \
                        sf_lib.smooth_frequency(frequency, variable["powerNS"], sampling_frequency,
                                                octave_window_width, octave_window_shift,
                                                min_frequency,
                                                float(utils_lib.param(param, 'xStart').xStart[plot_index]))
                    smooth_x, smooth["powerLambda"] = \
                        sf_lib.smooth_frequency(frequency, variable["powerLambda"], sampling_frequency,
                                                octave_window_width, octave_window_shift,
                                                min_frequency,
                                                float(utils_lib.param(param, 'xStart').xStart[plot_index]))
                    smooth_x, smooth["betaSquare"] = \
                        sf_lib.smooth_frequency(frequency, variable["betaSquare"], sampling_frequency,
                                                octave_window_width, octave_window_shift,
                                                min_frequency,
                                                float(utils_lib.param(param, 'xStart').xStart[plot_index]))

                    # Smoothing of angular quantities.
                    smooth_x, smooth["thetaH"] = \
                        sf_lib.smooth_frequency_angular(frequency, variable["thetaH"], sampling_frequency,
                                                        octave_window_width, octave_window_shift,
                                                        min_frequency,
                                                        float(utils_lib.param(param, 'xStart').xStart[plot_index]),
                                                        0.0)
                    for ii in range(0, len(smooth["thetaH"])):
                        if smooth["thetaH"][ii] < 0.0:
                            smooth["thetaH"][ii] += 360.0

                    smooth_x, smooth["thetaV"] = \
                        sf_lib.smooth_frequency_angular(frequency, variable["thetaV"], sampling_frequency,
                                                        octave_window_width, octave_window_shift,
                                                        min_frequency,
                                                        float(utils_lib.param(param, 'xStart').xStart[plot_index]),
                                                        90.0)

                    smooth_x, smooth["phiVH"] = \
                        sf_lib.smooth_frequency_angular(frequency, variable["phiVH"], sampling_frequency,
                                                        octave_window_width, octave_window_shift,
                                                        min_frequency,
                                                        float(utils_lib.param(param, 'xStart').xStart[plot_index]),
                                                        90.0)
                    for ii in range(0, len(smooth["phiVH"])):
                        if smooth["phiVH"][ii] > 90.0:
                            smooth["phiVH"][ii] -= 180.0
                        elif smooth["phiVH"][ii] < -90.0:
                            smooth["phiVH"][ii] += 180.0

                    smooth_x, smooth["phiHH"] = \
                        sf_lib.smooth_frequency_angular(frequency, variable["phiHH"], sampling_frequency,
                                                        octave_window_width, octave_window_shift,
                                                        min_frequency,
                                                        float(utils_lib.param(param, 'xStart').xStart[plot_index]),
                                                        90.0)
                    for ii in range(0, len(smooth["phiHH"])):
                        if smooth["phiHH"][ii] > 180.0:
                            smooth["phiHH"][ii] -= 360.0
                        elif smooth["phiHH"][ii] < -180.0:
                            smooth["phiHH"][ii] += 360.0
            else:
                smooth_x = frequency
                smooth["powerUD"] = variable["powerUD"]
                smooth["powerEW"] = variable["powerEW"]
                smooth["powerNS"] = variable["powerNS"]
                smooth["powerLambda"] = variable["powerLambda"]
                smooth["betaSquare"] = variable["betaSquare"]
                smooth["thetaH"] = variable["thetaH"]
                smooth["thetaV"] = variable["thetaV"]
                smooth["phiVH"] = variable["phiVH"]
                smooth["phiHH"] = variable["phiHH"]
        if timing:
            t0 = utils_lib.time_it(f'SMOOTHING window {octave_window_width}, {octave_window_shift,} DONE', t0)

        # Convert to dB.
        variable["powerUD"] = 10.0 * np.log10(variable["powerUD"][0:spec_length])
        variable["powerEW"] = 10.0 * np.log10(variable["powerEW"][0:spec_length])
        variable["powerNS"] = 10.0 * np.log10(variable["powerNS"][0:spec_length])
        variable["powerLambda"] = 10.0 * np.log10(variable["powerLambda"][0:spec_length])

        smooth["powerUD"] = 10.0 * np.log10(smooth["powerUD"][0:spec_length])
        smooth["powerEW"] = 10.0 * np.log10(smooth["powerEW"][0:spec_length])
        smooth["powerNS"] = 10.0 * np.log10(smooth["powerNS"][0:spec_length])
        smooth["powerLambda"] = 10.0 * np.log10(smooth["powerLambda"][0:spec_length])

        # Create output paths if they do not exist.
        if utils_lib.param(param, 'outputValues').outputValues > 0:
            file_path, psd_file_tag = file_lib.get_dir(utils_lib.param(param, 'dataDirectory').dataDirectory,
                                                       utils_lib.param(param, 'polarDbDirectory').polarDbDirectory,
                                                       network, station, location, channelTag)
            file_path = os.path.join(file_path, segment_start_year, segment_start_doy)
            utils_lib.mkdir(file_path)

            # Output is based on the xtype.
            if verbose:
                msg_lib.info(f'tr_channel_.stats: {channel_tr[0].stats} '
                             f'REQUEST: {segment_start} '
                             f'TRACE: {channel_tr[0].stats.starttime} '
                             f'DELTA: {channel_tr[0].stats.delta}')
                samples = int(utils_lib.param(param, "windowLength").windowLength /
                              float(channel_tr[0].stats.delta) + 1)
                msg_lib.info(f'SAMPLES: '
                             f'{samples}')
            channel_time = channel_tr[0].stats.starttime
            # Avoid file names with 59.59.
            channel_time += datetime.timedelta(microseconds=10)
            tag_list = [psd_file_tag, channel_time.strftime("%Y-%m-%dT%H:%M:%S"),
                        f'{param.windowLength}', xtype]
            file_name = file_lib.get_file_name(utils_lib.param(param, 'namingConvention').namingConvention, file_path,
                                               tag_list)
            msg_lib.message(f'OUTPUT: {file_name}')
            try:
                with open(file_name, "w") as file:

                    # Header.
                    file.write(f'{x_units} {power_units}\n')
                    file.write(f'{header}\n')

                    # Data.
                    for i in range(0, len(smooth_x)):
                        file.write("%11.6f %11.4f %11.4f %11.4f %11.4f %11.4f %11.4f %11.4f %11.4f %11.4f\n" % (
                            float(smooth_x[i]), float(smooth["powerUD"][i]), float(smooth["powerEW"][i]),
                            float(smooth["powerNS"][i]), float(smooth["powerLambda"][i]),
                            float(smooth["betaSquare"][i]), float(smooth["thetaH"][i]), float(smooth["thetaV"][i]),
                            float(smooth["phiVH"][i]), float(smooth["phiHH"][i])))

            except Exception as ex:
                code = msg_lib.error(
                    f'failed to open {file_name}. Is the "namingConvention" parameter  of '
                    f'"{utils_lib.param(param, "namingConvention").namingConvention}" set correctly?', 4)
                sys.exit(code)

        # Plot
        if (utils_lib.param(param, 'plotSpectra').plotSpectra > 0 or \
            utils_lib.param(param, 'plotSmooth').plotSmooth > 0) and \
                do_plot > 0:
            action = "Plot 2"

            if timing:
                t0 = utils_lib.time_it('start PLOT ', t0)

            fig = plt.figure(figsize=param.figureSize)
            fig.subplots_adjust(hspace=.2)
            fig.subplots_adjust(wspace=.2)
            fig.set_facecolor('w')
            x, y = shared.production_label_position

            ax = dict()
            plot_count = 0
            for var_index, var in enumerate(param.variables):
                plot_count += 1
                ax[var] = plt.subplot(param.subplot[var])
                ax[var].set_xscale('log')

                # Period for the x-axis.
                if xtype == "period":
                    if utils_lib.param(param, 'plotSpectra').plotSpectra:
                        plt.plot(period, variable[var], utils_lib.param(param, 'colorSpectra').colorSpectra,
                                 lw=0.6, label=var)
                    if utils_lib.param(param, 'plotSmooth').plotSmooth:
                        plt.plot(smooth_x, smooth[var], color=utils_lib.param(param, 'colorSmooth').colorSmooth,
                                 lw=0.6, label=f'smoothed {var}')

                # Frequency for the x-axis.
                else:
                    if utils_lib.param(param, 'plotSpectra').plotSpectra:
                        plt.plot(frequency, variable[var], utils_lib.param(param, 'colorSpectra').colorSpectra,
                                 lw=0.6, label=var)
                    if utils_lib.param(param, 'plotSmooth').plotSmooth:
                        plt.plot(smooth_x, smooth[var], color=utils_lib.param(param, 'colorSmooth').colorSmooth,
                                 lw=0.6, label=f'smoothed {var}')

                plt.xlabel(x_units)
                plt.xticks(fontsize=6)
                plt.xlim(utils_lib.param(param, 'xlimMin').xlimMin[var][xtype],
                         utils_lib.param(param, 'xlimMax').xlimMax[var][xtype])
                plt.ylabel(utils_lib.param(param, 'yLabel').yLabel[var], fontsize=8)
                plt.yticks(fontsize=6)
                plt.ylim([utils_lib.param(param, 'ylimLow').ylimLow[var],
                          utils_lib.param(param, 'ylimHigh').ylimHigh[var]])

                if plot_count == 0:
                    plt.title(f'{station} from {segment_start} to {segment_end}')

                if var_index == 2:
                    ax[var].text(x, 3.0 * y, production_label, horizontalalignment='left', fontsize=5,
                                 verticalalignment='top',
                                 transform=ax[var].transAxes)

                if do_plot_nnm and 0 <= var_index < 4:
                    nlnm_x, nlnm_y = get_nlnm()
                    nhnm_x, nhnm_y = get_nhnm()
                    if xtype != 'period':
                        nlnm_x = 1.0 / nlnm_x
                        nhnm_x = 1.0 / nhnm_x
                    plt.plot(nlnm_x, nlnm_y, lw=1, ls=':', c='k', label='NLNM, NHNM')
                    plt.plot(nhnm_x, nhnm_y, lw=1, ls=':', c='k')
                ax[var].legend(frameon=False, prop={'size': 6})
            if timing:
                t0 = utils_lib.time_it('show PLOT ', t0)

            plt.suptitle(title, y=0.95)
            plt.show()
t0 = t1
t0 = utils_lib.time_it('END', t0)
msg_lib.info('Done!!')
