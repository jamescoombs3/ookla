import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
# from os import listdir
# from os.path import isfile, join
import re
# import zipfile
import pandas as pd
import glob
import timeit

# workdir is where any processed data will go
workdir = 'C:/1drive/OneDrive - Three/__projects/_5g/ookla-speed/'
# set path to the Ookla csv files and use globbing to get a current list for both Android and iPhone
ookladir = 'P:/ookla/'
# android_csvs = glob.glob(ookladir + 'android_20*csv')
# iphone_csvs = glob.glob(ookladir + 'iOs_20*csv')

android_zips = glob.glob(ookladir + 'android_20*zip')
iphone_zips = glob.glob(ookladir + 'iOs_20*zip')

# TEST  android_zips = ['p:/ookla\\android_2020-07-25.zip',  'p:/ookla\\android_2020-07-26.zip',  'p:/ookla\\android_2020-07-27.zip',  'p:/ookla\\android_2020-07-28.zip']
mapbox_access_token = open(".mapbox_token").read()

"""
 _____            _   _          _____       _______       
|  __ \     /\   | \ | |        |  __ \   /\|__   __|/\    
| |__) |   /  \  |  \| |        | |  | | /  \  | |  /  \   
|  _  /   / /\ \ | . ` |        | |  | |/ /\ \ | | / /\ \  
| | \ \  / ____ \| |\  |        | |__| / ____ \| |/ ____ \ 
|_|  \_\/_/    \_\_| \_|        |_____/_/    \_\_/_/    \_\

"""

# Add serving cell's coordinates using different sources for 3G and 4G
# 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G 3G
# 3G RAN config is sourced from http://opencellid.org/downloads.php?token=22d7e3274bddf4
conf3g = pd.read_csv(r'C:\1drive\OneDrive - Three\jumpserver\234.csv\234.csv', usecols=[0, 2, 3, 4, 6, 7])
# remove all but Three's records MNC=20
conf3g = conf3g[conf3g['net'] == 20]  # reduces from ~1.6m to .29m records so 1/6 the memory use!
# rename the columns to match the Ookla naming
conf3g.rename(columns={'radio': 'localcell_id', 'area': 'tac_a',
                       'cell': 'cid_a', 'lon': 'cell_lon', 'lat': 'cell_lat'},
              inplace=True)
# drop the net column (only loaded so we could save some memory)
conf3g.drop(columns=['net'], inplace=True)
# end up with shape (287288, 5), columns ['radio', 'tac_a', 'cid_a', 'lon', 'lat']

# 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G 4G
# For LTE we'll look in the latest iteration of:
conf4g_csv = r'C:\1drive\OneDrive - Three\jumpserver\Huawei\4G_RAN_Config\ERNI.4GCELL.POLYSTAR_20200730_003015.csv'
conf4g = pd.read_csv(conf4g_csv, usecols=[3, 13, 18, 22, 23])
# rename the columns to match the Ookla naming
conf4g.rename(columns={'localcell_id': 'localcell_id', 'taccode': 'tac_a',
                       'ECI-decimal': 'cid_a', 'longitude': 'cell_lon', 'latitude': 'cell_lat'},
              inplace=True)

"""
  ____   ____  _  ___                                 _   _ _____  _____   ____ _____ _____  
 / __ \ / __ \| |/ / |        /\                /\   | \ | |  __ \|  __ \ / __ \_   _|  __ \ 
| |  | | |  | | ' /| |       /  \              /  \  |  \| | |  | | |__) | |  | || | | |  | |
| |  | | |  | |  < | |      / /\ \            / /\ \ | . ` | |  | |  _  /| |  | || | | |  | |
| |__| | |__| | . \| |____ / ____ \          / ____ \| |\  | |__| | | \ \| |__| || |_| |__| |
 \____/ \____/|_|\_\______/_/    \_\        /_/    \_\_| \_|_____/|_|  \_\\____/_____|_____/ 
"""
# Initially separate dictionary for Android and iOS were set up. Simpler to create a single dictionary and
# look in both sources (and no slower in execution)
device_ids = {
268326942: 'CW',
313643292: 'KL',
218072934: 'JR',
315483301: 'AC',
169942571: 'SC1',
182682821: 'JC',
141331475: 'JM',
120115319: 'me',
253918328: 'AR',
293138196: 'AR5G',
292144061: 'SK',
295983942: 'CRY',
}

# for one off testing ...
# device_ids = {120115319: 'me',}




# Find the wanted columns relating to Android test devices
and_cols = [0, 1, 3, 4, 5, 6, 19, 20, 22, 64, 67, 68, 69, 75, 76,
            77, 78, 79, 80, 81, 89, 90, 91, 92, 100, 101, 102, 106,
            107, 108, 109, 115, 116, 117, 118, 120, 123, 124]

start_time = timeit.default_timer()
and_df = pd.DataFrame()
for zipf in android_zips:
    print('checking', zipf)
    ook = pd.read_csv(zipf, compression='zip', header=0, usecols=and_cols, low_memory=False)
    for key in device_ids.keys():
        print('seeking', key)
        and_df = and_df.append(ook[ook['android_device_id'] == key])
        print('found', and_df.__len__(), 'records')


elapsed = timeit.default_timer() - start_time
print('Scanned', android_zips.__len__(), 'massive zipped Android CSV files scanned in', elapsed, 'seconds!')
# five minutes is very impressive to load all that data but save to CSV so when the IDE crashes ...
and_df.to_csv(workdir + 'android_results.csv')
# print the shape
print(and_df.shape)

"""
  ____   ____  _  ___                        _  ____   _____ 
 / __ \ / __ \| |/ / |        /\            (_)/ __ \ / ____|
| |  | | |  | | ' /| |       /  \            _| |  | | (___  
| |  | | |  | |  < | |      / /\ \          | | |  | |\___ \ 
| |__| | |__| | . \| |____ / ____ \         | | |__| |____) |
 \____/ \____/|_|\_\______/_/    \_\        |_|\____/|_____/ 
                                                             
"""

# repeat for iOS test devices
ios_cols = [0, 5, 6, 1, 3, 4, 19, 20, 24, 72, 47, 61, 62, 48, 49]
start_time = timeit.default_timer()
ios_df = pd.DataFrame()
for zipf in iphone_zips:
    print('checking', zipf)
    ook = pd.read_csv(zipf, compression='zip', header=0, usecols=ios_cols, low_memory=False)
    for key in device_ids.keys():
        print('seeking', key)
        ios_df = ios_df.append(ook[ook['iphone_device_id'] == key])
        print('found', ios_df.__len__(), 'records')

# print the size and whilst we're at it write to a CSV

elapsed = timeit.default_timer() - start_time
print('Scanned', iphone_zips.__len__(), 'massive zipped iOS CSV files scanned in', elapsed, 'seconds!')
# five minutes is very impressive to load all that data but save to CSV so when the IDE crashes ...
ios_df.to_csv(workdir + 'iphone_results.csv', index=False)
print(ios_df.shape)


"""
 __  __ ______ _____   _____ ______     
|  \/  |  ____|  __ \ / ____|  ____|
| \  / | |__  | |__) | |  __| |__
| |\/| |  __| |  _  /| | |_ |  __|
| |  | | |____| | \ \| |__| | |____
|_|  |_|______|_|  \_\\_____|______|
                                                                                      
"""
# These columns in the RAN data should all really be integer so might as well do all of them.
to_ints = ['pci_a', 'tac_a', 'cid_a', 'lac_a', 'psc_a', 'asu_level_a', 'dbm_a', 'level_a', 'ploss_sent_a',
           'ploss_recv_a', 'wifi_speed_mbps_a', 'wifi_frequency_mhz_a', 'uarfcn_a', 'arfcn_a', 'bsic_a',
           'earfcn_a', 'rsrp_a', 'rsrq_a', 'rssnr_a', 'download_kb_a']
# ... will hold off doing that as there are NaN values where info is missing.
# Don't delete the assignment just yet as it may turn out to be useful.

# If necessary re-load the CSV database ...
# and_df = pd.read_csv(workdir + 'android_results.csv')

# The merge between Ookla and RAN data used TAC and CID but was failing on 3G due to NaN values
# original was to remove all records missing either of these values which reduced from 845 to 745 (-100)
# and_df.dropna(subset=['tac_a', 'cid_a'], inplace=True)

# Only need to drop the CID to enable 3G to merge.
and_df.dropna(subset=['cid_a'], inplace=True)

# The merges only records which can match tac_a and cid_a with the 4G RAN data
and_4g = pd.merge(and_df, conf4g)

# The crowd source also includes some 4G sites so we have to select the correct records only from amd_df
# this can be manually validated by running and_df[and_df['signal_cell_type_a'] == 3].shape
# There are only 58 (when writing) rows of tests on 3G which can be filtered out like this:
and_3g = pd.merge(and_df[and_df['signal_cell_type_a'] == 3], conf3g)

and_all = pd.concat(and_3g, and_4g)

"""
# rename the lon/lat columns so it is clear these relate to the cell and not UE when merged with Ookla data
conf3g.rename(columns={'lon': 'cell_lon', 'lat': 'cell_lat'}, inplace=True)
# In 4G RAN data 'localcell_id' also gives frequency but this is missing in 3G data
# rename the and_3g column 'radio' which contains UMTS|GSM|LTE to 'localcell_id'
conf3g.rename(columns={'radio': 'localcell_id'}, inplace=True)

# merge the and_df fields with both 3g and 4g. Only rows which match will be merged so the total rows in
# these two df added will contain the same number of rows as and_df
and_4g = pd.merge(and_df, conf4g)
and_3g = pd.merge(and_df, conf3g)


# currently only contains the 4G records but does include three new columns
# 'localcell_id',
# 'longitude',
# 'latitude'

# iterate over the 3G rows? Maybe inefficient coding so I might want to revise this later
df = and_df[and_df['signal_cell_type_a'] == 3]


# if signal_cell_type_a == 4 we want to look up cid_a in conf4g to return the lat/long relating to 'ECI-decimal'
# could we simply do a merge?
"""



# I now have two dataframes, and_df for Android and ios_df for iOS

# objective is to iterate over all of these extracting the Ookla results directly from the Ookla csv files
# start by writing the code for just JR as he has a mix of WiFi and LTE
# ... need to also clean the source data

# hard code for testing
tt = 'JR'
id = '6164563342'   # should this be an integer since it can be?







# separate out Lte from Wifi tests
lte = ostd[ostd['ConnType'] == 'Lte']
wifi = ostd[ostd['ConnType'] == 'Wifi']

# plot the WiFi and LTE results individually
fig = go.Figure()
fig.add_trace(go.Scattermapbox(
    mode='markers',
    # size=wifi['DLSpeed'], # yes this doesn't work!!
    lat=wifi['Lat'],
    lon=wifi['Lon'],
    name='WiFi',
    #text=lte['Date'] + ' ' + lte['DLSpeed'] + ' DLink',
    text=lte['DLSpeed'],
    marker={'size': 15}))
fig.add_trace(go.Scattermapbox(
    mode='markers',
    lat=lte['Lat'],
    lon=lte['Lon'],
    name='LTE',
    text=lte['Date'],
    marker={'size': 15}))

fig.update_layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=51.42541545,
            lon=-0.156844207
        ),
        pitch=0,
        zoom=19
    ),
)

fig.write_html(workdir + 'Ookla_KL.html', auto_open=True)

# Look  at just the WiFi results, see if we can include the download speed as a colour or size of bubble.




"""
fig = px.scatter_mapbox(wifi, lat='Lat', lon='Lon', size='DLSpeed', # size="car_hours",
                  # color_continuous_scale=px.colors.cyclical.IceFire,
                        size_max=15, zoom=10)

"""



# single range but with text hoverover



fig = go.Figure(go.Scattermapbox(
    lat=wifi['Lat'],
    lon=wifi['Lon'],
    mode='markers',
    marker=go.scattermapbox.Marker(size=9),
    text=wifi['label'],
    ))

fig.update_layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=51.42541545,
            lon=-0.156844207
        ),
        pitch=0,
        zoom=19
    ),
)



fig.write_html(workdir + 'Ookla_KL.html', auto_open=True)





