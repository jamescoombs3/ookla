import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf

"""
This script follows on from a series of cleansing and shaping scripts the output of which is 
1) A 'coverage map' 
2) Ookla test data.  

Entire project is uploaded to https://github.com/jamescoombs3/ookla
"""

workdir = 'p:/ookla/pickle'
ook_df = pd.read_pickle(workdir + '/ookla.pickle')
map_df = pd.read_pickle(workdir + '/aug_map.pickle')


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

    # Adjust the location by the values discovered during calibration
    Er = Er - 30
    Nr = Nr + 50

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
    rsrp_val = map_df.iloc[y, x]  # Documented in RasterCalcsNotes.docx
    # print('Debug info finding RSRP at', Er, Nr, ', Col:', x, 'Row', y, 'returns:', rsrp_val)
    return rsrp_val

# having created a function, is it possible to do it all in an anonymous lambda function?
ook_df['RSRP'] = ook_df.apply(lambda row: RSRP(row.E, row.N), axis=1)

formula = 'rsrp_a ~ RSRP'
print('Testing', formula)
lm = smf.ols(formula=formula, data=ook_df).fit()
print(lm.summary())

offsets = [["x1y1", -50, -50], ["x2y1", 0, -50], ["x3y1", 50, -50], ["x4y1", 100, -50],
           ["x1y2", -50,   0], ["x2y2", 0,   0], ["x3y2", 50,   0], ["x4y2", 100,   0],
           ["x1y3", -50,  50], ["x2y3", 0,  50], ["x3y3", 50,  50], ["x4y3", 100,  50],
           ["x1y4", -50, 100], ["x2y4", 0, 100], ["x3y4", 50, 100], ["x4y4", 100, 100]]

for tup in offsets:
    print('Calculating values for column', tup[0])
    ook_df[tup[0]] = ook_df.apply(lambda row: RSRP(row.E + tup[1], row.N + tup[2]), axis=1)

# Write to a pickle file
ook_df.to_pickle(workdir + '/ook_df_final.pickle')
# ... and because I'm paranoid ...
ook_df.to_csv(workdir + '/ook_df_final.csv')
ook_df.head(2000).to_csv(workdir + '/ook_df_final2k.csv')

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

'''
__      __     _____  _____          _   _  _____ ______ 
\ \    / /\   |  __ \|_   _|   /\   | \ | |/ ____|  ____|
 \ \  / /  \  | |__) | | |    /  \  |  \| | |    | |__   
  \ \/ / /\ \ |  _  /  | |   / /\ \ | . ` | |    |  __|  
   \  / ____ \| | \ \ _| |_ / ____ \| |\  | |____| |____ 
    \/_/    \_\_|  \_\_____/_/    \_\_| \_|\_____|______|
                                                         
This section looks at multiple tests run at same location to establish the variance 
Need to load ook_df and map_df create the function and populate RSRP with valid values as above before running this
'''

# The minimum longitude is -8.096000 so this creates a simple unique hash of location
ook_df['lochash'] = ook_df.apply(lambda row: row.client_latitude + (row.client_longitude + 10) * 100000, axis=1)

# find the most common values
print(ook_df['lochash'].value_counts().head())

# use the value returned to create a dataframe of 1675 all run at the same location (someone was busy!)
varies = ook_df[ook_df['lochash'] == 836954.632]

ax = sns.histplot(data=varies, x='rsrp_a', kde=True)

print(varies['rsrp_a'].describe(), '\n skew',
      varies['rsrp_a'].skew(), '\n kurtosis',
      varies['rsrp_a'].kurtosis()
      )

# THIS CODE NEEDS TIDYING UP !!

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

