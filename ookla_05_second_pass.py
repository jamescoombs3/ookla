import pandas as pd
import numpy as np

"""
This script carries out final preparation of the coverage map and Ookla data  

  _____ ______      ________ _____            _____ ______ 
 / ____/ __ \ \    / /  ____|  __ \     /\   / ____|  ____|
| |   | |  | \ \  / /| |__  | |__) |   /  \ | |  __| |__   
| |   | |  | |\ \/ / |  __| |  _  /   / /\ \| | |_ |  __|  
| |___| |__| | \  /  | |____| | \ \  / ____ \ |__| | |____ 
 \_____\____/   \/   |______|_|  \_\/_/    \_\_____|______|
                                                           
COVERAGE MAP
============
This section:  
1) Loads the first 12,000 lines of the August coverage map. (This is the max which can be loaded but 
   covers 93.7% of the sample data.)
2) Changes the data from floats to integer. This reduces memory consumption from 1.2GB to 600MB 
3) The lowest actual value is -127 dBm but no signal at all is recorded as 0 (which as loss is being measured would
   represent a perfect signal!) Changed zeros to -128 to prevent them distorting any predictions.  
4) Rewrites the coverage map as a pickle file.  


"""

workdir = 'p:/ookla/pickle'
rasterfile = 'P:/ookla/4G_RSS/2021-01-08-AW_H3G_LTE1800-1st-Best-RSS.asc'
# rasterfile = 'P:/ookla/_aug_rev_12k' < this
# testrasterfile = 'P:/ookla/_a_jan21-rev-2k.txt'  # this has just 2,000 rows

# define a function to show shape and and memory consumption of dataframe
def sizeof(df):
    name = [x for x in globals() if globals()[x] is df][0]
    print('Dataframe name:', name)
    print('Shape:', df.shape)
    print('Memory consumed: {0:.2f} MB'.format(
        df.memory_usage().sum() / (1024 * 1024)
    ))


# Run task manager, kill your browsers and look at memory consumption before running this!
# file contains 22830 rows (checked with wc -l) and we want to read the last 12k only
rf = pd.read_csv(rasterfile, delim_whitespace=True, header=None, low_memory=False, skiprows=22830 - 12000)

print(sizeof(rf))
"""
Dataframe name: rf
Shape: (12000, 13561)
Memory consumed: 1241.55 MB
"""

print('mean values in the dataframe are', rf.mean().mean())
# returns
# Out[22]: -44.869449757884134

# converting the 'raster' file dataframe to integer values cuts memory consumption by half!
rf = rf.astype(int)
print('mean values in the dataframe are (still)', rf.mean().mean())
print(sizeof(rf))

rf = rf.replace(0, -128)
rf.to_pickle(workdir + '/aug_map.pickle')

"""
  _____ ______ _____ ____  _   _ _____         _____         _____ _____ 
 / ____|  ____/ ____/ __ \| \ | |  __ \       |  __ \ /\    / ____/ ____|
| (___ | |__ | |   | |  | |  \| | |  | |______| |__) /  \  | (___| (___  
 \___ \|  __|| |   | |  | | . ` | |  | |______|  ___/ /\ \  \___ \\___ \ 
 ____) | |___| |___| |__| | |\  | |__| |      | |  / ____ \ ____) |___) |
|_____/|______\_____\____/|_| \_|_____/       |_| /_/    \_\_____/_____/ 

     
Final Ookla data preparation
============================
Data prep is always an iterative process. This second tranche of filtering will takes as its input 
the concatenated monthly files from May, Jun, Jul, Aug and remove: 
1)  Rows further north than 600,000 (600km). This removes 2,914 of 46810 records = 6.225%
2)  Rows where location accuracy is zero. It transpires that this means unknown rather than zero! 
3)	Select only rows where location_type_start is 1 (GPS rather than GeoIP)
4)	Remove rows where location_age_a is older than ten minutes. (10 x 60 x 1000 milliseconds)
5)  Rewrite the 24x pre_connection_type codes as either WiFi, Cellular or unknown then use get_dummies to create cats.  
6)  Rewrite the Ookla data as a pickle file.

                                                                       
"""

# datafile = 'P:/ookla/2020-05.csv'           # for testing
datafile = 'P:/ookla/2020-may2aug.csv'      # for real!
ook_df = pd.read_csv(datafile, low_memory=False)

# 1)  Rows further north than 600,000 (600km). This removes 2,914 of 46810 records = 6.225%
# 1) Rows further north than 600,000 (600km)
# The first pass filter saves only the Ookla files covering the southernmost 600km of the UK.
# This removes 2,914 of 46810 records or about 6.225%.
# Confirm that all the tests are below 600km North
print('Max Northings value is', ook_df['N'].max())

# Data happens to have a couple of unused columns so rather than delete and create rename these as
# RSRP (signal strength) and WiFi (Boolean categorical for WiFi connection)
ook_df = ook_df.rename(columns={'Unnamed: 0': 'RSRP', 'index': 'WiFi'})
print('starting shape', ook_df.shape)

# 2)  Rows where location accuracy is zero. It transpires that this means unknown rather than zero!

# It turns out that location accuracy of "0" doesn't mean what you might think!
# Remove all the rows where this is zero!
print('removing location accuracy = 0 (which does not mean what you would expect!)')
ook_df = ook_df[ook_df['location_accuracy_a'] > 0]
print('Shape is now', ook_df.shape)

# 3)	Select only rows where location_type_start is 1 (GPS rather than GeoIP)
# 1=GPS
# 2=GeoIP
print('Selecting only rows which use GPS location')
ook_df = ook_df[ook_df['location_type_start'] == 1]
print('Shape is now', ook_df.shape)

# 4)	Remove rows where location_age_a is older than ten minutes. (10 x 60 x 1000 milliseconds)
print('Removing any location_age_a older than ten minutes.')
ook_df.location_age_a = pd.to_numeric(ook_df.location_age_a, errors='coerce').fillna(0).astype(np.int64)
ook_df = ook_df[ook_df['location_age_a'] < 10 * 60 * 1000]
print('Shape is now', ook_df.shape)

# 5)  Rewrite the 24x pre_connection_type codes as {WiFi|Cellular|Unknown} then get_dummies to create cats.
# Full metadata description below but 2 = WiFi, all else is some type of cellular
ook_df['WiFi'] = np.where(ook_df.pre_connection_type == 2, 1, 0)

# ook_df['WiFi'].mean()

# 6)  Rewrite Ookla data as a pickle file.
ook_df.to_pickle(workdir + '/ookla.pickle')


