import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
import numpy as np
import datetime

"""
  _____          _      _____ ____  _____         _______ ______ 
 / ____|   /\   | |    |_   _|  _ \|  __ \     /\|__   __|  ____|
| |       /  \  | |      | | | |_) | |__) |   /  \  | |  | |__   
| |      / /\ \ | |      | | |  _ <|  _  /   / /\ \ | |  |  __|  
| |____ / ____ \| |____ _| |_| |_) | | \ \  / ____ \| |  | |____ 
 \_____/_/    \_\______|_____|____/|_|  \_\/_/    \_\_|  |______|
                                                                 
This script follows on from a series of cleansing and shaping scripts the output of which is 
1) A 'coverage map' 
2) Ookla test data.  

The information on how to interpret the coverage map may be incorrect. This script creates an enhanced version 
of the coverage map lookup function with two extra arguments allowing a shift in both x and y axes.
An 11x11 heatmap is created for each offset (-100 to + 100 in increments of 10) to see which returns the best R**2 

"""

workdir = 'p:/ookla/pickle'
ook_df = pd.read_pickle(workdir + '/ookla.pickle')
map_df = pd.read_pickle(workdir + '/aug_map.pickle')

# create a new column containing a unique hash of lat/long. The minimum longitude is -8.096000 so
# can create a unique hash like this
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


# MODIFIED signal strength function. This version has additional parameters to 'tune' the x and y parameters
def RSRP(Er, Nr, xdelta, ydelta):
    cellsize = 50
    xllcorner = -8200
    yllcorner = 12600
    Er = Er + xdelta
    Nr = Nr + ydelta

    Ediv, r = divmod(Er, cellsize)
    Ediv = Ediv * cellsize

    Ndiv, r = divmod(Nr, cellsize)
    Ndiv = Ndiv * cellsize

    # Using the convention that x is for rows and y for columns, work out column
    x = int((Ediv - xllcorner) / cellsize)
    y = int((Ndiv - yllcorner) / cellsize)
    # Cartesian coordinates are conventionally (x, y). Pandas is more like "find the row, then find column"
    # this ends up with a vector (y, x) I have to write this comment to stop myself 'correcting' the next line!
    rsrp_val = map_df.iloc[y, x]
    # print('Debug info finding RSRP at', Er, Nr, ', Col:', x, 'Row', y, 'returns:', rsrp_val)
    return rsrp_val


"""
# FIRST VERSION - REMOVE FROM FINAL

# pandas.iloc can't write to a non-existent location so initialise with zeros
heatmap = pd.DataFrame(np.zeros((21, 21)))
for xx in range(-100, 101, 10):
    for yy in range(-100, 101, 10):
        ook_df['calib'] = ook_df.apply(lambda row: RSRP(row.E, row.N, xx, yy), axis=1)
        lm = smf.ols(formula='rsrp_a ~ calib', data=ook_df).fit()
        # This takes a while (500k values updated) so print the datetime to monitor progress
        print(datetime.datetime.now(), ' xx:yy =', xx, ':', yy, 'returns', lm.rsquared)
        heatmap.iloc[int(xx / 10 + 10), int(yy / 10 + 10)] = lm.rsquared


# That nested loop iterates 11x11 = 121 times, has~ 500k lookups in the inner loop and takes 2 hours to execute
# so first thing to do is write it to csv ;-)
heatmap.to_csv(workdir + '/heatmap.csv')
# because my heatmap is called heatmap and the axes are the indexes I can just do
ax = sns.heatmap(heatmap)

# hmmm that crashed it!
heatmap = pd.read_csv(workdir + '/heatmap.csv')
heatmap = heatmap.drop("Unnamed: 0", axis=1)

ax = sns.heatmap(heatmap, cmap='YlOrRd_r', cbar=False)

"""

# pandas.iloc can't write to a non-existent location so initialise with zeros
heatmap = pd.DataFrame(np.zeros((21, 21)))
columns = list(range(-100, 101, 10))
# set the column headers for empty dataframe
heatmap.columns = [columns]
# transpose it so the rows are named
heatmap = heatmap.T
# set the column headers for empty dataframe
heatmap.columns = [columns]
# iterate over all rows/columns
for xx in range(-100, 101, 10):
    for yy in range(-100, 101, 10):
        ook_df['calib'] = ook_df.apply(lambda row: RSRP(row.E, row.N, xx, yy), axis=1)
        lm = smf.ols(formula='rsrp_a ~ calib', data=ook_df).fit()
        # This takes a while (500k values updated) so print the datetime to monitor progress
        print(datetime.datetime.now(), ' xx:yy =', xx, ':', yy, 'returns', lm.rsquared)
        heatmap.iloc[int(xx / 10 + 10), int(yy / 10 + 10)] = lm.rsquared


# The above nested loop iterates 11x11 = 121 times, has~ 500k lookups in the inner loop and takes 2 hours to execute
# so first thing to do is write it to csv ;-)
heatmap.to_csv(workdir + '/heatmap.csv')

"""
# reload if necessary 
heatmap = pd.read_csv(workdir + '/heatmap.csv')
heatmap = heatmap.drop("Unnamed: 0", axis=1)
columns = list(range(-100, 101, 10))
heatmap.columns = [columns]
heatmap = heatmap.T
heatmap.columns = [columns]
heatmap = heatmap.T
"""

# Plot the results - 'out of the box' looks pretty good!
ax = sns.heatmap(heatmap)

# consider horizontal key and changing the palette
grid_kws = {"height_ratios": (.9, .05), "hspace": .3}
f, (ax, cbar_ax) = plt.subplots(2, gridspec_kw=grid_kws)
ax = sns.heatmap(heatmap, ax=ax,
                 cmap='YlOrRd_r',
                 cbar_ax=cbar_ax,
                 cbar_kws={"orientation": "horizontal"})

# find the maximum value
heatmap.max().max()  # this doesn't work! 

"""
  _____  _____ _____         _______ _____ _    _ 
 / ____|/ ____|  __ \     /\|__   __/ ____| |  | |
| (___ | |    | |__) |   /  \  | | | |    | |__| |
 \___ \| |    |  _  /   / /\ \ | | | |    |  __  |
 ____) | |____| | \ \  / ____ \| | | |____| |  | |
|_____/ \_____|_|  \_\/_/    \_\_|  \_____|_|  |_|
                                                  
From here below should be removed from final code to tidy up. 
(I miss Perl's __END__ directive!)            

"""



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
