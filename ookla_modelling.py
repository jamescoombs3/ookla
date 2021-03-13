import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

"""
import statsmodels.formula.api as smf
import xlrd
import matplotlib.pyplot as plt
import glob
import numpy as np
"""

"""
This script follows on from a series of cleansing and shaping scripts the output of which is 
1) A 'coverage map' 
2) Ookla test data.  


"""

workdir = 'p:/ookla/pickle'
ook_df = pd.read_pickle(workdir + '/ookla.pickle')
map_df = pd.read_pickle(workdir + '/aug_map.pickle')

# To potentially investigate locations with more than n samples create a new column containing a unique location hash
# The minimum longitude is -8.096000 so this works
ook_df['lochash'] = ook_df.apply(lambda row: row.client_latitude + (row.client_longitude + 10) * 100000, axis=1)

# define a function to show shape and and memory consumption of dataframe
def sizeof(df):
    name = [x for x in globals() if globals()[x] is df][0]
    print('Dataframe name:', name)
    print('Shape:', df.shape)
    print('Memory consumed: {0:.2f} MB'.format(
        df.memory_usage().sum() / (1024 * 1024)
    ))

print(sizeof(map_df))
print(sizeof(ook_df))


# function to return the signal strength at a given Eastings/Northings location
def RSRP(Er, Nr):
    cellsize = 50
    xllcorner = -8200
    yllcorner = 12600

    # Implement floor function to round down to multiple of 50m
    Ediv, r = divmod(Er, cellsize)
    Ediv = Ediv * cellsize

    Ndiv, r = divmod(Nr, cellsize)
    Ndiv = Ndiv * cellsize

    # Using the convention that x is for rows and y for columns, work out column
    x = int((Ediv - xllcorner) / cellsize)
    y = int((Ndiv - yllcorner) / cellsize)
    # Cartesian coordinates are by convention (x, y) but this is accessing a dataframe which conceptually is
    # more like, "find the row then find the column"
    rsrp_val = map_df.iloc[y + 1, x - 1]  # Documented in RasterCalcsNotes.docx
    # print('Debug info finding RSRP at', Er, Nr, ', Col:', x, 'Row', y, 'returns:', rsrp_val)
    return rsrp_val

# having created a function, is it possible to do it all in an anonymous lambda function?
ook_df['RSRP'] = ook_df.apply(lambda row: RSRP(row.E, row.N), axis=1)

formula = 'rsrp_a ~ RSRP'
print('Testing', formula)
lm = smf.ols(formula=formula, data=ook_df).fit()
print(lm.summary())

offsets = [['off_N', 0, 50],
           ['off_NE', 50, 50],
           ['off_E', 50, 0],
           ['off_SE', 50, -50],
           ['off_S', 0, -50],
           ['off_SW', -50, -50],
           ['off_W', -50, 0],
           ['off_NW', -50, 50]]

for tup in offsets:
    # print('tup', tup)
    # print('calculating', tup[0])
    ook_df[tup[0]] = ook_df.apply(lambda row: RSRP(row.E + tup[1], row.N + tup[2]), axis=1)
    # print(sizeof(ook_df))
    formula = 'rsrp_a ~ ' + tup[0]
    print('Testing', formula)
    lm = smf.ols(formula=formula, data=ook_df).fit()
    print(lm.rsquared)
    # z = input('press enter for next')   # not needed if just printing rsquared


formula = 'rsrp_a ~ RSRP'
print('Testing', formula)
lm = smf.ols(formula=formula, data=ook_df).fit()
print(lm.rsquared)

# see if we get different results with WiFi brought back in.

for tup in offsets:
    formula = 'rsrp_a ~ WiFi + ' + tup[0]
    print('Testing', formula)
    lm = smf.ols(formula=formula, data=ook_df).fit()
    print(lm.rsquared)
    # z = input('press enter for next')   # not needed if just printing rsquared


formula = 'rsrp_a ~ WiFi + RSRP'
print('Testing', formula)
lm = smf.ols(formula=formula, data=ook_df).fit()
print(lm.rsquared)

# same ("focus") results although obviously better R^2 values.

ook_df.to_pickle(workdir + '/may-aug+offset.pickle')
ook_df.to_csv(workdir + '/may-aug+offset.csv')

"""
 _____ _   _ _______ ______ _____  _____   ____  _            _______ ______ 
|_   _| \ | |__   __|  ____|  __ \|  __ \ / __ \| |        /\|__   __|  ____|
  | | |  \| |  | |  | |__  | |__) | |__) | |  | | |       /  \  | |  | |__   
  | | | . ` |  | |  |  __| |  _  /|  ___/| |  | | |      / /\ \ | |  |  __|  
 _| |_| |\  |  | |  | |____| | \ \| |    | |__| | |____ / ____ \| |  | |____ 
|_____|_| \_|  |_|  |______|_|  \_\_|     \____/|______/_/    \_\_|  |______|
                                                                             
This is where we implement the first algorithm! 
Start by using a special case. This is the second row in the dataframe
E = 472553.9442	
N = 174296.4146

1. Work out the offset to the central 'RSRP' tile
2. Use that to work out the distance to ALL tiles (including RSRP) by iterating over the tuple
3. Plug those values into the formula 

Second row is ook_df.iloc[1]

"""

# 1. Work out the offset to the central 'RSRP' tile
e = ook_df.iloc[1]['E']
n = ook_df.iloc[1]['N']
cellsize = 50
Ediv, Er = divmod(e, cellsize)
Er = 25 - Er

Ndiv, Nr = divmod(n, cellsize)
Nr = 25 - Nr

# 2. Use that to work out the distance to ALL tiles (including RSRP) by iterating over the tuple
# Do centre tile first (not in tuple) using pythagoras
# RSRP_r = (Er **2 + Nr ** 2) ** 0.5
top = ook_df.iloc[1]['RSRP']  # this is the dBm for centre tile ("top" of the fraction)
bottom = (Er **2 + Nr ** 2)   # this is r^2 for the centre tile ("bottom" of the fraction)
frac = top / bottom
frac2 = 1 / bottom
print('frac is', frac)
print('frac2 is', frac2)
total = frac
total2 = frac2

for tup in offsets:
    print(tup)
    # r = (Er + (tup[1]) **2 + (Nr + tup[2]) ** 2) ** 0.5
    top = top + ook_df.iloc[1][tup[0]]
    bottom = bottom + (Er + (tup[1]) ** 2 + (Nr + tup[2]))
    frac = top / bottom
    frac2 = 1 / bottom
    print('frac is', frac)
    print('frac2 is', frac2)
    total = total + frac
    total2 = total2 + frac2
    print('total is', total)
    print('total2 is', total2)

for tup in offsets:
    print(tup)
    print(ook_df.iloc[1][tup[0]])




# 3. Plug those values into the formula








# OK so let's try something totally crazy. What if my RSRP function had slipped by 50m in any direction?
print('Adding N')
ook_df['RSRPN'] = ook_df.apply(lambda row: RSRP(row.E, row.N + 50), axis=1)
print(sizeof(ook_df))
formula = 'rsrp_a ~ RSRPN'
print('Testing', formula)
lm = smf.ols(formula=formula, data=ook_df).fit()
print(lm.summary())

print('Adding NE')
ook_df['RSRPNE'] = ook_df.apply(lambda row: RSRP(row.E + 50, row.N + 50), axis=1)
print(sizeof(ook_df))

print('Adding E')
ook_df['RSRPE'] = ook_df.apply(lambda row: RSRP(row.E + 50, row.N), axis=1)
print(sizeof(ook_df))

print('Adding SE')
ook_df['RSRPSE'] = ook_df.apply(lambda row: RSRP(row.E + 50, row.N - 50), axis=1)
print(sizeof(ook_df))

print('Adding S')
ook_df['RSRPS'] = ook_df.apply(lambda row: RSRP(row.E, row.N - 50), axis=1)
print(sizeof(ook_df))

print('Adding SW')
ook_df['RSRPSW'] = ook_df.apply(lambda row: RSRP(row.E - 50, row.N - 50), axis=1)
print(sizeof(ook_df))

print('Adding W')
ook_df['RSRPW'] = ook_df.apply(lambda row: RSRP(row.E - 50, row.N), axis=1)
print(sizeof(ook_df))

print('Adding NW')
ook_df['RSRPNW'] = ook_df.apply(lambda row: RSRP(row.E - 50, row.N + 50), axis=1)
print(sizeof(ook_df))

points = ['RSRPN', 'RSRPNE', 'RSRPE', 'RSRPSE', 'RSRPS', 'RSRPSW', 'RSRPW', 'RSRPNW']
for p in points:
    formula = 'rsrp_a ~ ' + p
    print('Testing', formula)
    lm = smf.ols(formula=formula, data=ook_df).fit()
    print(lm.summary())
    z = input('press enter for the next')

print('Adding NW2')
ook_df['NW2'] = ook_df.apply(lambda row: RSRP(row.E - 100, row.N + 50), axis=1)
print(sizeof(ook_df))

print('Adding NWN')
ook_df['NWN'] = ook_df.apply(lambda row: RSRP(row.E - 50, row.N + 100), axis=1)
print(sizeof(ook_df))

print('Adding N2')
ook_df['N2'] = ook_df.apply(lambda row: RSRP(row.E, row.N + 100), axis=1)
print(sizeof(ook_df))

print('Adding NWW')
ook_df['NWW'] = ook_df.apply(lambda row: RSRP(row.E - 100, row.N + 50), axis=1)
print(sizeof(ook_df))

print('Adding W2')
ook_df['W2'] = ook_df.apply(lambda row: RSRP(row.E - 100, row.N), axis=1)
print(sizeof(ook_df))

points = ['NW2', 'NWN', 'N2', 'NWW', 'W2']
for p in points:
    formula = 'rsrp_a ~ ' + p
    print('Testing', formula)
    lm = smf.ols(formula=formula, data=ook_df).fit()
    print(lm.summary())
    z = input('press enter for the next')



# ook_df.to_csv(workdir + '/may-aug-2.csv')

lm = smf.ols(formula='rsrp_a ~ RSRP + WiFi + test_method_a + data_connection_type_a + wifi_frequency_mhz_a + location_accuracy_a + device_ram_a + device_storage_a ', data=ook_df).fit()

print(lm.summary())
print(lm.pvalues)
print(lm.params)




# Split into 80% for training set and 20% for testing set to test accuracy of models
from sklearn.model_selection import train_test_split
ook_plot_df, ook_rem_df = train_test_split(ook_df, test_size=0.998, random_state=0)

sns.set(rc={'figure.figsize': (12, 12)})
# ax = sns.scatterplot(x='RSRP', y='rsrp_a', data=ook_plot_df, hue='WiFi')
# there are some outliers in the data but in UK longitude should range from about -8 to +2

# Instead, use lmplot which automatically adds linear regression lines for each hue
ax = sns.lmplot(x='RSRP', y='rsrp_a', data=ook_plot_df, hue='WiFi', markers=["x", "+"])
# ax.set(ylim=(0, None))
ax.set(xlim=(-130, -60))
ax.set(ylim=(-135, -55))
ax.savefig('p:/ookl/plots/lmplot_450dpi.png', dpi=450)

# remove records with RSRP of -128
ook_df = ook_df[ook_df['RSRP'] > -128]



lm = smf.ols(formula='rsrp_a ~ WiFi + RSRP', data=ook_df).fit()

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
