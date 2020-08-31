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
import numpy as np

# As usual nicked something else to hack. This code was saved as ookla_location.py and building up to
# producing mapbox plots of trialists signal strength to location. I want to do two other things for
# the Powerpoint so start with this as a "template"
# 1) Simple scatter plot of Ookla
# 2) Table showing relation between predicted RSRP and that returned by ACS to return four columns
# postcode, predicted_RSRP, mean_ACS_RSRP, SampleSize

"""
          _____  _____     _____   _____ _____  _____  
    /\   / ____|/ ____|   |  __ \ / ____|  __ \|  __ \ 
   /  \ | |    | (_____  _| |__) | (___ | |__) | |__) |
  / /\ \| |     \___ \ \/ /  _  / \___ \|  _  /|  ___/ 
 / ____ \ |____ ____) >  <| | \ \ ____) | | \ \| |     
/_/    \_\_____|_____/_/\_\_|  \_\_____/|_|  \_\_|     
                                                                                                              
"""
import glob
import pandas as pd

workdir = r'C:\1drive\OneDrive - Three\__projects\_5g\ookla-speed\\'   # damn Bill Gates' backslash
acsdir = r'C:\1drive\OneDrive - Three\jumpserver\UKB\ACS_Reports'
filespec = acsdir + r'\3UK_CPE_2020*csv'
files = glob.glob(filespec)

# Seems to be a pretty nasty bug in pandas pd.read_csv when it comes to handling files with multiple empty
# columns on RHS. (OK so our source data should never be like that but we don't control it!)
# Our data has:
# - three valid fields (0-2)
# - three blank fields (3-5)
# - nine more valid fields (6-14)
# - ten more blank fields which are causing the problem (15-24)
# Workaround is to set the index column to 15. Index ends up as rubbish but it loads correctly :-)

acs = pd.DataFrame()
for file in files:
    print('adding', file)
    acs = acs.append(pd.read_csv(file, index_col=15, header=0,))

# trying to do this intelligently by only loading the wanted columns (loading is very broken due to all those
# empty cols in the data) or testing columns are empty and then deleting didn't work so need to specify which
# cols in the ACS data are empty and drop manually. Still very worthwhile doing this as over half are empty!
emptycols = ['Identity', 'CINR0', 'CINR1', 'P01', 'P02', 'P03',
             'P04', 'P05', 'P06', 'P07', 'P08', 'P09', 'P10']

print('acs shape before dropping empty cols', acs.shape)
acs.drop(columns=emptycols, inplace=True)
print('acs shape after dropping empty cols', acs.shape)

# values of RSRP_5G = -199 are incorrect so rows need to be dropped
print(acs.__len__(), 'records before dropping -199')
acs = acs[acs['RSRP_5G'] != -199]
print(acs.__len__(), 'records after dropping -199')


pcfile = r'C:\1drive\OneDrive - Three\__projects\_5g\ookla-speed\postcode_imsi.csv'
postcodes = pd.read_csv(pcfile, index_col='IMSI')
# postcodes.insert('mean_rsrp5G') ... insists on a value - is there any benefit to creating zeros?
postcodes['mean_rsrp5G'] = pd.Series(np.nan)
postcodes['count_rsrp5G'] = pd.Series(np.zeros)

for imsi in postcodes.index:
    mean_rsrp5G = acs[acs['imsi'] == imsi].mean()['RSRP_5G']
    # Need to check how pandas is calculating the mean RSRP.
    print(imsi, 'mean value', mean_rsrp5G)
    postcodes.at[imsi, 'mean_rsrp5G'] = mean_rsrp5G

    count_rsrp5G = acs[acs['imsi'] == imsi].count()['RSRP_5G']
    # Need to check how pandas is calculating the mean RSRP.
    print(imsi, 'number of samples', count_rsrp5G)
    postcodes.at[imsi, 'count_rsrp5G'] = count_rsrp5G

postcodes['count_rsrp5G'] = postcodes['count_rsrp5G'].astype(int)
postcodes.to_csv(workdir + 'postcode2acs.csv', index=False)

"""
It would be good to remove all those useless empty columns based on first checking they are empty
testing individual columns with, for example:  
acs['imsi'].sum() 
has no problem in returning a massive number or zero if empty but the following start of an idea just doesn't work! 

for c in acs.columns:
    print(c)
    acs[c].sum()
    
... so need to specify the cols to drop, however more efficient to do that in the initial acs data load 
"""

acs3 = acs[acs['imsi'].isin(postcodes.index)]
print(acs3.__len__(), 'records for just three trialists')
acs3.to_csv(workdir + 'acs3.csv', index=False)



"""
  ____   ____  _  ___               
 / __ \ / __ \| |/ / |        /\    
| |  | | |  | | ' /| |       /  \   
| |  | | |  | |  < | |      / /\ \  
| |__| | |__| | . \| |____ / ____ \ 
 \____/ \____/|_|\_\______/_/    \_\
                                    
"""


# workdir is where any processed data will go
workdir = 'C:/1drive/OneDrive - Three/__projects/_5g/ookla-speed/'
# set path to the Ookla csv files and use globbing to get a current list for both Android and iPhone
ookladir = 'P:/ookla/'
android_csvs = glob.glob(ookladir + 'android_20*csv')
iphone_csvs = glob.glob(ookladir + 'iOs_20*csv')

android_zips = glob.glob(ookladir + 'android_20*zip')
iphone_zips = glob.glob(ookladir + 'iOs_20*zip')

# TEST  android_zips = ['p:/ookla\\android_2020-07-25.zip',  'p:/ookla\\android_2020-07-26.zip',  'p:/ookla\\android_2020-07-27.zip',  'p:/ookla\\android_2020-07-28.zip']
mapbox_access_token = open(".mapbox_token").read()

# trialists = ['AC', 'CW', 'JC', 'JM', 'JR', 'KL', 'SC1']
androids = {
    268326942: 'CW',
    313643292: 'KL',
    218072934: 'JR',
#    6164563342: 'JR',
    315483301: 'AC',
    120115319: 'me',
}
iphones = {
    169942571: 'SC1',
    182682821: 'JC',
    141331475: 'JM',
}

# Find the wanted columns relating to Android test devices
and_cols = [0, 1, 3, 4, 5, 6, 19, 20, 22, 64, 67, 68, 69, 75, 76,
            77, 78, 79, 80, 81, 89, 90, 91, 92, 100, 101, 102, 106,
            107, 108, 109, 115, 116, 117, 118, 120, 123, 124]

and_df = pd.DataFrame()
for zipf in android_zips:
    print('checking', zipf)
    ook = pd.read_csv(zipf, compression='zip', header=0, usecols=and_cols, low_memory=False)
    for key in androids.keys():
        print('seeking', key)
        and_df = and_df.append(ook[ook['android_device_id'] == key])

# print the size and whilst we're at it write to a CSV
print(and_df.shape)
and_df.to_csv(workdir + 'android_results.csv', index=False)

# repeat for iOS test devices
ios_cols = [0, 5, 6, 1, 3, 4, 19, 20, 24, 72, 47, 61, 62, 48, 49]
ios_df = pd.DataFrame()
for zipf in iphone_zips:
    print('checking', zipf)
    ook = pd.read_csv(zipf, compression='zip', header=0, usecols=ios_cols, low_memory=False)
    for key in iphones.keys():
        print('seeking', key)
        ios_df = ios_df.append(ook[ook['iphone_device_id'] == key])

# print the size and whilst we're at it write to a CSV
print(ios_df.shape)
ios_df.to_csv(workdir + 'iphone_results.csv', index=False)

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





