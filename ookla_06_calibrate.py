import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
import numpy as np
import datetime
import matplotlib.pyplot as plt

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

Entire project is uploaded to https://github.com/jamescoombs3/ookla
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
# rename xRSRP to ensure not confused with the "production" RSRP function
def xRSRP(Er, Nr, xdelta, ydelta):
    # define variables relating to the headers for origin and cell size
    cellsize = 50
    xllcorner = -8200
    yllcorner = 12600

    # Adjust the actual location by the offset given as a pair of delta coordinates in the function arguments
    Er = Er + xdelta
    Nr = Nr + ydelta

    # convert from metres to pixels
    Ediv, r = divmod(Er, cellsize)
    Ediv = Ediv * cellsize
    Ndiv, r = divmod(Nr, cellsize)
    Ndiv = Ndiv * cellsize

    # Work out the column and row within the data file
    x = int((Ediv - xllcorner) / cellsize)
    y = int((Ndiv - yllcorner) / cellsize)
    # retrieve the value at this point in the (already loaded) dataframe 
    rsrp_val = map_df.iloc[y, x]
    # Debugging line. This generates ~500,000 lines of output so normally commented out!
    # print('Debug info finding RSRP at', Er, Nr, ', Col:', x, 'Row', y, 'returns:', rsrp_val)
    return rsrp_val


"""
Iterate over 'delta' values ranging from -100 to + 100 in increments of 10 and pass these to a modified version of the signal strength function. 
These value pairs are used to shift the original coordinates by varying amounts to create a temporary 'calib' column. Simple linear regression is
then used to see which 'offset' returns the best match. 

The 'calib' column is overwritten with each iteration because we don't want to create (21 x 21 =) 441 additional rows in the dataset!!
The r-square value is captured in an array called 'heatmap' which is then used to plot a heatmap which is used to determine the closest match.
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
        ook_df['calib'] = ook_df.apply(lambda row: xRSRP(row.E, row.N, xx, yy), axis=1)
        lm = smf.ols(formula='rsrp_a ~ calib', data=ook_df).fit()
        # This takes a while (500k values updated) so print the datetime to monitor progress
        print(datetime.datetime.now(), ' xx:yy =', xx, ':', yy, 'returns', lm.rsquared)
        # REMEMBER! pandas indexes rows then columns so the Cartesian is [y, x]
        heatmap.iloc[int(yy / 10 + 10), int(xx / 10 + 10)] = lm.rsquared


# The above nested loop iterates 21x21 = 441 times, has~ 500k lookups in the inner loop and takes 2 hours to execute
# so first thing to do is write it to csv ;-)
# It'd be more intuitive if the y-axis is flipped so north is upwards! .iloc[::-1] reverses the rows
heatmap.iloc[::-1].to_csv(workdir + '/heatmap.csv')
heatmap = heatmap.iloc[::-1]

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

# consider horizontal key and changing the palette https://seaborn.pydata.org/generated/seaborn.heatmap.html
grid_kws = {"height_ratios": (.9, .05), "hspace": .3}
f, (ax, cbar_ax) = plt.subplots(2, gridspec_kw=grid_kws)
ax = sns.heatmap(heatmap, ax=ax,
                 cmap='YlOrRd_r',
                 cbar_ax=cbar_ax,
                 cbar_kws={"orientation": "horizontal"})


grid_kws = {"height_ratios": (.9, .05), "hspace": .3}
f, (ax, cbar_ax) = plt.subplots(2, gridspec_kw=grid_kws)
ax = sns.heatmap(heatmap[3:7], ax=ax,
                 annot=True, fmt='.3g',
                 cmap='YlOrRd_r',
                 cbar_ax=cbar_ax,
                 cbar_kws={"orientation": "horizontal"})


# Check we have the correct maximum value
# print(heatmap.min().min())
print(heatmap.max().max())
print(heatmap.iloc[5, 7])


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

# check a hunch ...
xx = -25
yy = 50

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

