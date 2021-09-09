from os import listdir
from os.path import isfile, join
import os
import sys

import collections
import numpy as np
import math

from obspy.core import UTCDateTime, read, Stream
from obspy import read_inventory
from obspy.io.stationxml.core import validate_stationxml as validate_StationXML
from time import time

import msgLib as msg_lib
import utilsLib as utils_lib
import staLib as sta_lib


def get_response_inventory(resp_dir, debug=False):
    """"
    get_response_inventory
        build a list of response inventories under a given met directory

        2016-10-27 Manoch: craeted
    """

    t0 = time()
    accept_count = 0
    reject_count = 0

    msg_lib.info('reading response files')
    file_list = [f for f in listdir(resp_dir) if isfile(join(resp_dir, f))]
    inventory = list()
    for resp_file in file_list:
        try:
            validation = validate_StationXML(os.path.join(resp_dir, resp_file))
            if not validation[0]:
                msg_lib.error(f'Skipped invalid response file {os.path.join(resp_dir, resp_file)}  {validation[1]}', 4)
            inv = read_inventory(os.path.join(resp_dir, resp_file))
            accept_count += 1
            inventory.append(inv)
        except TypeError as e:
            if debug:
                msg_lib.error(f'Skipped invalid response file {os.path.join(resp_dir, resp_file)} {e.message}', 4)
            reject_count += 1
        except Exception as ex:
            if debug:
                msg_lib.error(f'Skipped, could not read {os.path.join(resp_dir, resp_file)} {ex}', 4)
            reject_count += 1
    t1 = utils_lib.time_it("Response Inventory", t0)
    msg_lib.info(f'response inventory:{accept_count} valid and {reject_count} rejected')
    return inventory


def get_response_from_file(inventory, resp_dir, network, station, location, channel, start_time, debug):
    """"
    get_response_from_file
    find response for a given Network, Station, Location cannel

        2016-10-27 Manoch: craeted
    """

    # If inventory list is not populated, populate it first.
    if inventory is None:
        inventory = get_response_inventory(resp_dir, False)

    this_start_time = UTCDateTime(start_time)
    seed_id = ".".join([network, station, location, channel])
    msg_lib.info(f'Looking for seed ID: {seed_id}')
    this_inventory = None
    for inv in inventory:
        try:
            response = inv.get_response(seed_id, this_start_time)
            if debug:
                msg_lib.info(f'Response: {response}')
            this_inventory = inv
            break
        except Exception as ex:
            response = None
    return inventory, this_inventory


def get_channel_waveform_files(network, station, location, channel, start_time, end_time,
                               client, file_tag, resp_dir=None, inventory=None):
    """
    get_channel_waveform_files gets data from files and
    the response form the FDSN client. for the requested
    network/station/location/channel and time

    the output is the corresponding data stream
    file_tag should be in such a way to guide the function in
    selecting waveform files like

    {this Path}/*.SAC

    channel may have the last one or two letters wildcarded (e.g. channel="EH*")
    to select all components with a common band/instrument code.

    All other selection criteria that accept strings (network, station, location)
    may also contain Unix style wildcards (*, ?, ...).

    HISTORY:
       2015-03-17 Manoch: added the "waterLevel" parameter to provide user with more control on how the ObsPy module
       shrinks values under water-level of max spec amplitude
                          when removing the instrument response.
       2015-02-24 Manoch: introduced two new parameters (performInstrumentCorrection, applyScale) to allow user avoid
       instrument correction also now user can turn od decon. filter

       2014-03-15 Manoch: created
   """
    debug = True
    sender = 'get_channel_waveform_files'

    # Stream holds the final stream
    this_start_time = UTCDateTime(start_time)
    this_end_time = UTCDateTime(end_time)
    stream = Stream()
    try:
        # Read in the files to a stream.
        msg_lib.info(f'checking: {file_tag}')
        msg_lib.info('Apply scaling')
        stream_in = read(file_tag, start_time=this_start_time, end_time=this_end_time, nearest_sample=True)
    except Exception as ex:
        msg_lib.error(f'{network}, {station}, {location}, {channel}, {start_time}, {end_time} {ex}', 2)
        return None

    try:

        # Select the desire streams only.
        if location == "--":
            stream_out = stream_in.select(network=network, station=station, location="", channel=channel)
        else:
            stream_out = stream_in.select(network=network, station=station, location=location, channel=channel)

        for i in range(len(stream_out)):

            # Get the network, station, location and channel information.
            this_nslc, this_time, junk = str(stream_out[i]).split('|')
            net, sta, loc, chan = this_nslc.strip().split('.')
            if len(loc) == 0:
                loc = "--"

            # If resp_dir is defined, first look into user's resp_dir for stationXML files,
            # if not found get it from FDSN
            start, end = this_time.split(' - ')
            inv = None
            if resp_dir is not None:
                msg_lib.info(f'Getting response from {resp_dir}')
                this_loc = loc
                if loc == '--':
                    this_loc = ''

                inventory, inv = get_response_from_file(inventory, resp_dir, net, sta, this_loc, chan,
                                                        start_time, debug)
                if inv is not None:
                    if debug:
                        msg_lib.info(f'Attaching {inv}')
                    stream_out[i].attach_response(inv)
                    stream += stream_out[i]
                else:
                    this_start_time = UTCDateTime(start.strip())
                    msg_lib.warning(sender, f'NO RESPONSE FILE: {net}, {sta}, {loc}, {chan}, {this_start_time}')
            if inv is None and client is not None:
                # The FDSN webservices return StationXML metadata.
                msg_lib.info('Getting response from IRIS')
                try:
                    this_start_time = UTCDateTime(start.strip())
                    this_end_time = UTCDateTime(end.strip())
                    inv = client.get_stations(network=net, station=sta, location=loc, channel=chan,
                                              starttime=this_start_time,
                                              endtime=this_end_time, level="response")
                    stream_out[i].attach_response(inv)
                    stream += stream_out[i]
                    if debug:
                        msg_lib.info(f'Response attached: {inv}')
                except Exception as ex:
                    this_start_time = UTCDateTime(start.strip())
                    msg_lib.warning(sender, f'NO RESPONSE: {net}, {sta}, {loc}, {chan}, '
                                    f'{this_start_time}, {this_end_time} {ex}')
                    continue

    except Exception as ex:
        msg_lib.error(f'get_channel_waveform_files {network}, {station}, {location}, {channel}, {start_time}, '
                      f'{end_time}, {ex}',
                      2)
        return None, None

    return inventory, stream


def divide_to_chunks(long_list, chunks):
    """Yield successive chunk_count-sized chunks from long_list."""
    # For item i in a range that is a length of l,
    for i in range(0, len(long_list), chunks):
        # Create an index range for l of n items:
        yield long_list[i:i + chunks]


def get_request_items(req_line):
    """Split a request line to its components."""
    (req_net, req_sta, req_loc, req_chan, req_start, req_end) = req_line.strip().split()
    return req_net, req_sta, req_loc, req_chan, req_start, req_end


def get_service_url(ws_catalog, ws_dc):
    """Extract the service URL from dataselect service URL."""
    ws_service_url = ws_catalog[ws_dc]['dataselect_service'].split('/fdsn')[0]
    return ws_service_url


def get_fedcatalog_station(req_url, request_start, request_end, chunk_length, chunk_count=1):
    """Get station list from fedcatalog service."""

    # This dictionary stores all the fedcatalog information.
    fedcatalog_info = dict()

    # This dictionary provides a template for fetdatalog creation.
    catalog_info = dict()

    bulk_list = collections.OrderedDict()
    dc_chunk_list = dict()

    msg_lib.info(f'sending request to fedcatalog: {req_url}')

    try:
        content = utils_lib.read_url(req_url)
    except Exception as _er:
        code = msg_lib.error(f'Request  {req_url}: {_er}', 4)
        sys.exit(code)

    # Go through the station list and see if they qualify.
    _lines = content.split('\n')

    _line_index = -1
    previous_dc = None
    dc_name = None
    for _line in _lines:
        _line_index += 1

        # Skip the blank and the comment lines.
        if not _line.strip() or _line.startswith('#'):
            continue

        # From the parameter=value lines, we are interested in the DATACENTER and DATASELECTSERVICE lines.
        elif '=' in _line:
            _par, _value = _line.split('=')

            # Found the data center name.
            if _par == 'DATACENTER':
                if dc_name is not None:
                    previous_dc = dc_name
                msg_lib.info(f'from the {_value} data center')
                dc_name, dc_url = _value.strip().split(',')

                # Initialize the data center information, create chunk_count containers for chunked requests.
                if dc_name not in catalog_info.keys():
                    msg_lib.info(f'Initiating fedcatalog request for {dc_name}')
                    catalog_info[dc_name] = utils_lib.ObjDict(
                        {'url': dc_url, 'dataselect_service': '', 'bulk': list()})

                # if this is not the first data center, save the previous data center's bulk list
                if bulk_list:
                    this_dc_list = list()
                    for _key in bulk_list:
                        this_dc_list.append(bulk_list[_key][0])

                    # Break the  list into chunks and add it to fedcatalog_info. We incorporate band_index,
                    # in case multiple bands are requested. Otherwise, chunk_index of the next band will overwrite
                    # chunk_index of this band.
                    for chunk_index, chunk in enumerate(divide_to_chunks(this_dc_list, chunk_count)):
                        chunk_dc = f'{previous_dc}_{chunk_index}'

                        # Keep track of chunks for each DC for later use.
                        if previous_dc not in dc_chunk_list.keys():
                            dc_chunk_list[previous_dc] = list()
                        dc_chunk_list[previous_dc].append(chunk_dc)

                        fedcatalog_info[chunk_dc] = catalog_info[previous_dc].copy()
                        fedcatalog_info[chunk_dc]['bulk'] = chunk

                    # The list is saved. Now, reset the bulk_list.
                    bulk_list = collections.OrderedDict()

                continue
            # Found the dataselect service address.
            elif _par == 'DATASELECTSERVICE':
                # Save the dataselect service address for all chunks.
                if dc_name in dc_chunk_list.keys():
                    for chunk_dc in dc_chunk_list[dc_name]:
                        fedcatalog_info[chunk_dc]['dataselect_service'] = _value.strip()

                # Save the dataselect service address in the catalog for this DC,
                catalog_info[dc_name]['dataselect_service'] = _value.strip()
                msg_lib.info(f'dataselect service is {_value.strip()}')
                continue
            else:
                # Ignore the other definitions.
                continue

        # The rest are the station lines.
        # Skip the blank lines.
        if not (_line.strip()):
            continue

        # Get the station information.
        net, sta, loc, chan, sta_start, sta_end = get_request_items(_line)

        start = UTCDateTime(request_start)
        end = UTCDateTime(request_end)
        segment = -1

        while start < end:
            segment += 1
            req_start = start.strftime('%Y-%m-%dT%H:%M:%S')
            if start + chunk_length <= end:
                req_end = (start + chunk_length).strftime('%Y-%m-%dT%H:%M:%S')
            else:
                req_end = end.strftime('%Y-%m-%dT%H:%M:%S')
            _net_sta_key = f'{net}_{sta}_{chan}_{segment}'
            bulk_list[_net_sta_key] = (net, sta, loc, chan, req_start, req_end)
            start += chunk_length + 0.0001

    # Save the last data center's bulk list.
    if bulk_list:
        this_dc_list = list()
        for _key in bulk_list.keys():
            this_dc_list.append(bulk_list[_key])

        # Break the  list into chunks and add it to fedcatalog_info.
        for chunk_index, chunk in enumerate(divide_to_chunks(this_dc_list, chunk_count)):
            chunk_dc = f'{dc_name}_{chunk_index}'
            # Keep track of chunks for each DC for later use.
            if dc_name not in dc_chunk_list.keys():
                dc_chunk_list[dc_name] = list()
            dc_chunk_list[dc_name].append(chunk_dc)

            fedcatalog_info[chunk_dc] = catalog_info[dc_name].copy()
            fedcatalog_info[chunk_dc]['bulk'] = chunk

        # Reset the bulk_list.

        bulk_list = collections.OrderedDict()
    return utils_lib.ObjDict(fedcatalog_info)


def qc_3c_stream(stream, segment_length, window, sorted_channel_list, channel_groups, verbose):
    """
      qc_3c_stream performs a QC on a 3-C stream by making sure all channels are present,
      traces are the same length and have same start and end times  mostly needed for
      polarization analysis

      the output is an array of trace record numbers in the stream that passed
      the QC

      HISTORY:
        2021-09-07 Manoch: qc_3c_stream  now uses trace stats information directly. Still follows the
                           old code's QC logic but now records are created based on the
                           trace stats.
        2014-04-21 Manoch: created
    """
    sender = 'qc_3c_stream'

    if verbose:
        msg_lib.info(f'{sender}, there are total of {len(stream)} traces.')
    # Sort to make sure related records are one after another. Defaults to
    # [‘network’, ‘station’, ‘location’, ‘channel’, ‘starttime’, ‘endtime’].
    stream.sort()

    # extract the list, one record (line) at a time and group them
    qc_record_list = list()
    previous_group_name = ""
    group_count = -1
    group_channels = list()
    group_records = list()
    group_names = list()
    station_info_list = list()
    time_info_list = list()
    channel_info_list = list()

    for line_index, trace in enumerate(stream):
        # Reset the list for each record (line).
        this_station_info_list = list()
        this_time_info_list = list()
        this_channel_info_list = list()

        # sta_info: [NET,STA,LOC,CHAN].
        this_station_info_list = [trace.stats.network, trace.stats.station,
                                  trace.stats.location, trace.stats.channel]

        # Replace blank locations with "--".
        this_station_info_list[2] = sta_lib.get_location(this_station_info_list[2])

        # time_info = [ STart, End].
        this_time_info_list.append([trace.stats.starttime, trace.stats.endtime])

        # Channel_info [SAMPLING,UNIT,SAMPLES,TEXT].
        this_channel_info_list.append([trace.stats.sampling_rate, 'Hz', trace.stats.npts, 'samples'])

        # Name each record as a channel group (do not include channel).
        this_group_name = ".".join(this_station_info_list[0:2])

        # Starting the first group, start saving info.
        if this_group_name != previous_group_name:
            group_count += 1
            if verbose:
                msg_lib.info(f'{sender}, started group {group_count}: {this_group_name}')
            group_names.append(this_group_name)

            group_channels.append(list())
            group_records.append(list())

            previous_group_name = this_group_name

        # Save the channel names.
        group_channels[group_count].append(this_station_info_list[-1])
        group_records[group_count].append(line_index)

        # Note: the following arrays are not grouped, hence extend and not append
        time_info_list.extend(this_time_info_list)
        channel_info_list.extend(this_channel_info_list)
        station_info_list.extend([this_station_info_list])

    if verbose:
        msg_lib.info(f'{sender}, found {len(group_records)} record groups.')

    # QC each group
    for rec_index, rec in enumerate(group_records):
        # All group elements are in, start the QC.
        qc_passed = True

        if verbose:
            msg_lib.info(f'{sender}, QC for record group {group_names[rec_index]}')

        # Create a sorted list of unique channels.
        channel_list = sorted(set(group_channels[rec_index]))
        if verbose:
            msg_lib.info(f'{sender}, channel list: {channel_list}')

        # Missing Channels?
        # - based on missing records.
        if len(group_records[rec_index]) < 3:
            msg_lib.info(f'{sender}, missing channels records, received {len(group_records[rec_index])}')
            qc_passed = False
        else:
            # - based on channels missing from channel list.
            if channel_list not in sorted_channel_list:
                msg_lib.info(f'{sender}, missing channels records from {group_names[rec_index]} got '
                             f'{channel_list} while expecting {sorted_channel_list}')
                qc_passed = False
            # - channel list is valid
            else:
                msg_lib.info(f'{sender}, channel list complete {channel_list}')

                """
                  Gaps?
                  This is a simple rejection based on gaps. A better choice will be to take segments and process 
                  those with sufficient length but with 3 channels involved, this will be too complicated 
                  -- manoch 2014-04-18
                """
                if len(group_records[rec_index]) > 3:
                    msg_lib.info(f'{sender}, gaps in {group_names[rec_index]}')
                    qc_passed = False
                else:
                    msg_lib.info(f'{sender}, no gaps in {group_names[rec_index]}')

                    # Check for sampling rates.
                    rec1, rec2, rec3 = map(int, group_records[rec_index])
                    sampling_frequency_01 = float(channel_info_list[rec1][0])
                    sampling_frequency_02 = float(channel_info_list[rec2][0])
                    sampling_frequency_03 = float(channel_info_list[rec3][0])
                    if sampling_frequency_01 != sampling_frequency_02 or sampling_frequency_01 != sampling_frequency_03:
                        msg_lib.info(f'{sender}, sampling frequencies do not match! ({sampling_frequency_01}, '
                                     f'{sampling_frequency_02}, {sampling_frequency_03}')
                        qc_passed = False
                    else:
                        msg_lib.info(f'{sender}, sampling frequencies: [{sampling_frequency_01}, '
                                     f'{sampling_frequency_02},'
                                     f'{sampling_frequency_03}]')

                        # Check for mismatched start time - Note: there are exactly 3 records.
                        delay01 = np.abs(UTCDateTime(time_info_list[rec1][0]) - UTCDateTime(
                            time_info_list[rec2][0]))
                        delay02 = np.abs(UTCDateTime(time_info_list[rec1][0]) - UTCDateTime(
                            time_info_list[rec3][0]))
                        samplerate = 1.0 / float(channel_info_list[rec1][0])

                        # Calculate number of points needed for FFT (as a power of 2) based on the run parameters.
                        num_samp_needed_03 = 2 ** int(math.log(int((float(segment_length) / samplerate + 1) / window),
                                                               2))  # make sure it is power of 2
                        if delay01 == 0.0 and delay02 == 0.0:
                            msg_lib.info(f'{sender}, start times OK')
                        else:
                            if 0.0 < delay01 < samplerate:
                                msg_lib.info(f'{sender}, start time difference between '
                                             f'{".".join(station_info_list[rec1])} '
                                             f'and {".".join(station_info_list[rec2])} is {delay01}s and is less '
                                             f'than 1 sample')
                            elif delay01 > 0.0 and delay01 >= samplerate:
                                msg_lib.info(f'{sender}, start time difference between '
                                             f'{".".join(station_info_list[rec1])} '
                                             f'and {".".join(station_info_list[rec2])} is {delay01}s and is  '
                                             f'one sample or more')
                                qc_passed = False
                            if 0.0 < delay02 < samplerate:
                                msg_lib.info(f'{sender}, start time difference between '
                                             f'{".".join(station_info_list[rec1])} '
                                             f'and {".".join(station_info_list[rec3])} is {delay02}s and is less '
                                             f'than 1 sample')
                            elif delay02 > 0.0 and delay02 >= samplerate:
                                msg_lib.info(f'{sender}, start time difference between '
                                             f'{".".join(station_info_list[rec1])} '
                                             f'and {".".join(station_info_list[rec3])} is {delay02}s and is  '
                                             f'one sample or more')

                        # Check for insufficient number of samples.
                        if qc_passed:
                            samples_list = list()
                            for _rec in (rec1, rec2, rec3):
                                samples_list.append(float(channel_info_list[_rec][2]))

                            if verbose:
                                msg_lib.info(f'{sender}, samples: {samples_list}')
                            minimum_samples = np.min(samples_list)
                            if minimum_samples < num_samp_needed_03:
                                msg_lib.info(f'{sender}, wanted minimum of {num_samp_needed_03} '
                                             f'but got only {minimum_samples}')
                                qc_passed = False
                            else:
                                msg_lib.info(f'{sender}, wanted minimum of '
                                             f'{num_samp_needed_03} got {minimum_samples}, OK')

                                # mismatched end time.
                                delay01 = np.abs(
                                    UTCDateTime(time_info_list[rec1][1]) - UTCDateTime(
                                        time_info_list[rec2][1]))
                                delay02 = np.abs(
                                    UTCDateTime(time_info_list[rec1][1]) - UTCDateTime(
                                        time_info_list[rec3][1]))
                                samplerate = 1.0 / float(channel_info_list[rec1][0])
                                qc_passed = True
                                if delay01 == 0.0 and delay02 == 0.0:
                                    msg_lib.info(f'{sender}, end times OK')

                                # For information only, we know we have enough samples!
                                else:
                                    if 0.0 < delay01 < samplerate:
                                        msg_lib.info(f'{sender}, end time difference between '
                                                     f'{".".join(station_info_list[rec1])}'
                                                     f' and {".".join(station_info_list[rec2])} is {delay01}s less '
                                                     f'than 1 sample')
                                    elif 0.0 < delay01 >= samplerate:
                                        msg_lib.info(f'{sender}, end time difference between '
                                                     f'{".".join(station_info_list[rec1])}'
                                                     f' and {".".join(station_info_list[rec2])} '
                                                     f'is {delay01}s is 1 sample or more')
                                    if 0.0 < delay02 < samplerate:
                                        msg_lib.info(f'{sender}, end time difference between '
                                                     f'{".".join(station_info_list[rec1])}'
                                                     f' and {".".join(station_info_list[rec3])} is {delay02}s and is '
                                                     f'less than 1 sample')
                                    elif delay02 > 0.0 and delay02 >= samplerate:
                                        msg_lib.info(f'{sender}, end time difference between '
                                                     f'{".".join(station_info_list[rec1])}'
                                                     f' and {".".join(station_info_list[rec3])}'
                                                     f' is {delay02}s and is 1 sample or more')

                # End of the QC save qc_passed flag.
                if qc_passed:
                    chan_group_found = False
                    # qc_record_list provides index of the record for each channel_groups element.
                    for chans in channel_groups:
                        # found the matching channel group?
                        if group_channels[rec_index][0] in chans and group_channels[rec_index][1] in \
                                chans and group_channels[rec_index][2] in chans:
                            msg_lib.info(f'{sender}, output channel order should be {chans}')
                            ordered_group_records = list()
                            group_channels_list = group_channels[rec_index]
                            chan_group_found = True
                            for chan in chans:
                                qc_record_list.append(group_channels_list.index(chan))
                            break
                    if not chan_group_found:
                        code = msg_lib.error(f'{sender}, channel_groups parameter matching the '
                                             f'output channel order [{group_channels[rec_index][0]}, '
                                             f'{group_channels[rec_index][1]}, {group_channels[rec_index][2]}] '
                                             f'not found', 4)
                        sys.exit(code)

    if verbose:
        msg_lib.info(f'{sender}, passed records: {qc_record_list}')
    return qc_record_list