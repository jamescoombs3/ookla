
"""
  ____   ____  _  ___                _____         __  __ _____  _      ______
 / __ \ / __ \| |/ / |        /\    / ____|  /\   |  \/  |  __ \| |    |  ____|
| |  | | |  | | ' /| |       /  \  | (___   /  \  | \  / | |__) | |    | |__
| |  | | |  | |  < | |      / /\ \  \___ \ / /\ \ | |\/| |  ___/| |    |  __|
| |__| | |__| | . \| |____ / ____ \ ____) / ____ \| |  | | |    | |____| |____
 \____/ \____/|_|\_\______/_/    \_\_____/_/    \_\_|  |_|_|    |______|______|

Analysis of the actual Ookla data

Version 0.1 (16/1/21) First version. Writes monthly summaries of the wanted values
Version 0.2 (14/2/21) Removed some columns and also rows north of 600km (still captures 93% of the population)
Entire project is uploaded to https://github.com/jamescoombs3/ookla
"""

import pandas as pd
import glob
from pyproj import Transformer

import xlrd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.formula.api as smf

# define a directory to write any outputs
workdir = 'C:/1drive/OneDrive - Three/_avado_Masters/_PROJECT/plots/'
# define location of the raw data
ookladir = 'P:/ookla/'
# can define a RE to load just a sample eg android_2020-01-12.zip
# android_zips = glob.glob(ookladir + 'android_2020*12.zip')

# First scan - looks like I should keep these columns
cols = [3,   4,    19,  20,  24,  25,  26,  27,  30,  31,  33,  34,  36,  37,  38,  39,  48,  59,  64,  70,  76,
        77,  82,   83,  84,  85,  86,  87,  88,  89,  95,  96, 101, 102, 103, 104, 108, 112, 113, 114, 115, 116,
        119, 120, 121, 122, 126, 127, 128, 133, 134, 136, 141, 142, 145, 146, 147, 151, 152, 153, 157, 158, 161, 163]

# Second scan - looks I should keep these instead ...
cols = [3, 19, 20, 25, 26, 27, 30, 31, 33, 34, 37, 59, 64, 95, 96, 101, 102, 103, 104, 112, 113, 115, 116, 120,
         121, 122, 126, 127, 128, 133, 134, 136, 141, 142]

# Splitting data by months and filter by Three results in ~500k records per month
mths = ['2020-05', '2020-06', '2020-07', '2020-08', '2020-09', '2020-10', '2020-11', '2020-12', '2021-01']

# Comment out the following to completely re-run the initial extract (maybe with additional columns)
# mths = ['2021-01']

# for dev/testing
# cols = [3,   4,    19,  20,  24,  25,  26, 102, 115]
# mths = ['2020-04']

# Define the projections and transformation method
bng = 'epsg:27700'
wgs84 = 'epsg:4326'
transformer = Transformer.from_crs(wgs84, bng)


for m in mths:
    android_zips = glob.glob(ookladir + 'android_' + m + '*.zip')
    # print(android_zips)
    # create an empty dataframe
    android_df = pd.DataFrame
    for zipf in android_zips:
        print('checking', zipf)
        ook = pd.read_csv(zipf, compression='zip', header=0, usecols=cols, low_memory=False)
        print(ook.__len__(), 'records read ... selecting mnc/mcc 234/20 accuracy <= 10 metres')
        ook = ook[ook['mnc'] == 20]
        ook = ook[ook['mcc'] == 234]
        # coerce the location accuracy and rsrp columns to integers
        ook.location_accuracy_a = pd.to_numeric(ook.location_accuracy_a, errors='coerce').fillna(0).astype(np.int64)
        ook.rsrp_a = pd.to_numeric(ook.rsrp_a, errors='coerce').fillna(0).astype(np.int64)
        ook = ook[ook['location_accuracy_a'] <= 10]
        # rsrp should always be negative so selecting where this is less than zero will remove missing values
        ook = ook[ook['rsrp_a'] < 0]
        print(ook.__len__(), 'records remain')
        # appending to an empty dataframe doesn't work, get around this with try/except
        # first time try will fail and the except initialises the dataframe with contents of the first zip file
        # subsequent attempts the try will append the contents of the other zip file
        try:
            android_df = android_df.append(ook)
        except:
            android_df = ook

        print('cumulative record count', android_df.__len__(), 'records')

    print('Adding Eastings and Northings ...')
    android_df.reset_index(inplace=True)
    for i, row in android_df.iterrows():
        # print(i, '>>', row)
        E, N = transformer.transform(row['client_latitude'], row['client_longitude'])
        # print(i, '>> ', E, ':  ', N)
        android_df.loc[i, 'E'] = E
        android_df.loc[i, 'N'] = N
        if i % 100 == 0:
            print(i, 'of', android_df.__len__(), 'rows processed')

    # remove rows further north than (roughly) Newcastle (600km)
    android_df = android_df[android_df['N'] < 600000]
    # write this month's transformed file to csv.
    android_df.to_csv(ookladir + m + '.csv')


# Pandas convert columns DOESN'T work like this
# ook['E'], ook['N'] = ll_to_os(ook['client_longitude'], ook['client_latitude'])
# Probably slower, but iterating over the rows might be easier to code and it's a batch process so take a hit on perf.
