import pandas as pd


"""
Problems loading this file mean can't load all of it. 
"""

rasterfile = 'P:/ookla/_aug_rev_12k'
# testrasterfile = 'P:/ookla/_a_jan21-rev-2k.txt'  # this has just 2,000 rows
# rft = pd.read_csv(testrasterfile, delim_whitespace=True, header=None, low_memory=False)
# t = pd.read_csv('P:/ookla/_sample.csv', header=None, low_memory=False)

# define a function to show shape and and memory consumption of dataframe
def sizeof(df):
    name = [x for x in globals() if globals()[x] is df][0]
    print('Dataframe name:', name)
    print('Shape:', df.shape)
    print('Memory consumed: {0:.2f} MB'.format(
        df.memory_usage().sum() / (1024 * 1024)
    ))

# Run task manager, kill your browsers and look at memory consumption before running this!
rf = pd.read_csv(rasterfile, delim_whitespace=True, header=None, low_memory=False)


print(sizeof(rf))
"""
Dataframe name: rf
Shape: (12000, 13561)
Memory consumed: 1241.55 MB
"""

print('mean values in the dataframe are', rf.mean().mean())
# returns
# Out[22]: -44.869449757884134

# converting the 'raster' file dataframe to integer cuts memory consumption by half!

rf = rf.astype(int)
print('mean values in the dataframe are (still)', rf.mean().mean())
print(sizeof(rf))

"""
# Standard pedagogic approach to problem solving is to alternate between the general and special cases.  
# This 'getting my head around it' code fragment works out what value is returned when looking up the  
# location of a specific site at (472648, 173228) which ought to be pretty high when standing underneath
# the transmitter! 

# Set the coordinates:  
E = 472648
N = 173228

# Set the resolution and round down to the SW corner of the square 
cellsize = 50
Ediv, r = divmod(E, cellsize)
Ediv = Ediv * cellsize
Ndiv, r = divmod(N, cellsize)
Ndiv = Ndiv * cellsize

# Set the offset specified in the header lines of the 'raster' file. 
xllcorner = -8200
yllcorner = 12600

# Using the convention that x is for rows and y for columns, work out column
x = int((Ediv - xllcorner) / cellsize)
y = int((Ndiv - yllcorner) / cellsize)

# Use these x,y values to return the value at that point in the file
print('4G RSRP signal strength at the Kings Road site are, Col:', x, 'Row', y, 'returns:', rf.iloc[y, x])
"""

# Using the above special case, create a generic function which returns a signal strength
# given full precision E, N coordinates.


def RSRP(Er, Nr):
    cellsize = 50
    xllcorner = -8200
    yllcorner = 12600

    Ediv, r = divmod(Er, cellsize)
    Ediv = Ediv * cellsize

    Ndiv, r = divmod(Nr, cellsize)
    Ndiv = Ndiv * cellsize

    # Using the convention that x is for rows and y for columns, work out column
    x = int((Ediv - xllcorner) / cellsize)
    y = int((Ndiv - yllcorner) / cellsize)
    rsrp_val = rf.iloc[y, x]
    # print('Debug info, Col:', x, 'Row', y, 'returns:', rsrp_val)
    return rsrp_val


# Next challenge on memory is to load the data file and enrich it with hat will be the response variable
# in a linear regression analysis
datafile = 'P:/ookla/2020-05.csv'           # for testing
datafile = 'P:/ookla/2020-may2aug.csv'      # for real!
df = pd.read_csv(datafile, low_memory=False)

# shape
# Out[29]: (46810, 68)
# may as well filter in Excel since I have it open!
# filtering 600,000 and over removes 2,914 of 46810 records = 6.225%
# new shape
# Out[32]: (43896, 68)

# get rid of an unused column by renaming it y (the response variable in subsequent OLS
df = df.rename(columns={'Unnamed: 0': 'y'})

# having created a function, is it possible to do it all in an anonymous lambda function?
df['y'] = df.apply(lambda row: RSRP(row.E, row.N), axis=1)

df.to_csv('P:/ookla/2020-may2aug-y.csv')


# restartable from here

# TO DO <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# Would be useful to categorise tests as cellular, WiFi or unknown. Metadata description
#  0 = Unknown
#  1 = Cell,
#  2 = Wi-Fi,*************
#  3 = GPRS,  (cell)
#  4 = EDGE,(cell)
#  5 = UMTS,(cell)
#  6 = CDMA,  (cell)
#  7 = EVDO0, (WiFi)
#  8 = EVDOA,  (WiFi)
#  9 = OnexRTT,  (cell)
#  10 = HSDPA,   (cell)
#  11 = HSPA,  (cell)
#  12 = IDEN,  (cell)
#  13 = EHRPD,  (cell)
#  14 = EVDOB,  (cell)
#  15 = LTE,  (cell)
#  16 = HSUPA,  (cell)
#  17 = HSPAP,  (cell)
#  18 = GSM,  (cell)
#  19 = TDSCDMA,  (cell)
#  20 = IWLAN,  WIFI ************
#  21 = LTE-CA   (cell)
# This specific data 110k rows contains type 24 and there are a lot of them!
# one option is to code 2 & 20 as WiFi, 0 as Unknown and everything else as 'cellular'

df = pd.read_csv('P:/ookla/2020-may2aug-y.csv', low_memory=False)
# It turns out that location accuracy of "0" doesn't mean what you might think!
# Remove all the rows where this is zero!
df = df[df['location_accuracy_a'] > 0]

# ... or maybe it does! location_type_start is
# 1=GPS
# 2=GeoIP

df = pd.read_csv('P:/ookla/2020-may2aug-y.csv', low_memory=False)
# It turns out that location accuracy of "0" doesn't mean what you might think!
# Remove all the rows where this is zero!
df = df[df['location_type_start'] == 1]

# remove any location_age_a older than ten minutes. (10 x 60 x 1000 milliseconds)
df = df[df['location_age_a'] < 10 * 60 * 1000]

"""
THIS BIT NEEDS TO BE POST RSRP lookup to capture any signal strengths of zero 
(also for eg capture what happens if we take mean of 
0,    -120
-122, -123
This ends up as -366/4 = -91 which is really good RSRP !


# there are some reported signal strengths of zero just outside coverage.
df = df[df['y'] < 0]

"""

df.to_csv('P:/ookla/2020-may2aug-yy.csv')

import statsmodels.formula.api as smf
"""
import numpy as np
from io import StringIO
import matplotlib.pyplot as plt
import seaborn as sns
# from scipy.stats import gaussian_kde
from scipy.stats import truncnorm

A minimal example of OLS regression in Python to return similar output to R 

"""

# Example
# lm = smf.ols(formula='std_Verbal ~ Verbal + age_days', data=df).fit()

lm = smf.ols(formula='y ~ pre_connection_type + test_method_a + data_connection_type_a + wifi_frequency_mhz_a + location_accuracy_a + rsrp_a + device_ram_a + device_storage_a + altitude_a + vertical_accuracy_a', data=df).fit()

print(lm.summary())
print(lm.pvalues)
print(lm.params)


lm = smf.ols(formula='y ~ rsrp_a', data=df).fit()

print(lm.summary())
print(lm.pvalues)
print(lm.params)










"""
  _____  _____ _____         _______ _____ _    _ 
 / ____|/ ____|  __ \     /\|__   __/ ____| |  | |
| (___ | |    | |__) |   /  \  | | | |    | |__| |
 \___ \| |    |  _  /   / /\ \ | | | |    |  __  |
 ____) | |____| | \ \  / ____ \| | | |____| |  | |
|_____/ \_____|_|  \_\/_/    \_\_|  \_____|_|  |_|
                                                  
          


"""




# To return the value for King's road (calculated in raster-calcs.xlsx!Reading cells F72, G72)
print(rf.iloc[3213, 9616])


# To return individual values, for example a slice of this dataframe
for x in range(3210, 3213):
    print(rf.iloc[x, 9616])

for x in range(3210, 3213):
    for y in range(9614,9617):
        print(rf.iloc[x, y])







"""
RAN raster files contain six rows of meta data as follows: 

ncols      13561
nrows    22824
xllcorner              -8200
yllcorner              12600
cellsize  50
nodata_value     0

For distance calcs a cartesian coordinate system is much easier (Eastings/Northings) but most GIS tools
use Long/Lat polar coordinates so need to convert. 

The values above explain that each 'pixel' is 50m square 

For one off testing this site is good at converting between both (and postcodes) so for eg RG1 8DJ (the office)
-0.97332352 Long, 51.461702 Lat
... which should convert to 
471422E 174136N 
The value we're looking for should be located in row  
"""

raster = 'C:/1drive/OneDrive - Three/jumpserver/H3G/4G_Coverage\H3G_4G\AW_H3G_LTE1800/AW_H3G_LTE1800-1st-Best-Cell.txt'

# open the raster file using space delimiter. Skip six first lines.
"""
BIG problem the file is 1GB and won't load :-( 
Here's some methods which don't work. 
rr = pd.read_csv(raster, delim_whitespace=True, chunksize=1000, skiprows=6, low_memory=False)
rr = pd.read_csv(raster, delim_whitespace=True, skiprows=6)
rr = pd.read_csv(raster, delim_whitespace=True, skiprows=6, low_memory=False)
Remove the first six lines of metadata from the raster file  
rr = pd.read_csv(raster, delim_whitespace=True, low_memory=False)
... still doesn't work. 
"""



rasterfile = 'P:/ookla/april-2020-ab'
rf = pd.read_csv(rasterfile, delim_whitespace=True)

r = 'C:/1drive/OneDrive - Three/jumpserver/H3G/4G_Coverage\H3G_4G\AW_H3G_LTE1800/4G_Scell_04000.txt'
rr = pd.read_csv(r, delim_whitespace=True)

r = 'C:/1drive/OneDrive - Three/jumpserver/H3G/4G_Coverage\H3G_4G\AW_H3G_LTE1800/4G_RSS_14000.txt'
r = 'C:/1drive/OneDrive - Three/jumpserver/H3G/4G_Coverage\H3G_4G\AW_H3G_LTE1800/4G_Scell_14000.txt'
rr = pd.read_csv(r, delim_whitespace=True)


r = 'C:/1drive/OneDrive - Three/jumpserver/H3G/4G_Coverage\H3G_4G\AW_H3G_LTE1800/4G_RSS_02000.txt'
rr = pd.read_csv(r, delim_whitespace=True)

import zipfile
import pandas as pd
# not sure if needed.
import numpy as np

raster = 'C:/1drive/OneDrive - Three/jumpserver/H3G/4G_Coverage\H3G_4G\AW_H3G_LTE1800/AW_H3G_LTE1800-1st-Best-Cell.txt'
import dask.dataframe as ddf
r = ddf.read_csv(raster, delim_whitespace=True,)

rdf = r.compute().reset_index(drop=True)
