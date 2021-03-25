
"""
 _      ____   _____          _____ _____ _    _ _____            _______     __
| |    / __ \ / ____|   /\   / ____/ ____| |  | |  __ \     /\   / ____\ \   / /
| |   | |  | | |       /  \ | |   | |    | |  | | |__) |   /  \ | |     \ \_/ /
| |   | |  | | |      / /\ \| |   | |    | |  | |  _  /   / /\ \| |      \   /
| |___| |__| | |____ / ____ \ |___| |____| |__| | | \ \  / ____ \ |____   | |
|______\____/ \_____/_/    \_\_____\_____|\____/|_|  \_\/_/    \_\_____|  |_|

Investigate why location and start location have only ~.77 correlation.
Entire project is uploaded to https://github.com/jamescoombs3/ookla
"""
import pandas as pd
import xlrd
import seaborn as sns
import matplotlib.pyplot as plt
import glob
import numpy as np
import statsmodels.formula.api as smf

# define a directory to write any outputs
workdir = 'p:/ookla/pickle/'

# Pickle file was created as part of the wider analysis.
android_df = pd.read_pickle(workdir + 'android_1.pickle')
# Define a handy function to tell us how much memory is consumed by these dataframes and their shape
def sizeof(df):
    name = [x for x in globals() if globals()[x] is df][0]
    print('Dataframe name:', name)
    print('Shape:', df.shape)
    print('Memory consumed: {0:.2f} MB'.format(
        df.memory_usage().sum() / (1024 * 1024)
    ))

# Display size and memory consumption of the sample data.
sizeof(android_df)

# This was the original plot from objective_1
sns.set(rc={'figure.figsize': (8, 8)})
ax = sns.scatterplot(x='client_longitude', y='client_longitude_start', data=android_df)
# there are some outliers in the data but in UK longitude should range from about -8 to +2
ax.set_xlim(-8, 2)
ax.set_ylim(-8, 2)

# How well would that scatter improve if we dropped all records in which accuracy is either missing or > 20 (metres)?
# find out what these fields all do
# location_type	            object
# location_accuracy_a	    object
# location_age_a	        object
# location_type_start	    float64

# Copy all of these along with client lat/long and *_start versions to a new dataframe
cols = ['client_longitude', 'client_longitude_start', 'client_latitude', 'client_latitude_start',
        'location_type', 'location_accuracy_a', 'location_age_a', 'location_type_start']

and_clean = android_df[cols].copy()

"""
for c in cols[4:]:
    # print(eval(c))
    and_clean.c = pd.to_numeric(and_clean.c, errors='coerce').fillna(0).astype(np.int32)
    
never mind!     
"""
and_clean.location_type = pd.to_numeric(and_clean.location_type, errors='coerce').fillna(0).astype(np.int32)
and_clean.location_accuracy_a = pd.to_numeric(and_clean.location_accuracy_a, errors='coerce').fillna(0).astype(np.int32)
and_clean.location_age_a = pd.to_numeric(and_clean.location_age_a, errors='coerce').fillna(0).astype(np.int32)
and_clean.location_type_start = pd.to_numeric(and_clean.location_type_start, errors='coerce').fillna(0).astype(np.int32)

and_clean.drop(and_clean[and_clean.location_type != 1].index, inplace=True)
and_corr = and_clean[cols[:4]].corr()
print(and_corr)
and_corr.to_csv(workdir + 'and_corr.csv')

fig, ax = plt.subplots(figsize=(8, 8))
ax = sns.heatmap(and_clean[cols[:4]].corr(), ax=ax4,
                  vmin=-1, vmax=1, center=0, annot=True, square=True,
                  cmap=sns.diverging_palette(220, 20, n=200))
# fig.suptitle('Correlations', y=0.92);

sns.set(rc={'figure.figsize': (8, 8)})
ax = sns.scatterplot(x='client_longitude', y='client_longitude_start', data=and_clean)
# there are some outliers in the data but in UK longitude should range from about -8 to +2
ax.set_xlim(-8, 2)
ax.set_ylim(-8, 2)