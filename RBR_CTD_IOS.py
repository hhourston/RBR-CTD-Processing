# to write files similar to IOS output files:

"""
author: Lu Guan
date: Oct. 06, 2020
about: This script is for processing RBR CTD data and producing .ctd files in IOS Header format.

Modified July 2021 - September 2021 by Samantha Huntington

Modified Mar. 2023 - ___ by Hana Hourston @hhourston
"""
# globals().clear()
import cartopy.crs as ccrs
from cartopy.mpl.ticker import (LongitudeFormatter, LatitudeFormatter, LatitudeLocator)
import sys
import os
import warnings
import pyrsktools
# import itertools
# from datetime import datetime, timezone
import numpy as np
import pandas as pd
# import pyproj
from mpl_toolkits.basemap import Basemap
from copy import deepcopy  # copy,
from scipy import signal
import gsw
# import xarray as xr
from matplotlib import pyplot as plt
# import glob
from datetime import datetime
# from datetime import timedelta
# from decimal import Decimal
import random
from ocean_data_parser.convert.oxygen import O2stoO2c
from seawater import eos80

# import openpyxl
# from openpyxl import load_workbook


# Global variables
VARIABLES_POSSIBLE = ['Salinity', 'Temperature', 'Conductivity', 'Oxygen', 'Fluorescence']
VARIABLE_UNITS = ['PSS-78', 'C', 'mS/cm', '%', 'ug/L']
VARIABLE_COLOURS = ['b', 'r', 'goldenrod', 'k', 'g']


# ------- step 1: .rsk file in EPdesktop structure - Export profile data to .csv files from .rsk files-------

# run function to export files
# sh - call function at bottom of function


# def EXPORT_FILES(dest_dir, file, year, cruise_number, event_start):
#     """
#     Read in a rsk file and output in csv format
#     Inputs:
#         - folder, file, year, cruise_number: rsk-format file containing raw RBR data
#         - event_start: taken from ctd log or cruise log
#     Outputs:
#         - csv file: csv files containing the profile data
#     """
#
#     # function to export .csv files from .rsk file.
#     filename = str(dest_dir) + str(file)  # full path and name of .rsk file
#     path_slash_type = '/' if '/' in filename else '\\'
#     rsk = pyrsktools.open(filename)  # load up an RSK
#
#     # check the number of profiles
#     n_profiles = len(list(rsk.profiles()))  # get the number of profiles recorded
#
#     ctd_data = pd.DataFrame()  # set an empty pandas dataframe to store data
#
#     # print(list(rsk.channels.items()))
#     # export .csv file for each profile
#     for i in range(0, n_profiles, 1):
#
#         downcast = list(itertools.islice(rsk.casts(pyrsktools.Region.CAST_DOWN), i, i + 1))[
#             0].npsamples()  # separate samples for each downcast file
#         downcast_dataframe = pd.DataFrame(data=downcast,
#                                           columns=downcast.dtype.names)  # convert data into pandas data frame
#
#         upcast = list(itertools.islice(rsk.casts(pyrsktools.Region.CAST_UP), i, i + 1))[0].npsamples()
#         upcast_dataframe = pd.DataFrame(data=upcast, columns=upcast.dtype.names)
#         # print(downcast[0])
#
#         column_names = list(downcast.dtype.names)  # read the column names
#         # print(list(rsk.channels))
#         # print(column_names)
#         # print(len(column_names))
#         col_range = len(column_names)  # added this to get them all
#         column_names[0] = 'Time(yyyy-mm-dd HH:MM:ss.FFF)'  # update time
#         for j in range(1, col_range, 1):  # update the column names
#             column_names[j] = column_names[j][0: -3] + "(" + list(rsk.channels.items())[j - 1][1][4] + ")"
#
#         downcast_dataframe.columns = column_names  # update column names in downcast data frame
#         downcast_dataframe["Cast_direction"] = "d"  # add a column for cast direction
#         downcast_dataframe["Event"] = i + event_start  # add a column for event number - get event_start from Logs
#         upcast_dataframe.columns = column_names
#         upcast_dataframe["Cast_direction"] = "u"
#         upcast_dataframe["Event"] = i + event_start
#         # downcast_name = filename.split("/")[-1][0:-4].upper() + "_profile" + str(i + event_start).zfill(
#         #     4) + "_DOWNCAST.csv"  # downcast file name
#         # upcast_name = filename.split("/")[-1][0:-4].upper() + "_profile" + str(i + event_start).zfill(
#         #     4) + "_UPCAST.csv"  # upcast file name
#         profile_name = filename.split(path_slash_type)[-1][0:-4].upper() + "_profile" + str(i + event_start).zfill(
#             4) + ".csv"  # profile name
#         # combine downcast and upcast into one profile
#         profile_data = pd.concat([downcast_dataframe, upcast_dataframe])
#         ctd_data = ctd_data.append(profile_data, ignore_index=True)  # combine profiles into one file
#
#         # downcast_dataframe.to_csv(folder + downcast_name)
#         # upcast_dataframe.to_csv(folder + upcast_name)
#         profile_data.to_csv(dest_dir + profile_name)  # export each profile
#
#     output_filename = year + "-" + cruise_number + "_CTD_DATA.csv"  # all data file name
#     ctd_data.to_csv(dest_dir + output_filename)  # export all data in one .csv file
#
#     return


# -------------------  Exploring if we can input mulitple .rsk files----------------------


def EXPORT_MULTIFILES(dest_dir, num_profiles: int,  # year, cruise_number,
                      event_start=1, all_last: str = 'ALL', rsk_time1=None, rsk_time2=None):
    """
    Read in a directory of rsk files and output in csv format
    Inputs:
        - folder, file, year, cruise_number: rsk-format file containing raw RBR data
        - all_last: "all" or "last"; define which profiles to extract from the rsk file
    Outputs:
        - csv file: csv files containing the profile data
    """
    files = os.listdir(dest_dir)  # list all the files in dest_dir
    files = list(filter(lambda f: f.endswith('.rsk'), files))  # keep the rsk files only
    n_files = len(files)  # get the number of files

    current_profile = event_start

    # function to export .csv files from .rsk files .
    for k in range(n_files):
        # Open the rsk file and read the data within it
        filename = str(dest_dir) + str(files[k])  # full path and name of .rsk file
        # readHiddenChannels=True does not reveal the derived variables
        rsk = pyrsktools.RSK(filename, readHiddenChannels=False)  # load up an RSK
        rsk.open()
        rsk.readdata(t1=rsk_time1, t2=rsk_time2)
        # rsk.data now returns data in a structured array format

        # Compute the derived channels
        rsk.derivesalinity()
        rsk.deriveseapressure()
        rsk.derivedepth()
        # rsk.deriveO2()  # Derive later

        # Add a check on the number of profiles in the rsk file
        rsk_num_profiles = len(rsk.getprofilesindices(direction="down"))
        if rsk_num_profiles != num_profiles:
            warnings.warn(f'Number of rsk profiles does not match input number of profiles, '
                          f'{rsk_num_profiles} != {num_profiles}. Recomputing profiles...')
            # If the number of profiles does not match the number of profiles in the log,
            # compute the profiles (distinguish the different profiles) based on
            # pressure and conductivity data
            # todo choose the best pressure and conductivity thresholds
            pressureThreshold = (
                                        max(rsk.data['sea_pressure']) -
                                        min(rsk.data['sea_pressure'])
                                ) * 1 / 4
            rsk.computeprofiles(pressureThreshold=pressureThreshold,
                                conductivityThreshold=0.05)
            if rsk_num_profiles != len(rsk.getprofilesindices(direction="down")):
                print(f'Recomputed number of rsk profiles does not match input '
                      f'number of profiles, {rsk_num_profiles} != {num_profiles}. '
                      f'Ending process!')
                return
        # profileIndices = rsk.getprofilesindices()  # Returns a list of lists
        downcastIndices = rsk.getprofilesindices(direction="down")
        upcastIndices = rsk.getprofilesindices(direction="up")
        # firstDowncastIndices = rsk.getprofilesindices(profiles=1, direction="down")

        # check the number of profiles
        n_profiles = len(downcastIndices)  # get the number of profiles recorded

        if all_last == 'ALL':  # get all profiles within each .rsk file
            profile_range = range(n_profiles)
        elif all_last == 'LAST':
            profile_range = range(n_profiles - 1, n_profiles)
            # export .csv file for each profile
        else:
            print(f'Invalid selection of profiles all_last={all_last}, must specify "ALL" or "LAST"')
            return

        # Iterate through the selected profiles in one rsk file
        for i in profile_range:
            downcast_dataframe = pd.DataFrame(rsk.data).loc[downcastIndices[i]]
            upcast_dataframe = pd.DataFrame(rsk.data).loc[upcastIndices[i]]
            # downcast = list(itertools.islice(
            #     rsk.casts(pyrsktools.Region.CAST_DOWN), i, i + 1))[
            #     0].npsamples()  # separate samples for each downcast file
            # downcast_dataframe = pd.DataFrame(data=downcast,
            #                                   columns=downcast.dtype.names)  # convert data into pandas data frame
            #
            # upcast = list(itertools.islice(
            #     rsk.casts(pyrsktools.Region.CAST_UP), i, i + 1))[0].npsamples()
            # upcast_dataframe = pd.DataFrame(data=upcast, columns=upcast.dtype.names)

            column_names = list(downcast_dataframe.columns)  # read the column names
            channel_units = [chan.units for chan in rsk.channels]

            column_names[0] = 'Time(yyyy-mm-dd HH:MM:ss.FFF)'  # update time

            for j in range(1, len(column_names)):  # update the column names
                column_names[j] = column_names[j] + "(" + channel_units[j - 1] + ")"

            downcast_dataframe.columns = column_names  # update column names in downcast data frame
            upcast_dataframe.columns = column_names

            downcast_dataframe["Cast_direction"] = "d"  # add a column for cast direction
            downcast_dataframe["Event"] = current_profile  # add a column for event number - count the profiles

            upcast_dataframe["Cast_direction"] = "u"
            upcast_dataframe["Event"] = current_profile

            # combine downcast and upcast into one profile
            profile_data = pd.concat([downcast_dataframe, upcast_dataframe])

            profile_name = f'{os.path.basename(filename)[:-4]}_profile{str(current_profile).zfill(4)}.csv'

            # profile_data['Event'] = e_num + 1
            profile_data.to_csv(dest_dir + profile_name)  # export each profile
            current_profile = current_profile + 1  # sequential profiles through the files
    return


# ------------------------- step 1a - alternative if rsk file cant be used and an excel file is used instead...........

def READ_EXCELrsk(dest_dir, year, cruise_number, event_start, all_last):
    """
    #function to read in an excel (.xlxs) file exported from RUSKIN software using the rbr .rsk file.
   """

    files = os.listdir(dest_dir)  # list all the files in dest_dir
    files = list(filter(lambda f: f.endswith('.xlsx'), files))  # keep the rsk xlsx files only (make sure no other xlsx)
    n_files = len(files)  # get the number of files

    current_profile = event_start

    for k in range(0, n_files, 1):
        filename = str(dest_dir) + str(files[k])  # full path and name of .rsk file

        # extract a dataframe from the excel sheets
        # hourstonh 2022-01-25: xlrd package does not read xlsx files any more
        # https://groups.google.com/g/python-excel/c/IRa8IWq_4zk/m/Af8-hrRnAgAJ?pli=1 See release notes
        df1 = pd.read_excel(filename, sheet_name='Data', skiprows=[0], engine='openpyxl')  # engine=openpyxl
        # print('printing df1')
        # print(df1)

        # print(df1.sheetnames)

        df2 = pd.read_excel(filename, sheet_name='Profile_annotation', skiprows=[0], engine='openpyxl')
        # df3 = pd.read_excel(filename, sheet_name='Metadata', skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
        #                     usecols=[2], engine='openpyxl')
        # print(df1.keys)
        df1['Time'] = pd.to_datetime(df1['Time'])
        df2['Time 1'] = pd.to_datetime(df2['Time 1'])
        df2['Time 2'] = pd.to_datetime(df2['Time 2'])

        down_times = pd.DataFrame()
        up_times = pd.DataFrame()

        # find the start and end times for each profile
        down_times['Start'] = df2['Time 1'][1::3]
        down_times['End'] = df2['Time 2'][1::3]
        down_times.index = range(len(down_times))
        up_times['Start'] = df2['Time 1'][2::3]
        up_times['End'] = df2['Time 2'][2::3]
        up_times.index = range(len(up_times))

        n_times = len(list(down_times['Start']))

        # ctd_data = pd.DataFrame()

        # Iterate through the profiles in a single file
        # Change the range depending on if "All" or "Last"
        range_start = 0 if all_last == 'ALL' else n_times - 1
        # for i in range(0, n_times, 1):
        for i in range(range_start, n_times):
            down_start_time = down_times['Start'][i]
            down_end_time = down_times['End'][i]
            up_start_time = up_times['Start'][i]
            up_end_time = up_times['End'][i]

            # extract data for each profile - using start and end times
            downcast = df1[(df1['Time'] > down_start_time) & (df1['Time'] <= down_end_time)]
            downcast['Cast_direction'] = 'd'
            # Add event numbers - need an event start number (i + 1 only works if one file and the events start at 1.
            # alter code to read in multiple files and create an Event_Start_List to loop through?
            # or if events aren't sequential a list of all event numbers to add at the end?
            current_profile = k + (i - range_start) + event_start  # hourstonh
            # downcast['Event'] = i + event_start  # get this from the log
            downcast['Event'] = current_profile
            upcast = df1[(df1['Time'] > up_start_time) & (df1['Time'] <= up_end_time)]
            upcast['Cast_direction'] = 'u'
            # upcast['Event'] = i + event_start  # get this from the log
            upcast['Event'] = current_profile
            profile_data = pd.concat([downcast, upcast])  # combine downcast and upcast into one profile

            # Fix split character to account for forward and double-backward slashes
            # Also take period off with the file extension: [0:-5] instead of [0:-4]
            split_char = '/' if '/' in filename else '\\'

            # if all_last == 'LAST':
            #     profile_name = filename.split("/")[-1][0:-4].upper() + "_profile" + str(i + current_profile).zfill(
            #         4) + ".csv"  # profile name #i + from log
            # elif all_last == 'ALL':
            #     profile_name = filename.split("/")[-1][0:-4].upper() + "_profile" + str(i + event_start).zfill(
            #         4) + ".csv"  # profile name #i + from log
            #     output_filename = year + "-" + cruise_number + "_CTD_DATA.csv"  # all data file name
            #
            #     ctd_data = ctd_data.append(profile_data, ignore_index=True)  # combine profiles into one file
            #     profile_data.rename({'Time': 'Time(yyyy-mm-dd HH:MM:ss.FFF)'}, axis=1, inplace=True)
            #     profile_data.to_csv(dest_dir + profile_name)  # export each profile
            #     current_profile = current_profile + 1

            profile_name = filename.split(split_char)[-1][0:-5].upper() + "_profile" + str(current_profile).zfill(
                4) + ".csv"  # profile name #i + from log
            print(profile_name)

            output_filename = year + "-" + cruise_number + "_CTD_DATA.csv"  # all data file name

            # hourstonh commented out
            # ctd_data = ctd_data.append(profile_data, ignore_index=True)  # combine profiles into one file
            profile_data.rename({'Time': 'Time(yyyy-mm-dd HH:MM:ss.FFF)'}, axis=1, inplace=True)

            profile_data.to_csv(dest_dir + profile_name, index=False)  # export each profile #, index=False

            # output_filename = year + "-" + cruise_number + "_CTD_DATA.csv"
            # all data file name#ctd_data.to_csv(dest_dir + output_filename)

        if all_last == 'ALL':
            event_start = current_profile
        # ctd_data.to_csv(dest_dir + output_filename)

        return


# ------------ step 1b: .rsk file in full structure - combine profiles into one .csv file ------------


def MERGE_FILES(dest_dir: str, year: str, cruise_number: str, event_from: str = 'filename'):
    """
    Read in multiple csv file and output one csv format
    Inputs:
        - folder, year, cruise_number
        - event_from: where to get the event numbers. "filename" or "header-merge"
    Outputs:
        - csv file: csv files containing the profile data
   """
    files = os.listdir(dest_dir)  # list all the files in dest_dir
    # keep the profile csv files only
    files = list(filter(lambda fname: 'profile' in fname, files))
    event_csv = pd.read_csv(dest_dir + year + '-'
                            + cruise_number + '_header-merge.csv')

    files.sort(key=lambda x: int(x[-8:-4]))  # reorder the files according to profile number
    n_profiles = len(files)
    ctd_data = pd.DataFrame()  # set an empty pandas dataframe to store data

    for i in range(n_profiles):
        input_filename = str(dest_dir) + str(files[i])
        # data = pd.read_csv(input_filename, sep=',', skiprows=range(0, 20),
        #                    encoding= 'unicode_escape') #original by Lu
        data = pd.read_csv(input_filename, sep=',', encoding='unicode_escape')
        if event_from == 'filename':
            data.loc[:, 'Event'] = np.repeat(int(files[i][-8:-4]), len(data))
        elif event_from == 'header-merge':
            # Use this if you want non-sequential events, but won't work auto processing (cast i+1 etc...)
            data.loc[:, 'Event'] = np.repeat(event_csv.loc[i, 'LOC:Event Number'],
                                             len(data))

        # data['Event'] = int(files[i][-8:-4])
        # data['Time'] = pd.to_datetime(data['Time'])        #might not be needed
        ctd_data = pd.concat([ctd_data, data], ignore_index=True)
    if ctd_data.columns.to_list()[0] == '//Time(yyyy-mm-dd HH:MM:ss.FFF)':
        ctd_data.rename({'//Time(yyyy-mm-dd HH:MM:ss.FFF)': 'Time(yyyy-mm-dd HH:MM:ss.FFF)'},
                        axis=1, inplace=True)

    output_filename = year + '-' + cruise_number + '_CTD_DATA.csv'

    ctd_data.to_csv(dest_dir + output_filename, index=False)
    return


# ----------------------------   Step 2. Create Metadata dictionary    -------------------------------------------------
def CREATE_META_DICT(dest_dir: str, rsk_file: str, year: str, cruise_number: str,
                     rsk_time1=None, rsk_time2=None) -> dict:
    """
     Read in a csv file and output a metadata dictionary
     Inputs:
         - folder, file, year, cruise_number:
         - rsk_file: rsk-format file containing raw RBR data & csv file containing metadata
     Outputs:
         - metadata dictionary
     """
    meta_dict = {}
    # function to export .csv files from .rsk file.
    rsk_full_path = str(dest_dir) + str(rsk_file)  # full path and name of a .rsk file
    rsk = pyrsktools.RSK(rsk_full_path, readHiddenChannels=False)  # load up an RSK
    rsk.open()
    rsk.readdata(t1=rsk_time1, t2=rsk_time2)

    header_input_name = str(year) + '-' + str(cruise_number) + '_header-merge.csv'
    header_input_filename = dest_dir + header_input_name
    header = pd.read_csv(header_input_filename, header=0)

    # get the time interval for the IOS Header (sampling period)
    time_input_name = str(year) + '-' + str(cruise_number) + '_CTD_DATA.csv'
    time_input_filename = dest_dir + time_input_name
    time_input = pd.read_csv(time_input_filename)
    time_interval = pd.to_datetime(time_input['Time(yyyy-mm-dd HH:MM:ss.FFF)'][2]) - pd.to_datetime(
        time_input['Time(yyyy-mm-dd HH:MM:ss.FFF)'][1])
    time_interval = str(time_interval)
    time_interval = time_interval[-8:-3]

    csv_input_name = str(year) + '-' + str(cruise_number) + '_METADATA.csv'
    csv_input_filename = dest_dir + csv_input_name

    meta_csv = pd.read_csv(csv_input_filename)

    # Fill in metadata values
    meta_dict['Processing_Start_time'] = datetime.now()
    meta_dict['Instrument_information'] = rsk.instrument
    meta_dict['Sampling_Interval'] = time_interval
    print('time_interval', time_interval)
    # meta_dict['RSK_filename'] = rsk.name
    meta_dict['RSK_filename'] = meta_csv['Value'][meta_csv['Name'] == 'RSK_filename'].values[
                                0:]  # if more than one (list??)
    # meta_dict['Channels'] = list(rsk.channels.keys())
    meta_dict['Channels'] = rsk.channelNames
    # meta_dict['Channel_details'] = list(rsk.channels.items())
    meta_dict['Channel_details'] = rsk.channels
    meta_dict['Number_of_channels'] = len(rsk.channels)

    for key in ['number_of_profiles',
                'Data_description', 'Final_file_type',
                'Mission', 'Agency', 'Country', 'Project', 'Scientist',
                'Platform', 'Instrument_Model', 'Serial_number',
                'Instrument_type']:
        meta_dict[key] = meta_csv['Value'][meta_csv['Name'] == key].values[0]
    # meta_dict['Data_description'] = meta_csv['Value'][meta_csv['Name'] == 'Data_description'].values[0]
    # meta_dict['Final_file_type'] = meta_csv['Value'][meta_csv['Name'] == 'Final_file_type'].values[0]
    # meta_dict['Number_of_channels'] = meta_csv['Value'][meta_csv['Name'] == 'Number_of_channels'].values[0]
    # # meta_dict['Number_of_channels'] = len(list(rsk.channels.items())
    # meta_dict['Mission'] = meta_csv['Value'][meta_csv['Name'] == 'Mission'].values[0]
    # meta_dict['Agency'] = meta_csv['Value'][meta_csv['Name'] == 'Agency'].values[0]
    # meta_dict['Country'] = meta_csv['Value'][meta_csv['Name'] == 'Country'].values[0]
    # meta_dict['Project'] = meta_csv['Value'][meta_csv['Name'] == 'Project'].values[0]
    # meta_dict['Scientist'] = meta_csv['Value'][meta_csv['Name'] == 'Scientist'].values[0]
    # meta_dict['Platform'] = meta_csv['Value'][meta_csv['Name'] == 'Platform'].values[0]
    # meta_dict['Instrument_Model'] = meta_csv['Value'][meta_csv['Name'] == 'Instrument_Model'].values[0]
    # meta_dict['Serial_number'] = meta_csv['Value'][meta_csv['Name'] == 'Serial_number'].values[0]
    # meta_dict['Instrument_type'] = meta_csv['Value'][meta_csv['Name'] == 'Instrument_type'].values[0]
    meta_dict['Location'] = header
    return meta_dict


# ---------------  step 3. Add 6 line headers to CTD_DATA.csv file ------------------------
# Prepare data file with six line header for further applications in IOS Shell


def ADD_6LINEHEADER_2(dest_dir: str, year: str, cruise_number: str):
    """
     Read in a csv file and output in csv format for IOSShell
     Filter through the csv and remove un-needed columns.
     Inputs:
         - folder, file, year, cruise: csv-format file containing raw RBR CTD data
         exported from rsk file
     Outputs:
         - csv file: csv files containing 6-header line for IOSShell
     """
    # Add six-line header to the .csv file.
    # This file could be used for data processing via IOSShell
    input_name = str(year) + '-' + str(cruise_number) + '_CTD_DATA.csv'
    output_name = str(year) + "-" + str(cruise_number) + '_CTD_DATA-6linehdr.csv'
    input_filename = os.path.join(dest_dir, input_name)
    ctd_data = pd.read_csv(input_filename, header=0)

    ctd_data['Time(yyyy-mm-dd HH:MM:ss.FFF)'] = ctd_data['Time(yyyy-mm-dd HH:MM:ss.FFF)'].str[:19]
    ctd_data['Date'] = pd.to_datetime(ctd_data['Time(yyyy-mm-dd HH:MM:ss.FFF)'])  # add new column of Date
    ctd_data['Date'] = [d.date() for d in ctd_data['Date']]
    ctd_data['TIME:UTC'] = pd.to_datetime(ctd_data['Time(yyyy-mm-dd HH:MM:ss.FFF)'])  # add new column of time
    ctd_data['TIME:UTC'] = [d.time() for d in ctd_data['TIME:UTC']]
    ctd_data['Date'] = pd.to_datetime(ctd_data['Date'], format='%Y-%m-%d').dt.strftime('%d/%m/%Y')

    # make a list of columns to drop
    drop_list = ['Temperature .1(Â°C)', 'speedofsound(m/s)', 'Temperature .1', 'Temperature.1',
                 'Speed of sound ', 'Speed of sound', 'speed_of_sound(m/s)',
                 'specificconductivity(ÂµS/cm)', 'specific_conductivity(ÂµS/cm)',
                 'Density anomaly', 'Density anomaly ', 'Dissolved Oâ,,Concentration',
                 'Dissolved OÃ¢Â‚Â‚ concentration ', 'Dissolved OÃ¢Â‚Â‚ concentration',
                 'Specific conductivity ', 'Dissolved O₂ concentration',
                 'Specific conductivity', 'Dissolved Oâ\x82\x82 concentration ',
                 'Dissolved Oâ\x82\x82 concentration', 'Turbidity', 'Dissolved O2 concentration']

    # drop first indexing row and Time(HH....) plus everything in drop_list
    if 'Unnamed: 0' in ctd_data.columns[0]:
        drop_list.append('Unnamed: 0')
    drop_list.append('Time(yyyy-mm-dd HH:MM:ss.FFF)')
    # Ignore KeyError if columns in drop_list do not exist in the dataframe
    ctd_data.drop(columns=drop_list, inplace=True, errors='ignore')
    # ctd_data.reset_index(drop=True, inplace=True)

    col_list = ctd_data.columns.tolist()
    print(col_list)
    # n_col_list = len(col_list)

    # set empty column names
    # dict.fromkeys(ctd_data.columns, np.arange(len(ctd_data.columns)))
    column_names = {old: new for old, new in
                    zip(col_list, np.arange(len(ctd_data.columns)))}
    ctd_data.rename(columns=column_names, inplace=True)  # remove column names

    # append header information into the empty lists
    channel_list = ['Y', 'Y', 'N', 'Y', 'Y', 'Y', 'Y', 'Y', 'N', 'Y', 'Y', 'Y']
    index_list = ['Conductivity', 'Temperature', 'Pressure_Air', 'Fluorescence',
                  'Oxygen:Dissolved:Saturation', 'Pressure', 'Depth', 'Salinity:CTD',
                  'Cast_direction', 'Event_number', 'Date', 'TIME:UTC']
    unit_list = ['mS/cm', 'deg C(ITS90)', 'decibar', 'mg/m^3', '%', 'decibar',
                 'meters', 'PSS-78', 'n/a', 'n/a', 'n/a', 'n/a']
    input_format_list = ['R4', 'R4', 'R4', 'R4', 'R4', 'R4', 'R4', 'R4', ' ', 'I4',
                         'D:dd/mm/YYYY', 'T:HH:MM:SS']
    output_format_list = ['R4:F11.4', 'R4:F9.4', 'R4:F7.1', 'R4:F8.3', 'R4:F11.4',
                          'R4:F7.1', 'R4:F7.1', 'R4:F9.4', ' ', 'I:I4', 'D:YYYY/mm/dd',
                          'T:HH:MM:SS']
    na_value_list = ['-99', '-99', '-99', '-99', '-99', '-99', '-99', '-99', '', '-99', '', '']

    # Create empty lists
    channel = []
    index = []
    unit = []
    input_format = []
    output_format = []
    na_value = []

    # todo condense repeating code somehow?
    for col in col_list:
        if col in ['conductivity(mS/cm)', 'Conductivity ', 'Conductivity']:
            channel.append(channel_list[0]), index.append(index_list[0]), unit.append(
                unit_list[0]), input_format.append(input_format_list[0]), output_format.append(
                output_format_list[0]), na_value.append(na_value_list[0])
        elif col in ['temperature(Â°C)', 'Temperature ', 'Temperature']:
            channel.append(channel_list[1]), index.append(index_list[1]), unit.append(
                unit_list[1]), input_format.append(input_format_list[1]), output_format.append(
                output_format_list[1]), na_value.append(na_value_list[1])
        elif col in ['pressure(dbar)', 'Pressure ', 'Pressure']:
            channel.append(channel_list[2]), index.append(index_list[2]), unit.append(
                unit_list[2]), input_format.append(input_format_list[2]), output_format.append(
                output_format_list[2]), na_value.append(na_value_list[2])
        elif col in ['chlorophyll(Âµg/l)', 'Chlorophyll a ', 'Chlorophyll a',
                     'chlorophyll_a(Âµg/l)']:
            channel.append(channel_list[3]), index.append(index_list[3]), unit.append(
                unit_list[3]), input_format.append(input_format_list[3]), output_format.append(
                output_format_list[3]), na_value.append(na_value_list[3])
        elif col in ['oxygensaturation(%)', 'Dissolved OÃ¢Â‚Â‚ saturation ',
                     'Dissolved Oâ\x82\x82 saturation ', 'Dissolved O2 saturation',
                     'Dissolved OÃ¢Â‚Â‚ saturation', 'Dissolved Oâ\x82\x82 saturation',
                     'dissolved_o2_saturation(%)']:
            channel.append(channel_list[4]), index.append(index_list[4]), unit.append(
                unit_list[4]), input_format.append(input_format_list[4]), output_format.append(
                output_format_list[4]), na_value.append(na_value_list[4])
        elif col in ['seapressure(dbar)', 'Sea pressure', 'Sea pressure ',
                     'sea_pressure(dbar)']:
            channel.append(channel_list[5]), index.append(index_list[5]), unit.append(
                unit_list[5]), input_format.append(input_format_list[5]), output_format.append(
                output_format_list[5]), na_value.append(na_value_list[5])
        elif col in ['depth(m)', 'Depth ', 'Depth']:
            channel.append(channel_list[6]), index.append(index_list[6]), unit.append(
                unit_list[6]), input_format.append(input_format_list[6]), output_format.append(
                output_format_list[6]), na_value.append(na_value_list[6])
        elif col in ['salinity(PSU)', 'Salinity ', 'Salinity']:
            channel.append(channel_list[7]), index.append(index_list[7]), unit.append(
                unit_list[7]), input_format.append(input_format_list[7]), output_format.append(
                output_format_list[7]), na_value.append(na_value_list[7])
        elif col == 'Cast_direction':
            channel.append(channel_list[8]), index.append(index_list[8]), unit.append(
                unit_list[8]), input_format.append(input_format_list[8]), output_format.append(
                output_format_list[8]), na_value.append(na_value_list[8])
        elif col == 'Event':
            channel.append(channel_list[9]), index.append(index_list[9]), unit.append(
                unit_list[9]), input_format.append(input_format_list[9]), output_format.append(
                output_format_list[9]), na_value.append(na_value_list[9])
        elif col == 'Date':
            channel.append(channel_list[10]), index.append(index_list[10]), unit.append(
                unit_list[10]), input_format.append(input_format_list[10]), output_format.append(
                output_format_list[10]), na_value.append(na_value_list[10])
        elif col == 'TIME:UTC':
            channel.append(channel_list[11]), index.append(index_list[11]), unit.append(
                unit_list[11]), input_format.append(input_format_list[11]), output_format.append(
                output_format_list[11]), na_value.append(na_value_list[11])

    header = pd.DataFrame([channel, index, unit, input_format, output_format, na_value])
    # print(header[4])
    # print(ctd_data)
    # column_names_header = dict.fromkeys(header.columns, '')  # set empty column names
    # header = header.rename(columns=column_names_header)

    # If plan shapes not aligned, then may need to add another variable to drop_list
    ctd_data_header = pd.concat((header, ctd_data))
    ctd_data_header.to_csv(dest_dir + output_name, index=False, header=False)
    return


def plot_track_location(dest_dir, year: str, cruise_number: str, left_lon=None,
                        right_lon=None, bot_lat=None, top_lat=None):
    """
     Read in a csv file and output a map
     Inputs:
         - folder, year, cruise: csv file containing raw RBR data
         - left_lon, right_lon, bot_lat, top_lat: longitude and latitude of map extent
     Outputs:
         - A map showing sampling locations
     """
    # Create a folder for figures if it doesn't already exist
    figure_dir = os.path.join(dest_dir, 'FIG')
    if not os.path.exists(figure_dir):
        os.makedirs(figure_dir)

    input_name = str(year) + '-' + str(cruise_number) + '_header-merge.csv'
    input_filename = dest_dir + input_name
    header = pd.read_csv(input_filename, header=0)
    header['lat_degree'] = header['LOC:LATITUDE'].str[:2].astype(int)
    header['lat_min'] = header['LOC:LATITUDE'].str[3:10].astype(float)
    header['lat'] = header['lat_degree'] + header['lat_min'] / 60
    header['lon_degree'] = header['LOC:LONGITUDE'].str[:3].astype(int)
    header['lon_min'] = header['LOC:LONGITUDE'].str[4:12].astype(float)
    header['lon'] = 0 - (header['lon_degree'] + header['lon_min'] / 60)
    event = header['LOC:STATION'].astype(str)

    lon = header['lon'].tolist()
    lat = header['lat'].tolist()
    # event = event.tolist()

    coord_limits = [np.floor(np.min(header['lon']) * 10) / 10,
                    np.ceil(np.max(header['lon']) * 10) / 10,
                    np.floor(np.min(header['lat']) * 10) / 10,
                    np.ceil(np.max(header['lat']) * 10) / 10]

    left_lon = coord_limits[0] if left_lon is None else left_lon
    right_lon = coord_limits[1] if right_lon is None else right_lon
    bot_lat = coord_limits[2] if bot_lat is None else bot_lat
    top_lat = coord_limits[3] if top_lat is None else top_lat

    m = Basemap(llcrnrlon=left_lon, llcrnrlat=bot_lat,
                urcrnrlon=right_lon, urcrnrlat=top_lat,
                projection='lcc',
                resolution='h', lat_0=0.5 * (bot_lat + top_lat),
                lon_0=0.5 * (left_lon + right_lon))  # lat_0=53.4, lon_0=-129.0)

    x, y = m(lon, lat)

    fig = plt.figure(num=None, figsize=(8, 6), dpi=100)
    m.drawcoastlines(linewidth=0.2)
    m.drawmapboundary(fill_color='white')
    # m.fillcontinents(color='0.8')
    m.drawrivers()

    m.scatter(x, y, marker='D', color='m', s=5)
    # m.plot(x, y, marker='D', color='m', markersize=4)
    #   for event, xpt, ypt in zip(event, x, y):
    #       plt.text(xpt, ypt, event)

    parallels = np.arange(bot_lat, top_lat, 0.5)
    # parallels = np.arange(48., 54, 0.2), parallels = np.linspace(bot_lat, top_lat, 10)
    m.drawparallels(parallels, labels=[True, False, True, False])  # draw parallel lat lines
    meridians = np.arange(left_lon, right_lon, 0.5)
    m.drawmeridians(meridians, labels=[False, False, False, True])
    plt.title(year + '-' + cruise_number)
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'Fig_1.png'))
    plt.close()

    # ----- create a second map w/ Cartopy # just to double check - had an issue with Basemap once only

    map = plt.axes(projection=ccrs.PlateCarree())
    map.set_extent([left_lon, right_lon, bot_lat, top_lat])  # try left_lon, right_lon, bot_lat, top_lat
    x, y = (lon, lat)
    map.coastlines()
    gl = map.gridlines(crs=ccrs.PlateCarree(), linewidth=0.5, color='black', alpha=0.5,
                       linestyle='--', draw_labels=True)
    gl.top_labels = False
    gl.left_labels = True
    gl.bottom_labels = True
    gl.right_labels = False
    gl.ylocator = LatitudeLocator()
    gl.xformatter = LongitudeFormatter()
    gl.yformatter = LatitudeFormatter()

    gl.xlabel_style = {'color': 'black', 'weight': 'bold', 'size': 6}
    gl.ylabel_style = {'color': 'black', 'weight': 'bold', 'size': 6}

    cax = plt.scatter(x, y, transform=ccrs.PlateCarree(), marker='.', color='red', s=25)
    plt.title(year + '-' + cruise_number)
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'Figure_1.png'))
    plt.close()
    return


# ---------------------------- Step 5.  create variable dictionaries  ---------------------------------------
# input: .csv file

# output variables: cast cast_d, cast_u


# -------------   step 6. Plot and Check and correct for zero-order hold   ---------------


def PLOT_PRESSURE_DIFF(dest_dir: str, year: str, cruise_number: str, input_ext: str):
    """
     Read in a csv file and output a plot to check zero-order holds
     Inputs:
         - folder, year, cruise: csv file containing raw RBR data
         - input_ext: '_CTD_DATA-6linehdr.csv' or '_CTD_DATA-6linehdr_corr_hold.csv'
     Outputs:
         - a plot showing the time derivative of raw pressure
     """

    # Create a folder for figures if it doesn't already exist
    figure_dir = os.path.join(dest_dir, 'FIG')
    if not os.path.exists(figure_dir):
        os.makedirs(figure_dir)

    # input_name will depend on the need for zero order holds
    input_name = str(year) + "-" + str(cruise_number) + input_ext
    input_filename = dest_dir + input_name
    ctd_data = pd.read_csv(input_filename, header=None, low_memory=False)
    ctd_data = ctd_data.rename(columns=ctd_data.iloc[1])  # assign the second row as column names
    ctd_data = ctd_data.rename(
        columns={'Oxygen:Dissolved:Saturation': 'Oxygen', 'Salinity:CTD': 'Salinity',
                 'TIME:UTC': 'TIME'})
    ctd = ctd_data.iloc[6:]
    ctd.index = np.arange(0, len(ctd))
    # ctd = ctd[1000:4000] # to limit the number of records plotted -

    pressure = ctd['Pressure'].apply(pd.to_numeric)
    pressure_lag = pressure[1:]
    pressure_lag.index = np.arange(0, len(pressure_lag))
    pressure_diff = pressure_lag - pressure

    fig = plt.figure(num=None, figsize=(14, 6), dpi=100)
    plt.plot(pressure_diff, color='blue', linewidth=0.5, label='Pressure_diff')
    plt.ylabel('Pressure (decibar)')
    plt.xlabel('Scans')
    plt.grid()
    plt.legend()
    plt.title(year + '-' + cruise_number + ' ' + input_ext)
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'zero_order_holds_' + input_ext + '.png'))
    plt.close(fig)
    # check the plot then save it as Fig_2 or Fig_3.
    return


def check_for_zoh(dest_dir, year: str, cruise_number: str,
                  sampling_interval: float) -> bool:
    """
    Compute first order differences on pressure data to determine whether
    a correction for zero-order holds is needed.
    From DFO Technical Report 314:
    'The analog-to-digital (A2D) converter on RBR instruments must recalibrate once per
    minute.'
    inputs
        - dest_dir: destination directory
        - year
        - cruise_number
        - sampling_interval: amount of time in seconds between records
    """

    input_name = str(year) + "-" + str(cruise_number) + '_CTD_DATA-6linehdr.csv'
    input_filename = dest_dir + input_name
    ctd_data = pd.read_csv(input_filename, header=None, low_memory=False)
    # assign the second row as column names
    ctd_data = ctd_data.rename(columns=ctd_data.iloc[1])
    ctd_data = ctd_data.rename(
        columns={'Oxygen:Dissolved:Saturation': 'Oxygen', 'Salinity:CTD': 'Salinity',
                 'TIME:UTC': 'TIME'})
    ctd = ctd_data.iloc[6:]
    ctd.index = np.arange(0, len(ctd))

    pressure = ctd['Pressure'].apply(pd.to_numeric)
    pressure_diffs = np.diff(pressure)

    print('Number of pressure records:', len(pressure))
    print('Sum of zero pressure differences:', sum(pressure_diffs == 0))
    print('Intervals between zero pressure differences:',
          np.diff(np.where(pressure_diffs == 0)[0]), sep='\n')

    sec2min = 1/60  # Convert seconds to minutes b/c sampling interval in seconds
    if sum(pressure_diffs == 0) >= np.floor(len(pressure) * sampling_interval * sec2min):
        zoh_correction_needed = True
    else:
        zoh_correction_needed = False
    return zoh_correction_needed


def CREATE_CAST_VARIABLES(year: str, cruise_number: str, dest_dir, input_ext: str):
    """
     Read in a csv file and output data dictionaries to hold profile data
     Inputs:
         - folder, year, cruise: csv file containing raw RBR data
         - input_ext: '_CTD_DATA-6linehdr.csv' or '_CTD_DATA-6linehdr_corr_hold.csv'
     Outputs:
         - three dictionaries containing casts, downcasts and upcasts
     """
    input_name = str(year) + "-" + str(cruise_number) + input_ext
    input_filename = dest_dir + input_name
    ctd_data = pd.read_csv(input_filename, header=None, low_memory=False)  # read data without header
    ctd_data = ctd_data.rename(columns=ctd_data.iloc[1])  # assign the second row as column names
    ctd_data = ctd_data.rename(
        columns={'Oxygen:Dissolved:Saturation': 'Oxygen', 'Salinity:CTD': 'Salinity',
                 'TIME:UTC': 'TIME'})
    ctd = ctd_data.iloc[6:]
    # drop NaNs from Zero order holds correction (not including O or F in case they aren't present - but will capture)
    if input_ext == '_CTD_DATA-6linehdr.csv':
        pass  # ctd = ctd
    elif input_ext == '_CTD_DATA-6linehdr_corr_hold.csv':
        ctd.dropna(axis=0, subset=['Conductivity', 'Temperature', 'Pressure_Air',
                                   'Pressure', 'Depth', 'Salinity'],
                   how='all', inplace=True)  # I don't think this does anything - NaNs now dropped in Correct_Hold stage
    ctd = ctd.copy()
    cols = ctd.columns[0:-4]
    # cols_names = ctd.columns.tolist()
    ctd[cols] = ctd[cols].apply(pd.to_numeric, errors='coerce', axis=1)
    ctd['Cast_direction'] = ctd['Cast_direction'].str.strip()

    n = ctd['Event_number'].nunique()

    var_holder = {}
    for i in range(1, n + 1):
        # Assign values of type DataFrame
        var_holder['cast' + str(i)] = ctd.loc[(ctd['Event_number'] == str(i))]
    # var_holder['Processing_history'] = ""

    # Downcast dictionary
    var_holder_d = {}
    for i in range(1, n + 1):
        var_holder_d['cast' + str(i)] = ctd.loc[(ctd['Event_number'] == str(i)) &
                                                (ctd['Cast_direction'] == 'd')]
    # var_holder_d['Processing_history'] = ""

    # Upcast dictionary
    var_holder_u = {}
    for i in range(1, n + 1, 1):
        var_holder_u['cast' + str(i)] = ctd.loc[(ctd['Event_number'] == str(i)) &
                                                (ctd['Cast_direction'] == 'u')]
    # var_holder_u['Processing_history'] = ""

    return var_holder, var_holder_d, var_holder_u


# --------------------------------------   plot data from all profiles  ----------------------------------------


def format_profile_plot(ax, var_name, var_units, plot_title,
                        add_legend: bool = False):
    """
    inputs:
        - ax: from fig, ax = plt.subplots()
        - var_name: one of Temperature, Conductivity, Salinity,
                    fluorescence, oxygen
        - var_units: the units corresponding to the selected var_name
        - plot_title: Should indicate which processing step the plots are at
        - add_legend: If true then add a legend to the plot
    """
    ax.invert_yaxis()
    ax.xaxis.set_label_position('top')
    ax.xaxis.set_ticks_position('top')
    if var_units is not None:
        ax.set_xlabel(f'{var_name} ({var_units})')
    else:
        ax.set_xlabel(f'{var_name}')
    ax.set_ylabel('Pressure (decibar)')
    ax.set_title(plot_title, fontsize=5)
    if add_legend:
        ax.legend()
    plt.tight_layout()
    return


def first_plots(year: str, cruise_number: str, dest_dir, input_ext: str):
    """ Plot pre-processing and after Zero-order Holds if needed
    inputs:
        - input_ext: '_CTD_DATA-6linehdr.csv' or '_CTD_DATA-6linehdr_corr_hold.csv'
    """

    # Create a folder for figures if it doesn't already exist
    figure_dir = os.path.join(dest_dir, 'FIG')
    if not os.path.exists(figure_dir):
        os.makedirs(figure_dir)

    # Input ext specifies whether to use 6lineheader file with or without
    # the zero-order hold removed
    cast, cast_d, cast_u = CREATE_CAST_VARIABLES(year, cruise_number,
                                                 dest_dir, input_ext)

    # number_of_colors = len(cast)
    # color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
    #          for i in range(number_of_colors)]

    # get variables
    vars_available = list(dict.fromkeys(cast['cast1']))

    # Iterate through all the channels, plot data from all casts on one plot per channel
    for j, var in enumerate(VARIABLES_POSSIBLE):
        if var in vars_available:
            fig, ax = plt.subplots()
            for i in range(0, len(cast), 1):
                ax.plot(cast_d['cast' + str(i + 1)].loc[:, var],
                        cast_d['cast' + str(i + 1)].Pressure, color=VARIABLE_COLOURS[j])
                # label='cast' + str(i + 1))
                ax.plot(cast_u['cast' + str(i + 1)].loc[:, var],
                        cast_u['cast' + str(i + 1)].Pressure, '--', color=VARIABLE_COLOURS[j])
                # label='cast' + str(i + 1))
                # ax.plot(cast_d['cast1'].Salinity, cast_d['cast1'].Pressure, color='blue', label='cast1')
                # ax.plot(cast_u['cast1'].Salinity, cast_u['cast1'].Pressure, '--', color='blue', label='cast1')
            format_profile_plot(ax, var, VARIABLE_UNITS[j], 'Pre-Processing')
            plt.savefig(os.path.join(figure_dir, f'Pre_Processing_{var[0]}.png'))
            plt.close(fig)

    # TS Plot
    fig, ax = plt.subplots()
    for i in range(0, len(cast), 1):
        ax.plot(cast_d['cast' + str(i + 1)].Salinity,
                cast_d['cast' + str(i + 1)].Temperature, color='b',
                label='cast' + str(i + 1))
        # ax.plot(cast_d['cast11'].Salinity, cast_d['cast11'].Temperature, color='blue')
    ax.set_xlabel('Salinity')
    ax.set_ylabel('Temperature (C)')
    ax.set_title('Pre-Processing T-S Plot')
    # ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'Pre_Processing_T-S.png'))
    plt.close(fig)

    # todo confirm with sam if everything below this point can be deleted
    # -----------------------  Plot profiles by group --------------------------
    plot_by_group = False
    if plot_by_group:
        # T, C, O, S, F for each profile in one plot
        fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(1, 5, sharey=True)
        # Temperature
        ax1.plot(cast_d['cast1'].Temperature, cast_d['cast1'].Pressure, color='red',
                 label='cast_down')
        ax1.plot(cast_u['cast1'].Temperature, cast_u['cast1'].Pressure, '--', color='red',
                 label='cast_up')
        ax1.set_ylabel('Pressure(decibar)', fontsize=8)
        ax1.set_ylim(ax1.get_ylim()[::-1])
        ax1.set_xlabel('Temperature(C)', fontsize=8)
        ax1.xaxis.set_label_position('top')
        ax1.xaxis.set_ticks_position('top')
        ax.set_title('Pre-Processing', fontsize=5)
        ax1.legend()

        # Conductivity
        ax2.plot(cast_d['cast1'].Conductivity, cast_d['cast1'].Pressure, color='goldenrod',
                 label='cast_down')
        ax2.plot(cast_u['cast1'].Conductivity, cast_u['cast1'].Pressure, '--', color='goldenrod',
                 label='cast1_up')
        ax2.set_ylabel('Pressure(decibar)', fontsize=8)
        ax2.set_ylim(ax1.get_ylim()[::-1])
        ax2.set_xlabel('Conductivity (S/cm)', fontsize=8)
        ax2.xaxis.set_label_position('top')
        ax2.xaxis.set_ticks_position('top')
        ax.set_title('Pre-Processing', fontsize=5)
        ax2.legend()

        # Oxygen
        for var in vars_available:
            if var == 'Oxygen':
                ax3.plot(cast_d['cast1'].Oxygen, cast_d['cast1'].Pressure, color='black',
                         label='cast_down')
                ax3.plot(cast_u['cast1'].Oxygen, cast_u['cast1'].Pressure, '--', color='black',
                         label='cast_up')
                ax3.set_ylabel('Pressure(decibar)', fontsize=8)
                ax3.set_ylim(ax1.get_ylim()[::-1])
                ax3.set_xlabel('Oxygen Saturation (%)', fontsize=8)
                ax3.xaxis.set_label_position('top')
                ax3.xaxis.set_ticks_position('top')
                ax.set_title('Pre-Processing', fontsize=5)
                ax3.legend()
            elif var == 'Fluorescence':
                ax5.plot(cast_d['cast1'].Fluorescence, cast_d['cast1'].Pressure,
                         color='green', label='cast_down')
                ax5.plot(cast_u['cast1'].Fluorescence, cast_u['cast1'].Pressure, '--',
                         color='green', label='cast1_up')
                ax5.set_ylabel('Pressure(decibar)', fontsize=8)
                ax5.set_ylim(ax1.get_ylim()[::-1])
                ax5.set_xlabel('Fluoresence(ug/L)', fontsize=8)
                ax5.xaxis.set_label_position('top')
                ax5.xaxis.set_ticks_position('top')
                ax.set_title('Pre-Processing', fontsize=5)
                ax5.legend()

        # Salinity
        ax4.plot(cast_d['cast1'].Salinity, cast_d['cast1'].Pressure, color='blue',
                 label='cast_down')
        ax4.plot(cast_u['cast1'].Salinity, cast_u['cast1'].Pressure, '--', color='blue',
                 label='cast_up')
        ax4.set_ylabel('Pressure(decibar)', fontsize=8)
        ax4.set_ylim(ax1.get_ylim()[::-1])
        ax4.set_xlabel('Salinity', fontsize=8)
        ax4.xaxis.set_label_position('top')
        ax4.xaxis.set_ticks_position('top')
        ax.set_title('Pre-Processing', fontsize=5)
        ax4.legend()

    # -------------------------   Plot by Index and by Profile-------------------------
    # separate plot for T, C, O, S, F of each profile
    plot_by_index_and_profile = False
    if plot_by_index_and_profile:
        # Temperature
        fig, ax = plt.subplots()
        ax.plot(cast_d['cast1'].Temperature, cast_d['cast1'].Pressure, color='red',
                label='cast_down')
        ax.plot(cast_u['cast1'].Temperature, cast_u['cast1'].Pressure, '--', color='red',
                label='cast_up')
        ax.invert_yaxis()
        ax.xaxis.set_label_position('top')
        ax.xaxis.set_ticks_position('top')
        ax.set_xlabel('Temperature(C)')
        ax.set_ylabel('Pressure (decibar)')
        ax.set_title('Pre-Processing', fontsize=5)
        plt.tight_layout()
        plt.savefig(dest_dir + 'Pre_Cast1_T')
        ax.legend()

        # Salinity
        fig, ax = plt.subplots()
        ax.plot(cast_d['cast1'].Salinity, cast_d['cast1'].Pressure, color='blue',
                label='cast1_d')
        ax.plot(cast_u['cast1'].Salinity, cast_u['cast1'].Pressure, '--', color='blue',
                label='cast1_u')
        ax.invert_yaxis()
        ax.xaxis.set_label_position('top')
        ax.xaxis.set_ticks_position('top')
        ax.set_xlabel('Salinity')
        ax.set_ylabel('Pressure (decibar)')
        ax.set_title('Pre-Processing', fontsize=5)
        ax.legend()
        plt.tight_layout()
        plt.savefig(dest_dir + 'Pre_Cast1_S')

        # Conductivity
        fig, ax = plt.subplots()
        ax.plot(cast_d['cast1'].Conductivity, cast_d['cast1'].Pressure, color='yellow',
                label='cast1_d')
        ax.plot(cast_u['cast1'].Conductivity, cast_u['cast1'].Pressure, '--', color='yellow',
                label='cast1_u')
        ax.invert_yaxis()
        ax.xaxis.set_label_position('top')
        ax.xaxis.set_ticks_position('top')
        ax.set_xlabel('Conductivity (S/cm)')
        ax.set_ylabel('Pressure (decibar)')
        ax.set_title('Pre-Processing', fontsize=5)
        ax.legend()
        plt.tight_layout()
        plt.savefig(dest_dir + 'Pre_Cast1_C')

        # Oxygen
        for var in vars_available:
            if var == 'Oxygen':
                fig, ax = plt.subplots()
                ax.plot(cast_d['cast1'].Oxygen, cast_d['cast1'].Pressure, color='black',
                        label='cast1_d')
                ax.plot(cast_u['cast1'].Oxygen, cast_u['cast1'].Pressure, '--', color='black',
                        label='cast1_u')
                ax.invert_yaxis()
                ax.xaxis.set_label_position('top')
                ax.xaxis.set_ticks_position('top')
                ax.set_xlabel('Oxygen Saturation (%)')  # Check unit here
                ax.set_ylabel('Pressure (decibar)')
                ax.set_title('Pre-Processing', fontsize=5)
                ax.legend()
                plt.tight_layout()
                plt.savefig(dest_dir + 'Pre_Cast1_O')

            elif var == 'Fluorescence':
                fig, ax = plt.subplots()
                ax.plot(cast_d['cast1'].Fluorescence, cast_d['cast1'].Pressure,
                        color='green', label='cast1_d')
                ax.plot(cast_u['cast1'].Fluorescence, cast_u['cast1'].Pressure, '--',
                        color='green', label='cast1_u')
                ax.invert_yaxis()
                ax.xaxis.set_label_position('top')
                ax.xaxis.set_ticks_position('top')
                ax.set_xlabel('Fluorescence (ug/L)')  # Check unit here
                ax.set_ylabel('Pressure (decibar)')
                ax.set_title('Pre-Processing', fontsize=5)
                ax.legend()
                plt.tight_layout()
                plt.savefig(dest_dir + 'Pre_Cast1_F')

        fig, ax = plt.subplots()
        ax.plot(cast_d['cast1'].Salinity, cast_d['cast1'].Temperature, color='red',
                label='cast1_d')
        ax.plot(cast_u['cast1'].Salinity, cast_u['cast1'].Temperature, '--', color='blue',
                label='cast1_u')
        ax.set_xlabel('Salinity')
        ax.set_ylabel('Temperature (C)')
        ax.set_title('Pre-Processing T-S Plot')
        ax.legend()
        plt.tight_layout()
        plt.savefig(dest_dir + 'Pre_Cast1_T-S.png')

        number_of_colors = len(cast)
        color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                 for i in range(number_of_colors)]

    # pressure check

    fig, ax = plt.subplots()
    for i in range(len(cast)):
        ax.plot(cast_d['cast' + str(i + 1)].Conductivity[0:20],
                cast_d['cast' + str(i + 1)].Pressure[0:20],
                color='goldenrod', label='cast' + str(i + 1))
        ax.plot(cast_u['cast' + str(i + 1)].Conductivity[-20:-1],
                cast_u['cast' + str(i + 1)].Pressure[-20:-1],
                color='goldenrod', label='cast' + str(i + 1))
    # ax.plot(cast_d['cast1'].Conductivity[0:10], cast_d['cast1'].Pressure[0:10],
    #         color='blue', label='cast1')
    # ax.plot(cast_d['cast2'].Conductivity[0:10], cast_d['cast2'].Pressure[0:10],
    #         color='red', label='cast2')
    format_profile_plot(ax, 'Conductivity', 'mS/cm',
                        plot_title='Checking need for Pressure correction')
    plt.savefig(os.path.join(figure_dir, 'PC_need_CvP.png'))
    plt.close(fig)

    fig, ax = plt.subplots()
    for i in range(len(cast)):
        ax.plot(cast_d['cast' + str(i + 1)].Conductivity[0:20],
                cast_d['cast' + str(i + 1)].Depth[0:20], color='goldenrod',
                label='cast' + str(i + 1))
        ax.plot(cast_u['cast' + str(i + 1)].Conductivity[-20:-1],
                cast_u['cast' + str(i + 1)].Depth[-20:-1],
                color='goldenrod', label='cast' + str(i + 1))
    # ax.plot(cast_d['cast1'].Conductivity[0:10], cast_d['cast1'].Depth[0:10],
    #         color='blue', label='cast1')
    # ax.plot(cast_d['cast2'].Conductivity[0:10], cast_d['cast2'].Depth[0:10],
    #         color='red', label='cast2')
    ax.invert_yaxis()
    ax.xaxis.set_label_position('top')
    ax.xaxis.set_ticks_position('top')
    ax.set_xlabel('Conductivity (mS/cm)')
    ax.set_ylabel('Depth (m)')
    ax.set_title('Checking need for Pressure correction')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'PC_need_CvD.png'))
    plt.close(fig)
    return


def CORRECT_HOLD(dest_dir: str, year: str, cruise_number: str, metadata_dict: dict):
    """
    Read 6linehdr.csv and correct for zero order holds.  Look for repeat values in
    Pressure and replace with NaN, then
    look for repeats in the other sensors at the same place and replace
    with NaN..

    Adapted from RSKtools function RSKcorrecthold: 'This function identifies zero-hold
    points by looking
    for where consecutive differences for each channel are equal to zero, and replaces
    them with Nan or an
    interpolated value."  This function uses Nan. SH

    Output a new csv with the corrected values.
    """
    input_name = str(year) + "-" + str(cruise_number) + '_CTD_DATA-6linehdr.csv'
    output_name = str(year) + "-" + str(cruise_number) + '_CTD_DATA-6linehdr_corr_hold.csv'
    input_filename = dest_dir + input_name
    ctd_data = pd.read_csv(input_filename, header=None, low_memory=False)
    ctd_data = ctd_data.rename(columns=ctd_data.iloc[1])  # assign the second row as column names
    ctd_data = ctd_data.rename(
        columns={'Oxygen:Dissolved:Saturation': 'Oxygen', 'Salinity:CTD': 'Salinity',
                 'TIME:UTC': 'TIME'})
    header = ctd_data.iloc[0:6]  # keep the header to use at the end
    ctd = ctd_data.iloc[6:]
    ctd = ctd.copy()
    vars = list(dict.fromkeys(ctd))
    # print(vars)
    # cols = ctd.columns[0:-4]
    # ctd[cols] = ctd[cols].apply(pd.to_numeric, errors='coerce', axis=1)
    ctd.index = np.arange(0, len(ctd))
    pressure = ctd['Pressure'].apply(pd.to_numeric)
    pressure_lag = pressure[1:]
    pressure_lag.index = np.arange(0, len(pressure_lag))
    air = ctd['Pressure_Air'].apply(pd.to_numeric)
    air_lag = air[1:]
    air_lag.index = np.arange(0, len(air_lag))
    conductivity = ctd['Conductivity'].apply(pd.to_numeric)
    conductivity_lag = conductivity[1:]
    conductivity_lag.index = np.arange(0, len(conductivity_lag))
    temperature = ctd['Temperature'].apply(pd.to_numeric)

    temperature_lag = temperature[1:]
    temperature_lag.index = np.arange(0, len(temperature_lag))
    for var in vars:
        if var == 'Fluorescence':
            fluorescence = ctd['Fluorescence'].apply(pd.to_numeric)
            fluorescence_lag = fluorescence[1:]
            fluorescence_lag.index = np.arange(0, len(fluorescence_lag))
        elif var == 'Oxygen':
            oxygen = ctd['Oxygen'].apply(pd.to_numeric)
            oxygen_lag = oxygen[1:]
            oxygen_lag.index = np.arange(0, len(oxygen_lag))
    depth = ctd['Depth'].apply(pd.to_numeric)
    depth_lag = depth[1:]
    depth_lag.index = np.arange(0, len(depth_lag))
    salinity = ctd['Salinity'].apply(pd.to_numeric)
    salinity_lag = salinity[1:]
    salinity_lag.index = np.arange(0, len(salinity_lag))

    for i in range(0, len(ctd) - 1, 1):
        if pressure[i] == pressure_lag[i]:
            # pressure.iloc[i + 1] = np.nan
            if conductivity[i] == conductivity_lag[i]:
                conductivity.iloc[i + 1] = np.nan
            if air[i] == air_lag[i]:
                air.iloc[i + 1] = np.nan
            if temperature[i] == temperature_lag[i]:
                temperature.iloc[i + 1] = np.nan
            for var in vars:
                if var == 'Fluorescence':
                    if fluorescence[i] == fluorescence_lag[i]:
                        fluorescence.iloc[i + 1] = np.nan
                elif var == 'Oxygen':
                    if oxygen[i] == oxygen_lag[i]:
                        oxygen.iloc[i + 1] = np.nan
            # if depth[i] == depth_lag[i]:
            # depth.iloc[i + 1] = np.nan
            if salinity[i] == salinity_lag[i]:
                salinity.iloc[i + 1] = np.nan

    # ctd['Pressure'] = pressure  # this worked when pressure was set to NaN
    ctd['Conductivity'] = conductivity
    ctd['Temperature'] = temperature
    ctd['Pressure_Air'] = air
    for var in vars:
        if var == 'Fluorescence':
            ctd['Fluorescence'] = fluorescence
        elif var == 'Oxygen':
            ctd['Oxygen'] = oxygen
    # ctd['Depth'] = depth
    ctd['Salinity'] = salinity

    # drop the NaNs before they get into the CSV for IOS Shell Processing
    ctd.dropna(axis=0, subset=['Conductivity', 'Temperature', 'Pressure_Air', 'Salinity'],
               how='all', inplace=True)  # 'Pressure', 'Depth',  used to be in this list  #sometimes 'any' is required
    # ctd = ctd.reset_index(drop=True)

    metadata_dict['Processing_history'] = '-Zero-Order Holds Correction:|' \
                                          ' Correction type = Substitute with Nan' \
                                          ' Corrections applied:|' \
                                          ' All channels corrected where zero-order holds concur with Pressure Holds:|'
    metadata_dict['ZEROORDER_Time'] = datetime.now()

    # TODO: Improve metadata_dict entry here? Ask Lu

    columns = ctd.columns.tolist()

    # ctd = ctd.rename(columns={'Oxygen': 'Oxygen:Dissolved:Saturation', 'Salinity': 'Salinity:CTD',
    #                           'TIME': 'TIME:UTC'})
    column_names = dict.fromkeys(ctd.columns, '')  # set empty column names
    ctd = ctd.rename(columns=column_names)  # remove column names

    column_names_header = dict.fromkeys(header.columns, '')  # set empty column names
    header = header.rename(columns=column_names_header)
    # print(header)
    # print(ctd)

    ctd_header = header.append(ctd)
    ctd_header.to_csv(dest_dir + output_name, index=False, header=False)
    return


def CALIB(var: dict, var_downcast: dict, var_upcast: dict, metadata_dict: dict,
          zoh: bool, pd_correction_value=0):
    """
     Correct pressure and depth data
     Inputs:
         - cast, downcast, upcast and metadata dictionaries
         - correction_value: for pressure and depth data
         - zoh: if "no", then zero-order hold correction was not applied, else "yes"
     Outputs:
         - cast, downcast, upcast and metadata dictionaries after pressure correction
     """
    n = len(var.keys())
    var1 = deepcopy(var)
    var2 = deepcopy(var_downcast)
    var3 = deepcopy(var_upcast)

    for i in range(1, n + 1, 1):
        var1['cast' + str(i)].Pressure = var1['cast' + str(i)].Pressure + pd_correction_value
        var1['cast' + str(i)].Depth = var1['cast' + str(i)].Depth + pd_correction_value
        var2['cast' + str(i)].Pressure = var2['cast' + str(i)].Pressure + pd_correction_value
        var2['cast' + str(i)].Depth = var2['cast' + str(i)].Depth + pd_correction_value
        var3['cast' + str(i)].Pressure = var3['cast' + str(i)].Pressure + pd_correction_value
        var3['cast' + str(i)].Depth = var3['cast' + str(i)].Depth + pd_correction_value

    # check if a correction was done - need to see if this is the first addition of "processing history'
    if not zoh:
        metadata_dict['Processing_history'] = ''

    metadata_dict['Processing_history'] += '-CALIB parameters:|' \
                                           ' Calibration type = Correct|' \
                                           ' Calibrations applied:|' \
                                           ' Pressure (decibar) = {}|'.format(str(pd_correction_value)) + \
                                           ' Depth (meters) = {}'.format(str(pd_correction_value)) + '|'

    metadata_dict['CALIB_Time'] = datetime.now()

    return var1, var2, var3


# ------------------------------  Step 8: Data Despiking  ----------------------------------
# plot profiles to look for spikes


# ------------------------------  Step 9: Clip   -------------------------------------------

def CLIP_CAST(var: dict, metadata_dict: dict, limit_pressure_change: float,
              cast_direction: str) -> dict:
    """
    CLIP the unstable measurement from sea surface and bottom on the downcast OR upcast
     Inputs:
         - Upcast, metadata dictionary,
         - limit_pressure_change: limit drop for downcast, limit rise for upcast
     Outputs:
         - Upcast after removing records near surface and bottom
    direction: 'down' or 'up'
    """
    var_clip = deepcopy(var)
    for i in range(1, len(var_clip) + 1):
        pressure = var_clip['cast' + str(i)].Pressure
        diff = var_clip['cast' + str(i)].Pressure.diff()
        index_start = pressure.index[0]
        # index_end = pressure.index[-1]
        if cast_direction == 'down':
            limit_drop = limit_pressure_change
            diff_mask = diff > limit_drop
        elif cast_direction == 'up':
            limit_rise = limit_pressure_change
            diff_mask = diff < limit_rise
        else:
            print(f'cast_direction {cast_direction} is invalid. Ending program')
            return
        diff_rise = diff.loc[diff_mask]
        for j in range(len(diff.loc[diff_mask])):
            index_1 = diff_rise.index[j]
            if (diff_rise.index[j + 1] == index_1 + 1) and (diff_rise.index[j + 2] == index_1 + 2) and (
                    diff_rise.index[j + 3] == index_1 + 3) and (diff_rise.index[j + 4] == index_1 + 4) and (
                    diff_rise.index[j + 5] == index_1 + 5) and (diff_rise.index[j + 6] == index_1 + 6) and (
                    diff_rise.index[j + 7] == index_1 + 7) and (diff_rise.index[j + 8] == index_1 + 8):
                index_end_1 = index_1 - 1
                break
        cut_start = index_end_1 - index_start

        for j in range(-1, -len(diff.loc[diff_mask]), -1):
            index_2 = diff_rise.index[j]
            if (diff_rise.index[j - 1] == index_2 - 1) and (diff_rise.index[j - 2] == index_2 - 2) and (
                    diff_rise.index[j - 3] == index_2 - 3) and (diff_rise.index[j - 4] == index_2 - 4) and (
                    diff_rise.index[j - 5] == index_2 - 5):
                index_end_2 = index_2 + 1
                break
        cut_end = index_end_2 - index_start
        var_clip['cast' + str(i)] = var_clip['cast' + str(i)][cut_start:cut_end]

        metadata_dict['Processing_history'] += '-CLIP_{}cast{}'.format(
            cast_direction, str(i)) + ': First Record = {}'.format(
            str(cut_start)) + ', Last Record = {}'.format(str(cut_end)) + '|'
        metadata_dict['CLIP_{}_Time{}'.format(cast_direction[0].upper(), str(i))] = datetime.now()
    return var_clip


# def CLIP_DOWNCAST(var: dict, metadata_dict: dict, limit_drop: float) -> dict:
#     """
#      CLIP the unstable measurement from sea surface and bottom
#      Inputs:
#          - Downcast, metadata dictionary, limit_drop,
#      Outputs:
#          - Downcast after removing records near surface and bottom
#      """
#     var_clip = deepcopy(var)
#     for i in range(1, len(var_clip) + 1):
#         pressure = var_clip['cast' + str(i)].Pressure
#         # print(pressure.shape)
#         diff = var_clip['cast' + str(i)].Pressure.diff()  # First difference
#         index_start = pressure.index[0]
#         diff_drop = diff.loc[(diff > limit_drop)]
#         for j in range(len(diff.loc[(diff > limit_drop)])):
#             index_1 = diff_drop.index[j]
#             if (diff_drop.index[j + 1] == index_1 + 1) and (diff_drop.index[j + 2] == index_1 + 2) and (
#                     diff_drop.index[j + 3] == index_1 + 3) and (diff_drop.index[j + 4] == index_1 + 4) and (
#                     diff_drop.index[j + 5] == index_1 + 5) and (diff_drop.index[j + 6] == index_1 + 6) and (
#                     diff_drop.index[j + 7] == index_1 + 7) and (diff_drop.index[j + 8] == index_1 + 8):
#                 index_end_1 = index_1 - 1
#                 break
#         cut_start = index_end_1 - index_start
#
#         for j in range(-1, -len(diff.loc[(diff > limit_drop)]), -1):
#             index_2 = diff_drop.index[j]
#             if (diff_drop.index[j - 1] == index_2 - 1) and (diff_drop.index[j - 2] == index_2 - 2) and (
#                     diff_drop.index[j - 3] == index_2 - 3) and (diff_drop.index[j - 4] == index_2 - 4) and (
#                     diff_drop.index[j - 5] == index_2 - 5):
#                 index_end_2 = index_2 + 1
#                 break
#         cut_end = index_end_2 - index_start
#         # list_start.append(cut_start)
#         # list_end.append(cut_end)
#         var_clip['cast' + str(i)] = var_clip['cast' + str(i)][cut_start:cut_end]
#         metadata_dict['Processing_history'] += '-CLIP_downcast{}'.format(
#             str(i)) + ': First Record = {}'.format(str(cut_start)) + ', Last Record = {}'.format(
#             str(cut_end)) + '|'
#         metadata_dict['CLIP_D_Time' + str(i)] = datetime.now()
#
#     return var_clip


# def CLIP_UPCAST(var, metadata_dict: dict, limit_rise):
#     """
#      CLIP the unstable measurement from sea surface and bottom
#      Inputs:
#          - Upcast, metadata dictionary, limit_rise,
#      Outputs:
#          - Upcast after removing records near surface and bottom
#      """
#     var_clip = deepcopy(var)
#     for i in range(1, len(var_clip) + 1):
#         pressure = var_clip['cast' + str(i)].Pressure
#         diff = var_clip['cast' + str(i)].Pressure.diff()
#         index_start = pressure.index[0]
#         # index_end = pressure.index[-1]
#         diff_rise = diff.loc[(diff < limit_rise)]
#         for j in range(len(diff.loc[(diff < limit_rise)])):
#             index_1 = diff_rise.index[j]
#             if (diff_rise.index[j + 1] == index_1 + 1) and (diff_rise.index[j + 2] == index_1 + 2) and (
#                     diff_rise.index[j + 3] == index_1 + 3) and (diff_rise.index[j + 4] == index_1 + 4) and (
#                     diff_rise.index[j + 5] == index_1 + 5) and (diff_rise.index[j + 6] == index_1 + 6) and (
#                     diff_rise.index[j + 7] == index_1 + 7) and (diff_rise.index[j + 8] == index_1 + 8):
#                 index_end_1 = index_1 - 1
#                 break
#         cut_start = index_end_1 - index_start
#
#         for j in range(-1, -len(diff.loc[(diff < limit_rise)]), -1):
#             index_2 = diff_rise.index[j]
#             if (diff_rise.index[j - 1] == index_2 - 1) and (diff_rise.index[j - 2] == index_2 - 2) and (
#                     diff_rise.index[j - 3] == index_2 - 3) and (diff_rise.index[j - 4] == index_2 - 4) and (
#                     diff_rise.index[j - 5] == index_2 - 5):
#                 index_end_2 = index_2 + 1
#                 break
#         cut_end = index_end_2 - index_start
#         var_clip['cast' + str(i)] = var_clip['cast' + str(i)][cut_start:cut_end]
#         metadata_dict['Processing_history'] += '-CLIP_upcast{}'.format(str(i)) + ': First Record = {}'.format(
#             str(cut_start)) + ', Last Record = {}'.format(str(cut_end)) + '|'
#         metadata_dict['CLIP_U_Time' + str(i)] = datetime.now()
#     return var_clip


# run both functions
# cast_d_clip = CLIP_DOWNCAST(cast_d_pc, metadata, limit_drop = 0.02)
# cast_u_clip = CLIP_UPCAST(cast_u_pc, metadata, limit_rise = -0.02)


# Plot to check the profiles after clip by cast
def plot_clip(cast: dict, cast_d_clip: dict, cast_d_pc: dict, dest_dir):
    """ plot the clipped casts to make sure they are OK"""

    # Create a folder for figures if it doesn't already exist
    figure_dir = os.path.join(dest_dir, 'FIG')
    if not os.path.exists(figure_dir):
        os.makedirs(figure_dir)

    num_casts = len(cast)

    fig, ax = plt.subplots()
    for i in range(1, num_casts + 1):
        ax.plot(cast_d_pc[f'cast{i}'].TIME, cast_d_pc[f'cast{i}'].Pressure,
                color='blue')
    format_profile_plot(ax, var_name='Time', var_units=None, plot_title='Before Clip')
    plt.savefig(os.path.join(figure_dir, 'Before_Clip_P_vs_t.png'))
    plt.close(fig)

    fig, ax = plt.subplots()
    for i in range(1, num_casts + 1):
        ax.plot(cast_d_clip[f'cast{i}'].TIME, cast_d_clip[f'cast{i}'].Pressure,
                color='blue')
    format_profile_plot(ax, var_name='Time', var_units=None, plot_title='After Clip')
    plt.savefig(os.path.join(figure_dir, 'After_Clip_P_vs_t.png'))
    plt.close(fig)

    # # plot all cast together
    #
    # number_of_colors = len(cast)
    # color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
    #          for i in range(number_of_colors)]
    #
    # fig, ax = plt.subplots()
    # for i in range(0, len(cast), 1):
    #     ax.plot(cast_d_clip['cast' + str(i + 1)].TIME,
    #             cast_d_clip['cast' + str(i + 1)].Pressure, color=color[i],
    #             label='cast' + str(i + 1))
    #     # ax.plot(cast_u['cast' + str(i+1)].Salinity, cast_u['cast' + str(i+1)].Pressure, '--', color=color[i],
    #     #         label= 'cast' + str(i+1))
    # # ax.plot(cast_d['cast1'].Salinity, cast_d['cast1'].Pressure, color='blue', label='cast1')
    # # ax.plot(cast_u['cast1'].Salinity, cast_u['cast1'].Pressure, '--', color='blue', label='cast1')
    # ax.invert_yaxis()
    # ax.xaxis.set_label_position('top')
    # ax.xaxis.set_ticks_position('top')
    # ax.set_xlabel('Time')
    # ax.set_ylabel('Pressure (decibar)')
    # ax.set_title('After Clip')
    # ax.legend()
    return


# ------------------------------  Step 10: Filter  ---------------------------------------
# apply a moving average FIR filter (a simple low pass )

# def filter(x, n):# n -  filter size, 9 suggest by RBR manual, choose the smallest one which can do the job
#    b = (np.ones(n))/n #numerator co-effs of filter transfer function
#    #b = repeat(1.0/n, n)
#    a = np.ones(1)  #denominator co-effs of filter transfer function
#    #y = signal.convolve(x,b) #filter output using convolution
#    #y = signal.lfilter(b, a, x) #filter output using lfilter function
#    y = signal.filtfilt(b, a, x)  # Apply a digital filter forward and backward to a signal.
#    return y

def FILTER(var_downcast: dict, var_upcast: dict, metadata_dict: dict,
           have_fluor: bool, window_width=6, sample_rate: int = 8,
           time_constant: float = 1 / 8, filter_type: int = 1):
    """
     Filter the profile data using a low pass filter: moving average
     Inputs:
         - downcast and upcast data dictionaries
         - window_width:
         - sample_rate:
         - time_constant:
         - filter_type: 0 or 1, corresponding to FIR or Moving Average filter
     Outputs:
         - two dictionaries containing downcast and upcast profiles after applying filter
     """

    cast_number = len(var_downcast.keys())
    if filter_type == 0:
        Wn = (1.0 / time_constant) / (sample_rate * 2)
        # Numerator (b) and denominator (a) polynomials of the IIR filter
        b, a = signal.butter(2, Wn, "low")
        filter_name = "FIR"
    elif filter_type == 1:
        b = (np.ones(window_width)) / window_width  # numerator co-effs of filter transfer function
        a = np.ones(1)  # denominator co-effs of filter transfer function
        filter_name = "Moving average filter"
    else:
        print('Invalid filter type:', filter_type)
        return

    var1 = deepcopy(var_downcast)
    var2 = deepcopy(var_upcast)

    for i in range(1, cast_number + 1):
        var1['cast' + str(i)].Temperature = signal.filtfilt(
            b, a, var1['cast' + str(i)].Temperature)
        var1['cast' + str(i)].Conductivity = signal.filtfilt(
            b, a, var1['cast' + str(i)].Conductivity)
        var1['cast' + str(i)].Pressure = signal.filtfilt(
            b, a, var1['cast' + str(i)].Pressure)
        var2['cast' + str(i)].Temperature = signal.filtfilt(
            b, a, var2['cast' + str(i)].Temperature)
        var2['cast' + str(i)].Conductivity = signal.filtfilt(
            b, a, var2['cast' + str(i)].Conductivity)
        var2['cast' + str(i)].Pressure = signal.filtfilt(
            b, a, var2['cast' + str(i)].Pressure)
        if have_fluor:
            var1['cast' + str(i)].Fluorescence = signal.filtfilt(
                b, a, var1['cast' + str(i)].Fluorescence)
            var2['cast' + str(i)].Fluorescence = signal.filtfilt(
                  b, a, var2['cast' + str(i)].Fluorescence)

    metadata_dict['Processing_history'] += '-FILTER parameters:|' \
                                           ' ' + filter_name + ' was used.|' \
                                           ' Filter width = {}'.format(str(window_width)) + '.|' \
                                           ' The following channel(s) were filtered.|' \
                                           ' Pressure|' \
                                           ' Temperature|' \
                                           ' Conductivity|'
    if have_fluor:
        metadata_dict['Processing_history'] += ' Fluorescence|'

    metadata_dict['FILTER_Time'] = datetime.now()

    return var1, var2


# plot to check values before and after filtering
def plot_filter(cast_d_filtered: dict, cast_d_clip: dict, dest_dir, have_fluor: bool):
    """ check the filter plots"""

    # Create a folder for figures if it doesn't already exist
    figure_dir = os.path.join(dest_dir, 'FIG')
    if not os.path.exists(figure_dir):
        os.makedirs(figure_dir)

    vars_available = list(dict.fromkeys(cast_d_filtered['cast1']))
    n_casts = len(cast_d_filtered)

    for j, var in enumerate(VARIABLES_POSSIBLE):
        if var in vars_available:
            fig, ax = plt.subplots()
            for i in range(n_casts):
                ax.plot(cast_d_clip[f'cast{i + 1}'].loc[:, var],
                        cast_d_clip[f'cast{i + 1}'].Pressure,
                        color='blue', label='Pre-filtering')
                ax.plot(cast_d_filtered[f'cast{i + 1}'].loc[:, var],
                        cast_d_filtered[f'cast{i + 1}'].Pressure,
                        '--', color='red', label='Post-filtering')
                format_profile_plot(ax, var, VARIABLE_COLOURS[j], 'Post-Filter')
                plt.savefig(os.path.join(figure_dir, f'Post_Filter_{var[0]}.png'))
                plt.close(fig)

    return


# ------------------ Step 11: Shift conductivity and recalculate salinity ----------------------
# input variable: cast_d_filtered, cast_u_filtered, try 2-3s (12-18 scans)

def SHIFT_CONDUCTIVITY(var_downcast: dict, var_upcast: dict,
                       metadata_dict: dict, shifted_scan_number=2):
    """
     Delay the conductivity signal, and recalculate salinity
     Inputs:
         - downcast and upcast data dictionaries, metadata dictionary
         - shifted_scan_number: number of scans shifted. +: delay; -: advance
     Outputs:
         - two dictionaries containing downcast and upcast profiles
     """
    cast_number = len(var_downcast.keys())
    var1 = deepcopy(var_downcast)
    var2 = deepcopy(var_upcast)
    # Apply the shift to each cast
    for i in range(1, cast_number + 1):
        index_1 = var1['cast' + str(i)].Conductivity.index[0]
        v1 = var1['cast' + str(i)].Conductivity[index_1]
        index_2 = var2['cast' + str(i)].Conductivity.index[0]
        v2 = var2['cast' + str(i)].Conductivity[index_2]
        # shift C for n scans
        var1['cast' + str(i)].Conductivity = var1['cast' + str(i)].Conductivity.shift(
            periods=shifted_scan_number, fill_value=v1)
        # calculates SP from C using the PSS-78 algorithm (2 < SP < 42)
        var1['cast' + str(i)].Salinity = gsw.SP_from_C(var1['cast' + str(i)].Conductivity,
                                                       var1['cast' + str(i)].Temperature,
                                                       var1['cast' + str(i)].Pressure)
        var2['cast' + str(i)].Conductivity = var2['cast' + str(i)].Conductivity.shift(
            periods=shifted_scan_number, fill_value=v2)
        var2['cast' + str(i)].Salinity = gsw.SP_from_C(var2['cast' + str(i)].Conductivity,
                                                       var2['cast' + str(i)].Temperature,
                                                       var2['cast' + str(i)].Pressure)

    metadata_dict['Processing_history'] += '-SHIFT parameters:|' \
                                           ' Shift Channel: Conductivity|' \
                                           ' # of Records to Delay (-ve for Advance):|' \
                                           ' Shift = {}'.format(str(shifted_scan_number)) + '|' \
                                                                                            ' Salinity was recalculated after shift|'
    metadata_dict['SHIFT_Conductivity_Time'] = datetime.now()

    return var1, var2


# cast_d_shift_c, cast_u_shift_c = SHIFT_CONDUCTIVITY(
#   cast_d_filtered, cast_u_filtered, shifted_scan_number = 2, metadata_dict = metadata)
# delay conductivity data by 2 scans

# Plot Salinity and T-S to check the index after shift

def plot_shift_c(cast_d_shift_c: dict, cast_d_filtered: dict, dest_dir):
    """
    inputs:
        - cast_d_shift_c
        - cast_d_filtered
    """

    # Create a folder for figures if it doesn't already exist
    figure_dir = os.path.join(dest_dir, 'FIG')
    if not os.path.exists(figure_dir):
        os.makedirs(figure_dir)

    num_casts = len(cast_d_filtered)

    fig, ax = plt.subplots()  # Before
    for i in range(1, num_casts + 1):
        ax.plot(cast_d_filtered[f'cast{i}'].Salinity,
                cast_d_filtered[f'cast{i}'].Pressure, color='blue')
        # ax.plot(cast_u_filtered['cast1'].Salinity, cast_u_filtered['cast1'].Pressure,
        #         '--', color='blue', label='Pre-shift')
    format_profile_plot(ax, 'Salinity', 'PSS-78', 'Before Shift Conductivity')
    plt.savefig(os.path.join(figure_dir, 'Before_Shift_Conductivity_S.png'))
    plt.close(fig)

    fig, ax = plt.subplots()  # After
    for i in range(1, num_casts + 1):
        ax.plot(cast_d_shift_c[f'cast{i}'].Salinity,
                cast_d_shift_c[f'cast{i}'].Pressure, color='blue')
        # ax.plot(cast_u_shift_c['cast1'].Salinity, cast_u_shift_c['cast1'].Pressure,
        #         '--', color='red', label='Post-shift')
    format_profile_plot(ax, 'Salinity', 'PSS-78', 'After Shift Conductivity')
    plt.savefig(os.path.join(figure_dir, 'After_Shift_Conductivity_S.png'))
    plt.close(fig)

    # TS Plot
    fig, ax = plt.subplots()
    for i in range(1, num_casts + 1):
        ax.plot(cast_d_filtered['cast1'].Salinity,
                cast_d_filtered['cast1'].Temperature, color='blue')
        # ax.plot(cast_u_filtered['cast1'].Salinity, cast_u_filtered['cast1'].Temperature,
        #         '--', color='blue',
        # label='Pre-shift')
    ax.set_xlabel('Salinity')
    ax.set_ylabel('Temperature (C)')
    ax.set_title('Before Shift Conductivity T-S Plot')
    # ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'Before_Shift_Conductivity_T-S.png'))
    plt.close(fig)

    fig, ax = plt.subplots()
    for i in range(1, num_casts + 1):
        ax.plot(cast_d_shift_c['cast1'].Salinity,
                cast_d_shift_c['cast1'].Temperature, color='blue')
        # ax.plot(cast_u_shift_c['cast1'].Salinity, cast_u_shift_c['cast1'].Temperature,
        #         '--', color='red',
        # label='Post-shift')
    ax.set_xlabel('Salinity')
    ax.set_ylabel('Temperature (C)')
    ax.set_title('After Shift Conductivity T-S Plot')
    # ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'After_Shift_Conductivity_T-S.png'))
    plt.close(fig)

    return


# ------------------------------    Step 12: Shift Oxygen   ----------------------------------
# input variable: cast_d_filtered, cast_u_filtered, try 2-3s (12-18 scans for 6Hz)

def SHIFT_OXYGEN(var_downcast: dict, var_upcast: dict,
                 metadata_dict: dict, shifted_scan_number=-11):
    """
     Advance oxygen data by 2-3s
     Inputs:
         - downcast and upcast data dictionaries, metadata dictionary
         - - shifted_scan_number: number of scans shifted. +: delay; -: advance
     Outputs:
         - two dictionaries containing downcast and upcast profiles
     """
    cast_number = len(var_downcast.keys())
    var1 = deepcopy(var_downcast)
    var2 = deepcopy(var_upcast)
    for i in range(1, cast_number + 1, 1):
        index_1 = var1['cast' + str(i)].Oxygen.index[-1]
        v1 = var1['cast' + str(i)].Oxygen[index_1]
        index_2 = var2['cast' + str(i)].Oxygen.index[-1]
        v2 = var2['cast' + str(i)].Oxygen[index_2]
        # shift C for n scans
        var1['cast' + str(i)].Oxygen = var1['cast' + str(i)].Oxygen.shift(
            periods=shifted_scan_number, fill_value=v1)
        var2['cast' + str(i)].Oxygen = var2['cast' + str(i)].Oxygen.shift(
            periods=shifted_scan_number, fill_value=v2)

    metadata_dict['Processing_history'] += '-SHIFT parameters:|' \
                                           ' Shift Channel: Oxygen:Dissolved:Saturation|' \
                                           ' # of Records to Delay (-ve for Advance):|' \
                                           ' Shift = {}'.format(str(shifted_scan_number)) + '|'
    metadata_dict['SHIFT_Oxygen_Time'] = datetime.now()

    return var1, var2


def plot_shift_o(cast_d_shift_o, cast_d_shift_c, dest_dir):
    """Check Oxy plots after shift """

    # Create a folder for figures if it doesn't already exist
    figure_dir = os.path.join(dest_dir, 'FIG')
    if not os.path.exists(figure_dir):
        os.makedirs(figure_dir)

    # todo plot all casts
    fig, ax = plt.subplots()
    ax.plot(cast_d_shift_c['cast1'].Temperature, cast_d_shift_c['cast1'].Oxygen,
            color='blue', label='Pre-shift')
    # ax.plot(cast_u_shift_c['cast2'].Temperature, cast_u_shift_c['cast2'].Oxygen,
    #         '--', color='blue', label='Pre-shift')
    ax.plot(cast_d_shift_o['cast1'].Temperature, cast_d_shift_o['cast1'].Oxygen,
            color='red', label='Post-shift')
    # ax.plot(cast_u_shift_o['cast2'].Temperature, cast_u_shift_o['cast2'].Oxygen,
    #         '--', color='red', label='Post-shift')
    ax.set_ylabel('Oxygen Saturation (%)')
    ax.set_xlabel('Temperature (C)')
    ax.set_title('After Shift Oxygen T-O Plot')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'After_Shift_Oxygen_T-O.png'))
    return


# ------------------------------ Add oxygen ml/l derivation ----------------------------------


def DERIVE_OXYGEN_CONCENTRATION(var_downcast: dict, var_upcast: dict,
                                metadata_dict: dict):
    """
    Derive oxygen concentration in umol/kg and mL/L from oxygen percent saturation.
    inputs:
        - var_downcast, var_upcast
        - metadata_dict
    outputs:
        - var1, var2
    """
    umol_L_to_mL_L = 1 / 44.6596
    cast_number = len(var_downcast.keys())
    var1 = deepcopy(var_downcast)
    var2 = deepcopy(var_upcast)

    # O_sat_num_decimal_places = None

    for i in range(1, cast_number + 1, 1):
        for var in [var1, var2]:
            T = var['cast' + str(i)].Temperature.to_numpy()
            S = var['cast' + str(i)].Salinity.to_numpy()
            O_sat = var['cast' + str(i)].Oxygen.to_numpy()
            P = var['cast' + str(i)].Pressure.to_numpy()

            # Convert oxygen saturation to molar oxygen concentration
            # Use default P=0dbar and p_atm=1013.25 mbar, where
            # P: hydrostatic pressure in dbar, and
            # p_atm: atmospheric (air) pressure in mbar
            O_umol_L = O2stoO2c(O_sat, T, S)
            # Convert to mL/L
            O_mL_L = O_umol_L * umol_L_to_mL_L
            # todo Convert to umol/kg using potential density of seawater (kg/L) from
            # Fofonoff and Millard (1983) and Millero et al. (1980).
            # rho: potential density of seawater referenced to a hydrostatic pressure
            # of 0 dbar and using practical salinity.
            # Since TEOS-10 is based off ABSOLUTE salinity, it can't be used here!
            # One option is seawater.eos80.pden() potential density
            rho = eos80.pden(S, T, P)
            O_umol_kg = O_umol_L / rho
            var['cast' + str(i)]['Oxygen_mL_L'] = O_mL_L
            var['cast' + str(i)]['Oxygen_umol_kg'] = O_umol_kg

    metadata_dict['Processing_history'] += 'Oxygen concentration was calculated from oxygen ' \
                                           'saturation using SCOR WG 142|'
    return var1, var2


# def pH2O_Weiss_Price(T, S):
#     """
#     Compute the vapour pressure of water from temperature and salinity following
#     Weiss and Price (1980; doi:10.1016/0304-4203(80)90024-9)
#     inputs:
#         - T: temperature in degrees Celsius
#         - S: salinity (dimensionless, Practical Salinity Scale 1978)
#     outputs:
#         - pH2O: vapour pressure of water with units of atm
#     """
#     D0 = 24.4543
#     D1 = -67.4509
#     D2 = -4.8489
#     D3 = -5.44e-4
#     T_abs = T + 273.15
#     return np.exp(D0 + D1 * (100/T_abs) + D2 * np.log(T_abs/100) + D3 * S)


# def T_corr_Garcia_Gordon(T):
#     """
#     Correction term; the temperature-dependent part of seawater O2 solubility.
#     From Garcia and Gordon 1992, Benson and Krause refit
#     """
#     A0 = 2.00907
#     A1 = 3.22014
#     A2 = 4.05010
#     A3 = 4.94457
#     A4 = -2.56847e-1
#     A5 = 3.88767  # (Garcia and Gordon 1992, Benson and Krause refit)
#
#     T_s = np.log((298.15 - T) / (273.15 + T))
#
#     return 44.6596 * np.exp(A0 + A1*T_s + A2*T_s**2 + A3*T_s**3 + A4*T_s**4 + A5*T_s**5)


# def S_corr_Garcia_Gordon(T, S):
#     """
#     Correction term; the salinity-dependent part of seawater O2 solubility.
#     From Garcia and Gordon 1992, Benson and Krause refit
#     """
#     B0 = -6.24523e-3
#     B1 = -7.37614e-3
#     B2 = -1.03410e-2
#     B3 = -8.17083e-3
#     C0 = -4.88682e-7
#     S_preset = 0
#
#     T_s = np.log((298.15 - T) / (273.15 + T))
#
#     return np.exp((S - S_preset) *
#                   (B0 + B1*T_s + B2*T_s**2 + B3 * T_s**3) +
#                   C0 * (S**2 - S_preset**2))


# def DERIVE_OXYGEN_ML_L(var_downcast, var_upcast, metadata_dict):
#     """
#     Convert oxygen percent saturation to concentration with mL/L units
#     using SCOR WG 142 (DOI:10.13155/45915) equation used by ARGO program.
#     Hakai uses this reference to derive oxygen concentration.
#     Inputs:
#          - downcast and upcast data dictionaries, metadata dictionary
#     Outputs:
#          - two dictionaries containing downcast and upcast profiles
#     """
#     # test this function
#
#     umol_L_to_mL_L = 1/44.6596
#
#     cast_number = len(var_downcast.keys())
#     var1 = deepcopy(var_downcast)
#     var2 = deepcopy(var_upcast)
#
#     for i in range(1, cast_number + 1, 1):
#         for var in [var1, var2]:
#             T = var['cast' + str(i)].Temperature.values
#             S = var['cast' + str(i)].Salinity.values
#             O_sat = var['cast' + str(i)].Oxygen.values
#
#             T_corr = T_corr_Garcia_Gordon(T)
#             S_corr = S_corr_Garcia_Gordon(T, S)
#
#             cO2_star = T_corr * S_corr  # Oxygen solubility
#             cO2_umol_L = cO2_star * O_sat  # Oxygen concentration in what units?
#             cO2_mL_L = cO2_umol_L * umol_L_to_mL_L  # Convert to the desired units
#             var['cast' + str(i)]['Oxygen_concentration'] = cO2_mL_L  # Add to data dictionary
#
#     if 'Processing_history' not in metadata_dict:  # For testing purposes
#         metadata_dict['Processing_history'] = ''
#
#     metadata_dict['Processing_history'] += 'Converted Dissolved O2 % to mL/L units by using SCOR WG 142 ' \
#                                            '(DOI:10.13155/45915) saturation concentrations equation with ' \
#                                            'CTD and DO data 4.1667s smoothed|'
#     metadata_dict['DERIVE_OXYGEN_ML_L_Time'] = datetime.now()
#
#     return var1, var2


# TESTING
# test_year = '2023'
# test_cruise_num = '015'
# test_file = '208765_20230121_2113_newDOcoefficients.rsk'

# test_year = '2022'
# test_cruise_num = '025'
# test_file = '201172_20220925_1059.rsk'
#
# test_dir = 'C:\\Users\\HourstonH\\Documents\\ctd_processing\\RBR\\' \
#            'python_testing\\{}-{}\\'.format(test_year, test_cruise_num)
# test_event_start = 1
#
# rsk = pyrsktools.open(test_dir + test_file)
#
# # ValueError: Type names and field names must be valid identifiers: 'dissolvedo₂saturation_00'
# EXPORT_FILES(dest_dir=test_dir, file=test_file, year=test_year,
#              cruise_number=test_cruise_num, event_start=1)

# EXPORT_FILES(dest_dir=test_dir, file=test_file, year=test_year,
#              cruise_number=test_cruise_num, event_start=test_event_start)
#
# metadata = CREATE_META_DICT(dest_dir=test_dir,
#                             file=test_file,
#                             year=2023, cruise_number='2023-015')


# ---------------------    Step 13: Delete (swells/slow drop)  --------------------------
# correct for the wake effect, remove the pressure reversal


def DELETE_PRESSURE_REVERSAL(var_downcast, var_upcast, metadata_dict):
    """
     Detect and delete pressure reversal
     Inputs:
         - downcast and upcast data dictionaries, metadata dictionary
     Outputs:
         - two dictionaries containing downcast and upcast profiles
     """

    cast_number = len(var_downcast.keys())
    var1 = deepcopy(var_downcast)
    var2 = deepcopy(var_upcast)
    for i in range(1, cast_number + 1, 1):
        press = var1['cast' + str(i)].Pressure.values
        ref = press[0]
        inversions = np.diff(np.r_[press, press[-1]]) < 0
        mask = np.zeros_like(inversions)
        for k, p in enumerate(inversions):
            if p:
                ref = press[k]
                cut = press[k + 1:] < ref
                mask[k + 1:][cut] = True
        var1['cast' + str(i)][mask] = np.NaN

    for i in range(1, cast_number + 1, 1):
        press = var2['cast' + str(i)].Pressure.values
        ref = press[0]
        inversions = np.diff(np.r_[press, press[-1]]) > 0
        mask = np.zeros_like(inversions)
        for k, p in enumerate(inversions):
            if p:
                ref = press[k]
                cut = press[k + 1:] > ref
                mask[k + 1:][cut] = True
        var2['cast' + str(i)][mask] = np.NaN
    metadata_dict['Processing_history'] += '-DELETE_PRESSURE_REVERSAL parameters:|' \
                                           ' Remove pressure reversals|'
    metadata_dict['DELETE_PRESSURE_REVERSAL_Time'] = datetime.now()

    return var1, var2


def plot_processed(cast_d_wakeeffect: dict, cast_d_shift_o: dict, cast_d: dict,
                   cast: dict, dest_dir: str):
    """Plot the processed casts
    inputs:
        - cast_d_wakeeffect
        - cast_d_shift_o
        - cast_d
        - cast
    """
    # Create a folder for figures if it doesn't already exist
    figure_dir = os.path.join(dest_dir, 'FIG')
    if not os.path.exists(figure_dir):
        os.makedirs(figure_dir)

    vars = list(dict.fromkeys(cast['cast1']))
    fig, ax = plt.subplots()

    ax.plot(cast_d_shift_o['cast1'].Salinity, cast_d_shift_o['cast1'].Pressure, color='blue',
            label='Pre-Delete')
    # ax.plot(cast_u_filtered['cast1'].Salinity, cast_u_filtered['cast1'].Pressure, '--',
    #   color='blue', label='Pre-shift')
    ax.plot(cast_d_wakeeffect['cast1'].Salinity, cast_d_wakeeffect['cast1'].Pressure,
            color='red', label='Post-Delete')
    # ax.plot(cast_u_wakeeffect['cast1'].Salinity, cast_u_wakeeffect['cast1'].Pressure,
    #   '--', color='red', label='Post-shift')
    ax.invert_yaxis()
    ax.xaxis.set_label_position('top')
    ax.xaxis.set_ticks_position('top')
    ax.set_xlabel(' ')
    ax.set_ylabel('Pressure (decibar)')
    ax.set_title('After Delete Pressure Reversal')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'After_Delete_S.png'))

    fig, ax = plt.subplots()
    ax.plot(cast_d_shift_o['cast1'].Conductivity, cast_d_shift_o['cast1'].Pressure,
            color='blue', label='Pre-Delete')
    # ax.plot(cast_u_filtered['cast1'].Salinity, cast_u_filtered['cast1'].Pressure,
    #   '--', color='blue', label='Pre-shift')
    ax.plot(cast_d_wakeeffect['cast1'].Conductivity, cast_d_wakeeffect['cast1'].Pressure,
            color='red', label='Post-Delete')
    # ax.plot(cast_u_wakeeffect['cast1'].Salinity, cast_u_wakeeffect['cast1'].Pressure,
    #   '--', color='red', label='Post-shift')
    ax.invert_yaxis()
    ax.xaxis.set_label_position('top')
    ax.xaxis.set_ticks_position('top')
    ax.set_xlabel('Conductivity')
    ax.set_ylabel('Pressure (decibar)')
    ax.set_title('After Delete Pressure Reversal')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'After_Delete_C.png'))

    # TS Plot
    fig, ax = plt.subplots()
    ax.plot(cast_d_shift_o['cast1'].Salinity, cast_d_shift_o['cast1'].Temperature,
            color='blue', label='Pre-Delete')
    # ax.plot(cast_u_filtered['cast1'].Salinity, cast_u_filtered['cast1'].Temperature,
    #   '--', color='blue', label='Pre-shift')
    ax.plot(cast_d_wakeeffect['cast1'].Salinity, cast_d_wakeeffect['cast1'].Temperature,
            color='red', label='Post-Delete')
    # ax.plot(cast_u_wakeeffect['cast1'].Salinity, cast_u_wakeeffect['cast1'].Temperature,
    #   '--', color='red', label='Post-shift')
    ax.set_xlabel('Salinity')
    ax.set_ylabel('Temperature (C)')
    ax.set_title('T-S Plot (after delete pressure reversal)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'After_Delete_T-S.png'))

    # -------------------------  Plot processed profiles ------------------------------
    # number_of_colors = len(cast)
    # color = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
    #          for i in range(number_of_colors)]

    vars_available = list(dict.fromkeys(cast_d['cast1']))

    # Plot the first cast before and after processing
    for j, var in enumerate(VARIABLES_POSSIBLE):
        if var in vars_available:
            fig, ax = plt.subplots()
            # for i in range (0, len(cast_d), 1):
            # ax.plot(cast_d['cast' + str(i+1)].Salinity, cast_d['cast' + str(i+1)].Pressure,
            #   color=color[i], label= 'cast' + str(i+1))
            # ax.plot(cast_d_wakeeffect['cast' + str(i+1)].Salinity,
            #         cast_d_wakeeffect['cast' + str(i+1)].Pressure, '--', color=color[i],
            #         label='cast' + str(i+1))
            ax.plot(cast_d['cast1'].loc[:, var], cast_d['cast1'].Pressure, color='blue',
                    label='Pre_Processing')
            ax.plot(cast_d_wakeeffect['cast1'].loc[:, var],
                    cast_d_wakeeffect['cast1'].Pressure,
                    color='red', label='After_processing')
            format_profile_plot(ax, var, VARIABLE_UNITS[j], 'Pre and Post Processing',
                                add_legend=True)
            plt.savefig(os.path.join(figure_dir, f'Pre_Post_{var[0]}.png'))

    # T-S plot
    fig, ax = plt.subplots()
    # for i in range (0, len(cast_d), 1):
    #    #ax.plot(cast_d['cast' + str(i+1)].Salinity, cast_d['cast' + str(i+1)].Temperature,
    #    color=color[i], label= 'cast' + str(i+1))
    #    ax.plot(cast_d_wakeeffect['cast' + str(i+1)].Salinity,
    #    cast_d_wakeeffect['cast' + str(i+1)].Temperature, color=color[i],
    #    label='cast' + str(i+1))
    ax.plot(cast_d['cast1'].Salinity, cast_d['cast1'].Temperature, color='blue',
            label='Pre-Processing')
    # ax.plot(cast_d_shift_o['cast1'].Salinity, cast_d_shift_o['cast1'].Temperature,
    #         color='blue', label='Pre-shift')
    # ax.plot(cast_u_filtered['cast1'].Salinity, cast_u_filtered['cast1'].Temperature,
    #         '--', color='blue', label='Pre-shift')
    ax.plot(cast_d_wakeeffect['cast1'].Salinity, cast_d_wakeeffect['cast1'].Temperature,
            color='red', label='Post-Processing')
    # ax.plot(cast_u_wakeeffect['cast1'].Salinity, cast_u_wakeeffect['cast1'].Temperature,
    #         '--', color='red', label='Post-shift')
    ax.set_xlabel('Salinity')
    ax.set_ylabel('Temperature (C)')
    ax.set_title('Pre and Post Processing T-S Plot')
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(figure_dir, 'pre_post_T-S.png'))
    return


# ------------------------------    Step 14: bin averages  -----------------------------------
# input variables: cast_d_wakeeffect, cast_u_wakeeffect
def BINAVE(var_downcast: dict, var_upcast: dict, metadata_dict: dict, interval=1):
    """
     Bin average the profiles
     Note: Bin width and spacing are both universally chosen to be 1m in coastal waters
     Inputs:
         - downcast and upcast data dictionaries, metadata dictionary
         - default bin average interval set to 1 dbar
     Outputs:
         - two dictionaries containing downcast and upcast profiles
     """
    cast_number = len(var_downcast.keys())
    var1 = deepcopy(var_downcast)
    var2 = deepcopy(var_upcast)
    # Iterate through all the casts
    for i in range(1, cast_number + 1):
        start_d = np.floor(np.nanmin(var1['cast' + str(i)].Pressure.values))
        # start_d = np.round(start_d)
        stop_d = np.ceil(np.nanmax(var1['cast' + str(i)].Pressure.values))
        # stop_d = np.round(stop_d)
        new_press_d = np.arange(start_d - 0.5, stop_d + 1.5, interval)
        binned_d = pd.cut(var1['cast' + str(i)].Pressure, bins=new_press_d)
        obs_count_d = var1['cast' + str(i)].groupby(binned_d).size()

        var1['cast' + str(i)] = var1['cast' + str(i)].groupby(binned_d).mean()
        var1['cast' + str(i)]['Observation_counts'] = obs_count_d
        # Potential for whole row Nan values at top and bottom of output files
        var1['cast' + str(i)] = var1['cast' + str(i)].dropna(axis=0, how='any')  # drop the nans - ask if this is OK?
        var1['cast' + str(i)].reset_index(drop=True, inplace=True)

        start_u = np.ceil(np.nanmax(var2['cast' + str(i)].Pressure.values))
        stop_u = np.floor(np.nanmin(var2['cast' + str(i)].Pressure.values))
        new_press_u = np.arange(start_u + 0.5, stop_u - 1.5, -interval)
        binned_u = pd.cut(var2['cast' + str(i)].Pressure, bins=new_press_u[::-1])
        obs_count_u = var2['cast' + str(i)].groupby(binned_u).size()

        var2['cast' + str(i)] = var2['cast' + str(i)].groupby(binned_u).mean()
        var2['cast' + str(i)] = var2['cast' + str(i)].sort_values('Depth', ascending=False)
        var2['cast' + str(i)]['Observation_counts'] = obs_count_u
        var2['cast' + str(i)] = var2['cast' + str(i)].dropna(axis=0, how='any')
        var2['cast' + str(i)].reset_index(drop=True, inplace=True)

    metadata_dict['Processing_history'] += '-BINAVE parameters:' \
                                           ' Bin channel = Pressure|' \
                                           ' Averaging interval = 1.00|' \
                                           ' Minimum bin value = 0.000|' \
                                           ' Average value were used|' \
                                           ' Interpolated values were NOT used for empty bins|' \
                                           ' Channel NUMBER_OF_BIN_RECORDS was added to file|'
    metadata_dict['BINAVE_Time'] = datetime.now()

    return var1, var2


# ------------------------------    Step 15: Final edits  ----------------------------------------------------
# input variables: cast_d_binned, cast_u_binned

def FINAL_EDIT(var_cast: dict, have_oxy: bool, metadata_dict: dict) -> dict:
    """
     Final editing the profiles: edit header information, correct the unit of conductivity
     Inputs:
         - downcast and upcast data dictionaries, metadata dictionary
     Outputs:
         - two dictionaries containing downcast and upcast profiles
     """

    vars = list(dict.fromkeys(var_cast['cast1']))
    cast_number = len(var_cast.keys())
    var = deepcopy(var_cast)

    if have_oxy:
        col_list = ['Pressure', 'Depth', 'Temperature', 'Salinity', 'Fluorescence',
                    'Oxygen', 'Conductivity', 'Observation_counts']
    else:
        col_list = ['Pressure', 'Depth', 'Temperature', 'Salinity', 'Conductivity',
                    'Observation_counts']
    for i in range(1, cast_number + 1):
        var['cast' + str(i)] = var['cast' + str(i)].reset_index(drop=True)  # drop index column
        var['cast' + str(i)] = var['cast' + str(i)][col_list]  # select columns
        var['cast' + str(i)].Conductivity = var['cast' + str(i)].Conductivity * 0.1  # convert Conductivity to S/m

        var['cast' + str(i)].Pressure = var['cast' + str(i)].Pressure.apply('{:,.1f}'.format)
        var['cast' + str(i)].Depth = var['cast' + str(i)].Depth.apply('{:,.1f}'.format)
        var['cast' + str(i)].Temperature = var['cast' + str(i)].Temperature.apply('{:,.4f}'.format)
        var['cast' + str(i)].Salinity = var['cast' + str(i)].Salinity.apply('{:,.4f}'.format)
        for var_item in vars:
            if var_item == 'Fluorescence':
                var['cast' + str(i)].Fluorescence = var['cast' + str(i)].Fluorescence.apply('{:,.3f}'.format)
        for var_item in vars:
            if var_item == 'Oxygen':
                var['cast' + str(i)].Oxygen = var['cast' + str(i)].Oxygen.apply('{:,.2f}'.format)
        var['cast' + str(i)].Conductivity = var['cast' + str(i)].Conductivity.apply('{:,.6f}'.format)

        if have_oxy:
            var['cast' + str(i)].columns = ['Pressure', 'Depth', 'Temperature', 'Salinity',
                                            'Fluorescence:URU', 'Oxygen:Dissolved:Saturation:RBR',
                                            'Conductivity', 'Number_of_bin_records']
        else:
            var['cast' + str(i)].columns = ['Pressure', 'Depth', 'Temperature', 'Salinity',
                                            'Conductivity', 'Number_of_bin_records']

    metadata_dict['Processing_history'] += '-Remove Channels:|' \
                                           ' The following CHANNEL(S) were removed:|' \
                                           ' Date|' \
                                           ' TIME:UTC|' \
                                           '-CALIB parameters:|' \
                                           ' Calobration type = Correct|' \
                                           ' Calibration applied:|' \
                                           ' Conductivity (S/m) = 0.1* Conductivity (mS/cm)|'
    metadata_dict['FINALEDIT_Time'] = datetime.now()

    return var


# cast_d_final = FINAL_EDIT(cast_d_binned, metadata_dict=metadata)


# ----------------------------    IOS Header File   -----------------------------------

# define function to write file section
def write_file(cast_number, cast_original, cast_final, have_oxy: bool,
               metadata_dict: dict):
    """
     Bin average the profiles
     Inputs:
         - cast_number, cast_original = cast,
           cast_final = cast_d_final, metadata_dict = metadata, have_oxy
     Outputs:
         - two dictionaries containing downcast and upcast profiles
     """

    vars = list(dict.fromkeys(cast_original['cast1']))

    start_time = pd.to_datetime(
        cast_original['cast' + str(cast_number)].Date.values[0] + ' ' +
        cast_original['cast' + str(cast_number)].TIME.values[0]).strftime(
        "%Y/%m/%d %H:%M:%S.%f")[0:-3]
    end_time = pd.to_datetime(
        cast_original['cast' + str(cast_number)].Date.values[-1] + ' ' +
        cast_original['cast' + str(cast_number)].TIME.values[-1]).strftime(
        "%Y/%m/%d %H:%M:%S.%f")[0:-3]

    sample_interval = metadata_dict['Sampling_Interval']
    time_increment = '0 0 0 ' + sample_interval + ' 0  ! (day hr min sec ms)'

    # Number of ensembles
    number_of_records = str(cast_final['cast' + str(cast_number)].shape[0])
    data_description = metadata_dict['Data_description']
    number_of_channels = str(cast_final['cast' + str(cast_number)].shape[1])
    nan = -99
    file_type = "ASCII"

    print("*FILE")
    print("    " + '{:20}'.format('START TIME') + ": UTC " + start_time)
    print("    " + '{:20}'.format('END TIME') + ": UTC " + end_time)
    print("    " + '{:20}'.format('TIME INCREMENT') + ": " + time_increment)
    print("    " + '{:20}'.format('NUMBER OF RECORDS') + ": " + number_of_records)
    print("    " + '{:20}'.format('DATA DESCRIPTION') + ": " + data_description)
    print("    " + '{:20}'.format('FILE TYPE') + ": " + file_type)
    print("    " + '{:20}'.format('NUMBER OF CHANNELS') + ": " + number_of_channels)
    print()
    print('{:>20}'.format('$TABLE: CHANNELS'))
    print('    ' + '! No Name                             Units          Minimum        Maximum')
    print('    ' + '!--- -------------------------------- -------------- -------------- --------------')

    print('{:>8}'.format('1') + " " + '{:33}'.format(
        list(cast_final['cast' + str(cast_number)].columns)[0]) + '{:15}'.format(
        "decibar") + '{:15}'.format(
        str(np.nanmin(cast_final['cast' + str(cast_number)].Pressure.astype(float)))) + '{:14}'.format(
        str(np.nanmax(cast_final['cast' + str(cast_number)].Pressure.astype(float)))))

    print('{:>8}'.format('2') + " " + '{:33}'.format(
        list(cast_final['cast' + str(cast_number)].columns)[1]) + '{:15}'.format(
        "meters") + '{:15}'.format(
        str(np.nanmin(cast_final['cast' + str(cast_number)].Depth.astype(float)))) + '{:14}'.format(
        str(np.nanmax(cast_final['cast' + str(cast_number)].Depth.astype(float)))))

    print('{:>8}'.format('3') + " " + '{:33}'.format(
        list(cast_final['cast' + str(cast_number)].columns)[2]) + '{:15}'.format(
        "'deg C(ITS90)'") + '{:15}'.format(
        str(np.nanmin(cast_final['cast' + str(cast_number)].Temperature.astype(float)))) + '{:14}'.format(
        str(np.nanmax(cast_final['cast' + str(cast_number)].Temperature.astype(float)))))

    print('{:>8}'.format('4') + " " + '{:33}'.format(
        list(cast_final['cast' + str(cast_number)].columns)[3]) + '{:15}'.format(
        "PSS-78") + '{:15}'.format(
        str(np.nanmin(cast_final['cast' + str(cast_number)].Salinity.astype(float)))) + '{:14}'.format(
        str(float('%.04f' % np.nanmax(cast_final['cast' + str(cast_number)].Salinity.astype(float))))))

    if have_oxy:
        print('{:>8}'.format('5') + " " + '{:33}'.format(
            list(cast_final['cast' + str(cast_number)].columns)[4]) +
              '{:15}'.format("mg/m^3") +
              '{:15}'.format(str(np.nanmin(
                  cast_final['cast' + str(cast_number)]['Fluorescence:URU'].astype(float)))) +
              '{:14}'.format(str(float('%.03f' % np.nanmax(
                  cast_final['cast' + str(cast_number)]['Fluorescence:URU'].astype(float))))))

        print('{:>8}'.format('6') + " " + '{:33}'.format(
            list(cast_final['cast' + str(cast_number)].columns)[5]) + '{:15}'.format(
            "%") + '{:15}'.format(str(np.nanmin(
            cast_final['cast' + str(cast_number)]['Oxygen:Dissolved:Saturation:RBR'].astype(
                float)))) + '{:14}'.format(str(float('%.04f' % np.nanmax(
            cast_final['cast' + str(cast_number)]['Oxygen:Dissolved:Saturation:RBR'].astype(float))))))

        print('{:>8}'.format('7') + " " + '{:33}'.format(
            list(cast_final['cast' + str(cast_number)].columns)[6]) + '{:15}'.format(
            "S/m") + '{:15}'.format(
            str(np.nanmin(cast_final['cast' + str(cast_number)].Conductivity.astype(float)))) + '{:14}'.format(
            str(float('%.05f' % np.nanmax(cast_final['cast' + str(cast_number)].Conductivity.astype(float))))))

        print('{:>8}'.format('8') + " " + '{:33}'.format(
            list(cast_final['cast' + str(cast_number)].columns)[7]) + '{:15}'.format(
            "n/a") + '{:15}'.format(str(np.nanmin(
            cast_final['cast' + str(cast_number)]['Number_of_bin_records'].astype(float)))) + '{:14}'.format(
            str(np.nanmax(cast_final['cast' + str(cast_number)]['Number_of_bin_records'].astype(float)))))

    else:
        print('{:>8}'.format('5') + " " + '{:33}'.format(
            list(cast_final['cast' + str(cast_number)].columns)[4]) + '{:15}'.format(
            "S/m") + '{:15}'.format(
            str(np.nanmin(cast_final['cast' + str(cast_number)].Conductivity.astype(float)))) + '{:14}'.format(
            str(float('%.05f' % np.nanmax(cast_final['cast' + str(cast_number)].Conductivity.astype(float))))))

        print('{:>8}'.format('6') + " " + '{:33}'.format(
            list(cast_final['cast' + str(cast_number)].columns)[5]) + '{:15}'.format(
            "n/a") + '{:15}'.format(str(np.nanmin(
            cast_final['cast' + str(cast_number)]['Number_of_bin_records'].astype(float)))) +
              '{:14}'.format(
                  str(np.nanmax(cast_final['cast' + str(cast_number)]['Number_of_bin_records'].astype(float)))))

    # Add in table of Channel summary
    print('{:>8}'.format('$END'))
    print()
    print('{:>26}'.format('$TABLE: CHANNEL DETAIL'))
    print('    ' + '! No  Pad   Start  Width  Format  Type  Decimal_Places')
    print('    ' + '!---  ----  -----  -----  ------  ----  --------------')
    # print('{:>8}'.format('1') + "  " + '{:15}'.format("' '") + '{:7}'.format(' ') +
    # '{:7}'.format("' '") + '{:22}'.format('YYYY-MM-DDThh:mm:ssZ') +
    # '{:6}'.format('D, T') + '{:14}'.format("' '"))
    print(
        '{:>8}'.format('1') + "  " + '{:6}'.format(str(nan)) + '{:7}'.format("' '") + '{:7}'.format(
            str(7)) + '{:8}'.format(
            'F') + '{:6}'.format('R4') + '{:3}'.format(1))
    print(
        '{:>8}'.format('2') + "  " + '{:6}'.format(str(nan)) + '{:7}'.format("' '") + '{:7}'.format(
            str(7)) + '{:8}'.format(
            'F') + '{:6}'.format('R4') + '{:3}'.format(1))
    print(
        '{:>8}'.format('3') + "  " + '{:6}'.format(str(nan)) + '{:7}'.format("' '") + '{:7}'.format(
            str(9)) + '{:8}'.format(
            'F') + '{:6}'.format('R4') + '{:3}'.format(4))
    print(
        '{:>8}'.format('4') + "  " + '{:6}'.format(str(nan)) + '{:7}'.format("' '") + '{:7}'.format(
            str(9)) + '{:8}'.format(
            'F') + '{:6}'.format('R4') + '{:3}'.format(4))
    for var_item in vars:
        if var_item == 'Fluorescence':
            print(
                '{:>8}'.format('5') + "  " + '{:6}'.format(str(nan)) + '{:7}'.format("' '") + '{:7}'.format(
                    str(8)) + '{:8}'.format(
                    'F') + '{:6}'.format('R4') + '{:3}'.format(3))
    for var_item in vars:
        if var_item == 'Oxygen':
            print(
                '{:>8}'.format('6') + "  " + '{:6}'.format(str(nan)) + '{:7}'.format("' '") + '{:7}'.format(
                    str(8)) + '{:8}'.format(
                    'F') + '{:6}'.format('R4') + '{:3}'.format(2))
    print(
        '{:>8}'.format('7') + "  " + '{:6}'.format(str(nan)) + '{:7}'.format("' '") + '{:7}'.format(
            str(10)) + '{:8}'.format(
            'F') + '{:6}'.format('R4') + '{:3}'.format(6))
    print(
        '{:>8}'.format('8') + "  " + '{:6}'.format("' '") + '{:7}'.format("' '") + '{:7}'.format(
            str(5)) + '{:8}'.format(
            'I') + '{:6}'.format('I') + '{:3}'.format(0))
    # Add in table of Channel detail summary
    print('{:>8}'.format('$END'))
    print()


# define function to write administation section
def write_admin(metadata_dict: dict):
    mission = metadata_dict["Mission"]
    agency = metadata_dict["Agency"]
    country = metadata_dict["Country"]
    project = metadata_dict["Project"]
    scientist = metadata_dict["Scientist"]
    platform = metadata_dict["Platform"]
    print("*ADMINISTRATION")
    print("    " + '{:20}'.format('MISSION') + ": " + mission)
    print("    " + '{:20}'.format('AGENCY') + ": " + agency)
    print("    " + '{:20}'.format('COUNTRY') + ": " + country)
    print("    " + '{:20}'.format('PROJECT') + ": " + project)
    print("    " + '{:20}'.format('SCIENTIST') + ": " + scientist)
    print("    " + '{:20}'.format('PLATFORM ') + ": " + platform)
    print()
    return


def write_location(cast_number, metadata_dict: dict):
    """
     write location part in IOS header file
     Inputs:
         - cast_number, metadata_list
     Outputs:
         - part of txt file
     """
    station_number = metadata_dict['Location']['LOC:STATION'].tolist()
    event_number = metadata_dict['Location']['LOC:Event Number'].tolist()
    lon = metadata_dict['Location']['LOC:LONGITUDE'].tolist()
    lat = metadata_dict['Location']['LOC:LATITUDE'].tolist()
    print("*LOCATION")
    print("    " + '{:20}'.format('STATION') + ": " + str(station_number[cast_number - 1]))
    print("    " + '{:20}'.format('EVENT NUMBER') + ": " + str(event_number[cast_number - 1]))
    print("    " + '{:20}'.format('LATITUDE') + ":  " + lat[cast_number - 1][0:10] + "0 " + lat[cast_number - 1][
                                                                                            -14:-1] + ")")
    print("    " + '{:20}'.format('LONGITUDE') + ": " + lon[cast_number - 1])
    print()
    return


# define function to write instrument info
def write_instrument(metadata_dict: dict):
    model = metadata_dict['Instrument_Model']
    serial_number = f'{0:0}' + metadata_dict['Serial_number']
    data_description = metadata_dict['Data_description']
    instrument_type = metadata_dict['Instrument_type']
    print("*INSTRUMENT")
    print("    MODEL               : " + model)
    print("    SERIAL NUMBER       : " + serial_number)
    print("    INSTRUMENT TYPE     : " + instrument_type + "                           ! custom item")
    print("    DATA DESCRIPTION    : " + data_description + "                               ! custom item")
    print()
    return


# define function to write raw info
def write_history(cast_original, cast_clip, cast_filtered, cast_shift_c, cast_shift_o,
                  cast_wakeeffect, cast_binned, cast_final, cast_number, metadata_dict):
    """
    inputs:
        - cast_original:
        - cast_clip:
        - cast_filtered:
        - cast_shift_c:
        - cast_shift_o:
        - cast_wakeeffect:
        - cast_binned:
        - cast_final:
        - cast_number:
    outputs: nothing
    """
    vars = list(dict.fromkeys(cast_original['cast1']))
    print("*HISTORY")
    print()
    print("    $TABLE: PROGRAMS")
    print("    !   Name     Vers   Date       Time     Recs In   Recs Out")
    print("    !   -------- ------ ---------- -------- --------- ---------")
    print("        Z ORDER  " + '{:7}'.format(str(1.0))
          + '{:11}'.format(metadata_dict['ZEROORDER_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[0])
          + '{:9}'.format(metadata_dict['ZEROORDER_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[1])
          + '{:>9}'.format(str(cast_original['cast' + str(cast_number)].shape[0]))
          + '{:>10}'.format(str(cast_original['cast' + str(cast_number)].shape[0])))
    print("        CALIB    " + '{:7}'.format(str(1.0))
          + '{:11}'.format(metadata_dict['CALIB_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[0])
          + '{:9}'.format(metadata_dict['CALIB_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[1])
          + '{:>9}'.format(str(cast_original['cast' + str(cast_number)].shape[0]))
          + '{:>10}'.format(str(cast_original['cast' + str(cast_number)].shape[0])))
    print("        CLIP     " + '{:7}'.format(str(1.0))
          + '{:11}'.format(
        metadata_dict['CLIP_D_Time' + str(cast_number)].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[0])
          + '{:9}'.format(
        metadata_dict['CLIP_D_Time' + str(cast_number)].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[1])
          + '{:>9}'.format(str(cast_original['cast' + str(cast_number)].shape[0]))
          + '{:>10}'.format(str(cast_clip['cast' + str(cast_number)].shape[0])))
    print("        FILTER   " + '{:7}'.format(str(1.0))
          + '{:11}'.format(metadata_dict['FILTER_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[0])
          + '{:9}'.format(metadata_dict['FILTER_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[1])
          + '{:>9}'.format(str(cast_clip['cast' + str(cast_number)].shape[0]))
          + '{:>10}'.format(str(cast_filtered['cast' + str(cast_number)].shape[0])))
    print("        SHIFT    " + '{:7}'.format(str(1.0))
          + '{:11}'.format(
        metadata_dict['SHIFT_Conductivity_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[0])
          + '{:9}'.format(metadata_dict['SHIFT_Conductivity_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[1])
          + '{:>9}'.format(str(cast_filtered['cast' + str(cast_number)].shape[0]))
          + '{:>10}'.format(str(cast_shift_c['cast' + str(cast_number)].shape[0])))
    for var_item in vars:
        if var_item == 'Oxygen':
            print("        SHIFT    " + '{:7}'.format(str(1.0))
                  + '{:11}'.format(
                metadata_dict['SHIFT_Oxygen_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[0])
                  + '{:9}'.format(
                metadata_dict['SHIFT_Oxygen_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[1])
                  + '{:>9}'.format(str(cast_shift_c['cast' + str(cast_number)].shape[0]))
                  + '{:>10}'.format(str(cast_shift_o['cast' + str(cast_number)].shape[0])))
    print("        DELETE   " + '{:7}'.format(str(1.0))
          + '{:11}'.format(
        metadata_dict['DELETE_PRESSURE_REVERSAL_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[0])
          + '{:9}'.format(
        metadata_dict['DELETE_PRESSURE_REVERSAL_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[1])
          + '{:>9}'.format(str(cast_shift_o['cast' + str(cast_number)].shape[0]))
          + '{:>10}'.format(str(cast_wakeeffect['cast' + str(cast_number)].shape[0] -
                                list(cast_wakeeffect['cast' + str(cast_number)].isna().sum())[0])))
    print("        BINAVE   " + '{:7}'.format(str(1.0))
          + '{:11}'.format(metadata_dict['BINAVE_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[0])
          + '{:9}'.format(metadata_dict['BINAVE_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[1])
          + '{:>9}'.format(str(cast_wakeeffect['cast' + str(cast_number)].shape[0]))
          + '{:>10}'.format(str(cast_binned['cast' + str(cast_number)].shape[0])))
    print("        EDIT     " + '{:7}'.format(str(1.0))
          + '{:11}'.format(metadata_dict['FINALEDIT_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[0])
          + '{:9}'.format(metadata_dict['FINALEDIT_Time'].strftime("%Y/%m/%d %H:%M:%S.%f")[0:-7].split(" ")[1])
          + '{:>9}'.format(str(cast_binned['cast' + str(cast_number)].shape[0]))
          + '{:>10}'.format(str(cast_final['cast' + str(cast_number)].shape[0])))

    print("    $END")
    print(" $REMARKS")

    list_number = len(metadata_dict['Processing_history'].split("|"))
    for i in range(0, list_number, 1):
        print("     " + metadata_dict['Processing_history'].split("|")[i])
    print("$END")
    print()
    return


def write_comments(have_oxy: bool, metadata_dict: dict):
    cruise_ID = metadata_dict["Mission"]
    print("*COMMENTS")
    print("    " + "-" * 85)
    print()
    print("    Data Processing Notes:")
    print("    " + "-" * 22)
    print("       " + "No calibration sampling was available.")
    print()
    print("       " + "For details on the processing see document: " + cruise_ID + "_Processing_Report.doc.")

    if have_oxy:
        print("!--1--- --2--- ---3---- ---4---- ---5--- ---6--- ----7---- -8--")
        print("!Pressu Depth  Temperat Salinity Fluores Oxygen: Conductiv Numb")
        print("!re            ure               cence:  Dissolv ity       er_o")
        print("!                                URU     ed:               ~bin")
        print("!                                        Saturati          _rec")
        print("!                                        on:RBR            ords")
        print("!------ ------ -------- -------- ------- ------- --------- ----")
        print("*END OF HEADER")

    else:
        print("!--1--- --2--- ---3---- ---4---- ----5---- -6--")
        print("!Pressu Depth  Temperat Salinity Conductiv Numb")
        print("!re            ure               ity       er_o")
        print("!                                          ~bin")
        print("!                                          _rec")
        print("!                                          ords")
        print("!------ ------ -------- -------- --------- ----")
        print("*END OF HEADER")
        return


def write_data(have_oxy: bool, cast_data: dict, cast_number):  # , cast_d):
    # try:
    # check_for_oxy = cast_d.Oxygen.values
    if have_oxy:
        for i in range(len(cast_data['cast' + str(cast_number)])):
            # print(cast_data['cast' + str(cast_number)]['Pressure'][i] +
            # cast_data['cast' + str(cast_number)]['Depth'][i] + "  ")
            print('{:>7}'.format(cast_data['cast' + str(cast_number)].Pressure[i]) + " "
                  + '{:>6}'.format(cast_data['cast' + str(cast_number)].Depth[i]) + " "
                  + '{:>8}'.format(cast_data['cast' + str(cast_number)].Temperature[i]) + " "
                  + '{:>8}'.format(cast_data['cast' + str(cast_number)].Salinity[i]) + " "
                  + '{:>7}'.format(cast_data['cast' + str(cast_number)]['Fluorescence:URU'][i]) + " "
                  + '{:>7}'.format(cast_data['cast' + str(cast_number)]['Oxygen:Dissolved:Saturation:RBR'][i]) + " "
                  + '{:>9}'.format(cast_data['cast' + str(cast_number)]['Conductivity'][i]) + " "
                  + '{:>4}'.format(cast_data['cast' + str(cast_number)]['Number_of_bin_records'][i]) + " ")
    else:
        for i in range(len(cast_data['cast' + str(cast_number)])):
            # print(cast_data['cast' + str(cast_number)]['Pressure'][i] +
            # cast_data['cast' + str(cast_number)]['Depth'][i] + "  ")
            print('{:>7}'.format(cast_data['cast' + str(cast_number)].Pressure[i]) + " "
                  + '{:>6}'.format(cast_data['cast' + str(cast_number)].Depth[i]) + " "
                  + '{:>8}'.format(cast_data['cast' + str(cast_number)].Temperature[i]) + " "
                  + '{:>8}'.format(cast_data['cast' + str(cast_number)].Salinity[i]) + " "
                  + '{:>9}'.format(cast_data['cast' + str(cast_number)]['Conductivity'][i]) + " "
                  + '{:>4}'.format(cast_data['cast' + str(cast_number)]['Number_of_bin_records'][i]) + " ")
    return


def main_header(dest_dir, n_cast: int, metadata_dict: dict, cast: dict,
                cast_d: dict, cast_d_clip: dict, cast_d_filtered: dict,
                cast_d_shift_c: dict, cast_d_shift_o: dict, cast_d_wakeeffect: dict,
                cast_d_binned: dict, cast_d_final: dict, have_oxy: bool):
    """
    inputs:
        - dest_dir
        - n_cast
        - meta_data
        - cast
        - cast_d
        - cast_d_clip
        - cast_d_filtered,
        - cast_d_shift_c
        - cast_d_shift_o
        - cast_d_wakeeffect
        - cast_d_binned
        - cast_d_final
        - have_oxy
    outputs:
        - absolute path of the output data file
    """
    path_slash_type = '/' if '/' in dest_dir else '\\'
    f_name = dest_dir.split(path_slash_type)[-2]
    f_output = f_name.split("_")[0] + '-' + f'{n_cast:04}' + ".CTD"
    new_dir = os.path.join(dest_dir, f"CTD{path_slash_type}")
    output = new_dir + f_output
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    # Start
    # datetime object containing current date and time
    now = datetime.now()

    # dd/mm/YY H:M:S
    dt_string = now.strftime("%Y/%m/%d %H:%M:%S.%f")[0:-4]

    IOS_string = '*IOS HEADER VERSION 2.0      2020/03/01 2020/04/15 PYTHON'

    orig_stdout = sys.stdout
    file_handle = open(output, 'wt')
    try:
        sys.stdout = file_handle
        print("*" + dt_string)
        print(IOS_string)
        print()  # print("\n") pring("\n" * 40)
        write_file(n_cast, cast, cast_d_final, have_oxy, metadata_dict=metadata_dict)

        # def write_file(cast_number, cast_original, cast_final, metadata_dict):
        write_admin(metadata_dict=metadata_dict)
        write_location(n_cast, metadata_dict=metadata_dict)
        write_instrument(metadata_dict=metadata_dict)
        write_history(cast_d, cast_d_clip, cast_d_filtered,
                      cast_d_shift_c, cast_d_shift_o, cast_d_wakeeffect,
                      cast_d_binned, cast_d_final, cast_number=n_cast,
                      metadata_dict=metadata_dict)
        write_comments(have_oxy, metadata_dict)  # , metadata_dict=meta_data, cast_d=cast_d)
        write_data(have_oxy, cast_d_final, cast_number=n_cast)  # , cast_d=cast_d)
        sys.stdout.flush()  # Recommended by Tom
    finally:
        sys.stdout = orig_stdout
    return os.path.abspath(output)


def get_started(dest_dir):
    """ Start by opening the RSK files, find out how many channels and profiles there are

        Compare this to the cast list given by chief scientist

        prep metadata .csv

        have the header-merge.csv ready
        """

    files = os.listdir(dest_dir)  # list all the files in dest_dir
    files = list(filter(lambda f: f.endswith('.rsk'), files))  # keep the rsk files only
    n_files = len(files)  # get the number of files
    print(n_files)

    for k in range(0, n_files, 1):
        filename = str(dest_dir) + str(files[k])  # full path and name of .rsk file
        print(filename)
        rsk = pyrsktools.open(filename)  # load up an RSK

        # check the number of profiles
        n_profiles = len(list(rsk.profiles()))  # get the number of profiles recorded

        # last_profile = n_profiles[:-1] # get the last profile only
        last_profile = list(rsk.profiles())[:-1]
        print(n_profiles)
        print(rsk.samples)
        print(list(rsk.channels.items()))

    return


def first_step(dest_dir, year: str, cruise_number: str,
               event_start: int, all_last: str, data_file_type: str, num_profiles: int,
               rsk_time1=None, rsk_time2=None,
               left_lon=None, right_lon=None, bot_lat=None, top_lat=None):
    """Choose how to export the csv files from the rsk files

     Plot cruise, plot pre-processing plots, determine need for zero-order holds correction

     if multi_file choose an rsk_file for metadata

     inputs:
        - dest_dir, yearm cruise_number
        - event_start:
        - all_last: "all" (ingest all casts in each raw file) or "last" (ingest
        only last cast)
        - data_file_type: "rsk" for single or multiple rsk files, or "excel"
        (use on .xlsx files exported from Ruskin)
        - left_lon, right_lon, bot_lat, top_lat: map extent for plotting cast locations
     Outputs:
        - None in terms of python objects, but data files and plots are saved

     IMPORTANT: DON"T FORGET TO CHANGE THE SHEETNAME TO Profile_annotation or
     openpyxl won't read it.
     """

    if data_file_type == 'rsk':
        EXPORT_MULTIFILES(dest_dir, num_profiles, event_start, all_last, rsk_time1, rsk_time2)  # year, cruise_number,
    elif data_file_type == 'excel':
        # input file =  # not needed, filtered to keep only .xls
        READ_EXCELrsk(dest_dir, year, cruise_number, event_start, all_last)

    # Merge all data from a cruise into one csv file
    MERGE_FILES(dest_dir, year, cruise_number)
    print('files merged')
    ADD_6LINEHEADER_2(dest_dir, year, cruise_number)

    # Make preliminary plots
    plot_track_location(dest_dir, year, cruise_number, left_lon, right_lon, bot_lat, top_lat)
    first_plots(year, cruise_number, dest_dir, input_ext='_CTD_DATA-6linehdr.csv')
    PLOT_PRESSURE_DIFF(dest_dir, year, cruise_number, input_ext='_CTD_DATA-6linehdr.csv')
    return


def second_step(dest_dir: str, year: str, cruise_number: str,
                rsk_file, rsk_time1=None, rsk_time2=None,
                pd_correction_value=0,
                window_width=6,  # sample_rate=8, time_constant=1 / 8,
                filter_type=1, shift_recs_conductivity=2,
                shift_recs_oxygen=-11, verbose: bool = False):
    """
    Make corrections for zero-order holds and Pressure if needed
    zoh is zero-order holds correction
    inputs:
        - dest_dir
        - year
        - cruise_number
        - correction_value: value to correct pressure and depth data by using CALIB
        - input_ext: '_CTD_DATA-6linehdr.csv' or '_CTD_DATA-6linehdr_corr_hold.csv'
    outputs: none
    """

    # Create metadata dict
    metadata_dict = CREATE_META_DICT(dest_dir=dest_dir, rsk_file=rsk_file,
                                     year=year, cruise_number=cruise_number,
                                     rsk_time1=rsk_time1, rsk_time2=rsk_time2)

    # initialize casts for if statement
    cast, cast_d, cast_u = 0, 0, 0
    cast_pc, cast_d_pc, cast_u_pc = 0, 0, 0

    if verbose:
        print('Checking need for zero-order hold correction...')
    # Check pressure channel for zero order holds
    zoh = check_for_zoh(dest_dir, year, cruise_number,
                        float(metadata_dict['Sampling_Interval']))

    if zoh:
        # Correct the zero-order-holds
        CORRECT_HOLD(dest_dir, year, cruise_number, metadata_dict)

        input_ext = '_CTD_DATA-6linehdr_corr_hold.csv'

        if verbose:
            print('Using zero-order holds corrected variables')

        # check the plot then save it as Fig_3
        PLOT_PRESSURE_DIFF(dest_dir, year, cruise_number, input_ext)

        # t_cast_pc, t_cast_d_pc, t_cast_u_pc = CALIB(t_cast, t_cast_d, t_cast_u,
        #                                             metadata_dict,
        #                                             zoh, pd_correction_value)  # 0 if no neg pressures
        #
        # cast, cast_d, cast_u = t_cast, t_cast_d, t_cast_u
        #
        # cast_pc, cast_d_pc, cast_u_pc = t_cast_pc, t_cast_d_pc, t_cast_u_pc  # probably don't need the t_
    else:
        input_ext = '_CTD_DATA-6linehdr.csv'

        if verbose:
            print('using original variables')

        # cast_pc, cast_d_pc, cast_u_pc = CALIB(cast, cast_d, cast_u, pd_correction_value,
        #                                       metadata_dict, zoh=zoh)  # 0 if no neg pressures
        #

    cast, cast_d, cast_u = CREATE_CAST_VARIABLES(year, cruise_number, dest_dir, input_ext)

    # Calibrate pressure and depth
    cast_pc, cast_d_pc, cast_u_pc = CALIB(cast, cast_d, cast_u, metadata_dict, zoh,
                                          pd_correction_value)  # 0 if no neg pressures
    if verbose:
        print('The following correction value has been applied to Pressure and Depth:',
              pd_correction_value, sep='\n')

    # Commented this out because first plots are made earlier and in the past haven't been
    # remade after the zero hold correction. Plus there are two possible input_ext now.
    # first_plots(year, cruise_number, dest_dir, input_ext='_CTD_DATA-6linehdr_corr_hold.csv')
    # print('finished plotting first plots')

    # vars = list(dict.fromkeys(cast['cast1']))

    # clip the casts
    # cast_d_clip = CLIP_DOWNCAST(cast_d_pc, metadata_dict, limit_drop=0.02)
    # cast_u_clip = CLIP_UPCAST(cast_u_pc, metadata_dict, limit_rise=-0.02)
    cast_d_clip = CLIP_CAST(cast_d_pc, metadata_dict, limit_pressure_change=0.02,
                            cast_direction='down')
    cast_u_clip = CLIP_CAST(cast_u_pc, metadata_dict, limit_pressure_change=-0.02,
                            cast_direction='up')

    plot_clip(cast, cast_d_clip, cast_d_pc, dest_dir)

    if verbose:
        print('Casts clipped')

    # Check if oxygen data available todo confirm this check works properly
    print(cast_d_clip['cast1'].columns)
    have_oxy = True if 'Oxygen' in cast_d_clip['cast1'].columns else False
    have_fluor = True if 'Fluorescence' in cast_d_clip['cast1'].columns else False

    # Apply a low-pass filter
    # metadata_dict['Sampling_Interval']: time in seconds between records
    # (0.125-0.167s for an 8-6Hz instrument)
    cast_d_filtered, cast_u_filtered = FILTER(
        cast_d_clip, cast_u_clip, metadata_dict, have_fluor, window_width,
        sample_rate=int(np.round(1/float(metadata_dict['Sampling_Interval']))),
        time_constant=float(metadata_dict['Sampling_Interval']),
        filter_type=filter_type)  # n = 5 should be good.

    # Plot the filtered data
    plot_filter(cast_d_filtered, cast_d_clip, dest_dir, have_fluor)

    if verbose:
        print('Casts filtered')

    # Shift the conductivity channel and recalculate salinity after
    # Default conductivity shift is a delay by 2 scans
    cast_d_shift_c, cast_u_shift_c = SHIFT_CONDUCTIVITY(
        cast_d_filtered, cast_u_filtered, metadata_dict=metadata_dict,
        shifted_scan_number=shift_recs_conductivity)

    plot_shift_c(cast_d_shift_c, cast_d_filtered, dest_dir)

    if verbose:
        print(f'Conductivity shifted {-shift_recs_conductivity} scans')

    # Shift oxygen channel if available, then calculate oxygen concentration
    if have_oxy:
        cast_d_shift_o, cast_u_shift_o = SHIFT_OXYGEN(
            cast_d_shift_c, cast_u_shift_c, metadata_dict=metadata_dict,
            shifted_scan_number=shift_recs_oxygen)

        plot_shift_o(cast_d_shift_o, cast_d_shift_c, dest_dir)

        if verbose:
            print(f'Oxygen shifted {-shift_recs_oxygen} scans')

        # Add cast variables of oxygen conc. in ml/l and umol/kg
        cast_d_o_conc, cast_u_o_conc = DERIVE_OXYGEN_CONCENTRATION(
            cast_d_shift_o, cast_u_shift_o, metadata_dict)

        if verbose:
            print('Oxygen concentration derived from oxygen saturation')
    else:
        # Rename the variables
        cast_d_o_conc, cast_u_o_conc = cast_d_shift_c, cast_u_shift_c

    # Delete the upcast and all other pressure change reversals
    cast_d_wakeeffect, cast_u_wakeeffect = DELETE_PRESSURE_REVERSAL(
        cast_d_o_conc, cast_u_o_conc, metadata_dict=metadata_dict)

    if verbose:
        print('Deleted pressure change reversals')

    # Plot before and after comparisons of the delete step
    plot_processed(cast_d_wakeeffect, cast_d_o_conc, cast_d, cast, dest_dir)

    # Average the data into 1-dbar bins
    cast_d_binned, cast_u_binned = BINAVE(cast_d_wakeeffect, cast_u_wakeeffect,
                                          metadata_dict=metadata_dict)

    if verbose:
        print('Records averaged into equal-width pressure bins')

    # Final edits: change conductivity units
    cast_d_final = FINAL_EDIT(cast_d_binned, have_oxy, metadata_dict)

    if verbose:
        print('Final edit completed')

    # # Produce the IOS Shell header files containing the final data
    # main_header(dest_dir, n_cast,
    #             metadata_dict, cast, cast_d, cast_d_clip, cast_d_filtered,
    #             cast_d_shift_c, cast_d_shift_o,
    #             cast_d_wakeeffect, cast_d_binned, cast_d_final, have_oxy)

    for i in range(len(cast)):
        main_header(dest_dir, i + 1,
                    metadata_dict, cast, cast_d, cast_d_clip, cast_d_filtered,
                    cast_d_shift_c, cast_d_shift_o,
                    cast_d_wakeeffect, cast_d_binned, cast_d_final, have_oxy)

    if verbose:
        print('Header files produced')

    return


def PROCESS_RBR(dest_dir, year: str, cruise_number: str, rsk_file: str,
                event_start: int, all_last: str, data_file_type: str,
                num_profiles: int, window_width: int, filter_type: int = 1,
                # sample_rate: int, time_constant: float,
                shift_recs_conductivity: int = -2, shift_recs_oxygen=None,
                pd_correction_value=0, rsk_time1=None, rsk_time2=None,
                left_lon=None, right_lon=None, bot_lat=None, top_lat=None,
                ):
    """
    Main function to run the suite of processing functions on raw RBR data
    inputs:
        - dest_dir, year,
        - cruise_number: 3-character string, e.g., '015', '101'
        - event_start:
        - all_last: "all" (ingest all casts in each raw file) or "last" (ingest
        only last cast)
        - file_option: "single" (use for single .rsk file), or "multi" (use for
        multiple .rsk files), or "from_excel" (use on .xlsx files exported from Ruskin)
        - left_lon, right_lon, bot_lat, top_lat: map extent for plotting cast locations
    """

    first_step(dest_dir, year, cruise_number, event_start, all_last,
               data_file_type, num_profiles, rsk_time1, rsk_time2, left_lon, right_lon,
               bot_lat, top_lat)

    second_step(dest_dir, year, cruise_number, rsk_file, rsk_time1, rsk_time2,
                pd_correction_value, window_width,  # sample_rate, time_constant,
                filter_type, shift_recs_conductivity, shift_recs_oxygen)
    return


def test_process():
    test_year = '2022'
    test_cruise_num = '025'
    test_file = '201172_20220925_1059.rsk'
    num_profiles = 6

    # test_year = '2023'
    # test_cruise_num = '015'
    # test_file = '208765_20230121_2113_newDOcoefficients.rsk'
    # num_profiles = 44

    test_dir = 'C:\\Users\\HourstonH\\Documents\\ctd_processing\\RBR\\' \
               'python_testing\\{}-{}\\'.format(test_year, test_cruise_num)
    test_event_start = 1

    # EXPORT_MULTIFILES(test_dir, num_profiles, test_event_start, 'ALL')
    # MERGE_FILES(test_dir, test_year, test_cruise_num, event_from='header-merge')

    # first_step(test_dir, test_year, test_cruise_num, test_event_start, 'ALL', 'rsk',
    #            num_profiles)

    second_step(test_dir, test_year, test_cruise_num, test_file, window_width=3,
                filter_type=1, verbose=True)

    # PROCESS_RBR(test_dir, test_year, test_cruise_num,
    #             rsk_file=test_file,
    #             event_start=test_event_start, all_last='ALL', data_file_type='rsk',
    #             num_profiles=num_profiles,
    #             window_width=3,  # sample_rate=8, time_constant=1 / 8,
    #             shift_recs_oxygen=-11)

    return
