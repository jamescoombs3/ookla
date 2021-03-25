
"""
  ____   ____  _  ___                _____         __  __ _____  _      ______
 / __ \ / __ \| |/ / |        /\    / ____|  /\   |  \/  |  __ \| |    |  ____|
| |  | | |  | | ' /| |       /  \  | (___   /  \  | \  / | |__) | |    | |__
| |  | | |  | |  < | |      / /\ \  \___ \ / /\ \ | |\/| |  ___/| |    |  __|
| |__| | |__| | . \| |____ / ____ \ ____) / ____ \| |  | | |    | |____| |____
 \____/ \____/|_|\_\______/_/    \_\_____/_/    \_\_|  |_|_|    |______|______|

Analysis of the actual Ookla data
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
workdir = 'p:/ookla/workingdir/'

# define location of the raw data
ookladir = 'P:/ookla/'
# define a RE to load just the 12th day of each month in 2020 (avoids all outliers)
android_zips = glob.glob(ookladir + 'android_2020*12.zip')    # eg android_2020-01-12.zip

android_df = pd.DataFrame
for zipf in android_zips:
    print('checking', zipf)
    ook = pd.read_csv(zipf, compression='zip', header=0, low_memory=False)
    # appending to an empty dataframe doesn't work, get around this with try/except
    # first time try will fail and the except initialises the dataframe with contents of the first zip file
    # subsequent attempts the try will append the contents of the other zip file
    try:
        android_df = android_df.append(ook)
    except:
        android_df = ook

    print('so far', android_df.__len__(), 'records')

# took me *ages* to discover not doing this was a problem!
android_df.reset_index(drop=True, inplace=True)

# make a copy of the dataframes as frequently have memory problems
android_df.to_pickle(workdir + 'android_1.pickle')

"""
Reload if necessary 
android_df = pd.read_pickle(workdir + 'android_1.pickle')
"""

# Define function to tell us how much memory is consumed by these dataframes and their shape
def sizeof(df):
    name = [x for x in globals() if globals()[x] is df][0]
    print('Dataframe name:', name)
    print('Shape:', df.shape)
    print('Memory consumed: {0:.2f} MB'.format(
        df.memory_usage().sum() / (1024 * 1024)
    ))


# Display size and memory consumption of the sample data.
sizeof(android_df)

"""
 _   _ _    _ __  __ ______ _____  _____ _____          _      
| \ | | |  | |  \/  |  ____|  __ \|_   _/ ____|   /\   | |     
|  \| | |  | | \  / | |__  | |__) | | || |       /  \  | |     
| . ` | |  | | |\/| |  __| |  _  /  | || |      / /\ \ | |     
| |\  | |__| | |  | | |____| | \ \ _| || |____ / ____ \| |____ 
|_| \_|\____/|_|  |_|______|_|  \_\_____\_____/_/    \_\______|
Analyse the numerical data to potentially reduce dimensionality                                                             

Potential data validation methods include ...
android_df.info(verbose=True)
android_df.describe(include='all')
android_df.isna().mean()  # to highlight where values are missing eg: 
android_df.isna().mean().sort_values().tail(20)
android_df.corr()

# Plotting the correlations of this many fields is unreadable, even when constrained to numerical values.
fig1, ax1 = plt.subplots(figsize=(8, 8))
ax1 = sns.heatmap(android_df.select_dtypes(include=np.number).corr(), ax=ax1,
                  vmin=-1, vmax=1, center=0, annot=True, square=True,
                  cmap=sns.diverging_palette(220, 20, n=200))
fig1.suptitle('Android Cross-Correlation Matrix', y=0.92);

# More preliminary work needed to remove data which isn't useful   
"""

# capture the field types to add to the record of metadata.
android_df.dtypes.to_csv(workdir + 'android_info.csv')

# running .isna() in the REPL shows too many very sparse fields so explore this area further
and_sparse = android_df.isna().mean().sort_values()
and_sparse.to_csv(workdir + 'android_isna.csv')
# work out the sparsity of data (actually works out the presence of NA values so is the inverse)
and_sparse = android_df.isna().mean().sort_values()
# force this to a dataframe
and_sparse2 = and_sparse.reset_index()
# col 0 can be viewed as a set of probabilities but we want the inverse so subtract from 1
and_sparse2[0] = 1 - and_sparse2[0]
# not essential but rename this column
and_sparse2.rename(columns={0: 'Android fields'}, inplace=True)
# For plotting want to drop the 'index' column (which isn't THE # index but a column of that name!)
# Make a copy of the DF (reuse the variable name) first as this is still needed
and_sparse = and_sparse2.copy(deep=True)
# drop the index
and_sparse2.drop('index', axis=1, inplace=True)

# this is a single plot  - we should aim to produce a multiple plot for both Android and iOS
# ax2 = sns.lineplot(data=and_sparse2)

"""
Plotting doesn't work because it included iOS 

# plot both Android and iOS in a single figure with shared y-axis
sns.set(rc={'figure.figsize': (18, 5)})
fig, axs = plt.subplots(ncols=2)
sns.lineplot(data=and_sparse2, ax=axs[0])
sns.lineplot(data=ios_sparse2, ax=axs[1])
fig.suptitle('Sparsity of variables', fontsize=20, fontweight="bold", color="black")
# add lines at the chosen cut-off point of 50%
axs[0].axhline(0.5, ls='--', color='r')
axs[1].axhline(0.5, ls='--', color='r')

"""

# REVISIONS REVISIONS REVISIONS REVISIONS REVISIONS REVISIONS REVISIONS REVISIONS REVISIONS REVISIONS REVISIONS
# There were a couple of revisions necessary and writing the code isn't linear!
# 1) need to create a "5G detected" field before dropping all the largely sparse 5G fields
# 2) need to retain the 'cdma_cell_id' field. Although largely sparse, this can indicate where a mobile device
# has changed cell during the test which is likely to impact

# create new column showing any records where signal strength greater than -140dBm
android_df['5G_detected'] = (android_df['ss_rsrp_a'] > -140)
print('created "5G_detected" field. Count of values:')
print(android_df['5G_detected'].value_counts())

# first remove row matching 'cdma_cell_id' from and_sparse. Note the field called 'index' is not THE index!
and_sparse.drop(and_sparse[and_sparse['index'] == 'cdma_cell_id'].index, inplace=True)
and_drop = and_sparse.loc[and_sparse['Android fields'] < 0.5]
print(and_sparse.loc[and_sparse['Android fields'] < 0.5]['index'])

# sizeof(android_df)
# THIS CRASHES MY COMPUTER (when using inplace=True. Probably a memory allocation issue)
# android_df.drop(and_drop['index'], axis=1, inplace=True)
# This works
android_df2 = android_df.drop(and_drop['index'], axis=1)

# two functions to print out the highest correlations (originally courtesy of
# https://stackoverflow.com/questions/17778394/list-highest-correlation-pairs-from-a-large-correlation-matrix-in-pandas)

def get_redundant_pairs(df):
    '''Get diagonal and lower triangular pairs of correlation matrix'''
    pairs_to_drop = set()
    cols = df.columns
    for i in range(0, df.shape[1]):
        for j in range(0, i+1):
            pairs_to_drop.add((cols[i], cols[j]))
    return pairs_to_drop

def get_top_abs_correlations(df, n=5):
    au_corr = df.corr().abs().unstack()
    labels_to_drop = get_redundant_pairs(df)
    au_corr = au_corr.drop(labels=labels_to_drop).sort_values(ascending=False)
    return au_corr[0:n]


print(get_top_abs_correlations(android_df2.select_dtypes(include=np.number), 60))

# why do download thread count and airplane mode highly correlate?
# We conject because both are predominantly a single value

print('is_airplane_mode_a mean =', android_df2['is_airplane_mode_a'].mean())
print('is_airplane_mode_a mode = ', android_df2['is_airplane_mode_a'].mode())
print('download_thread_count_a mean =', android_df2['download_thread_count_a'].mean())
print('download_thread_count_a = ', android_df2['download_thread_count_a'].mode())

# attempting to plot a histogram isn't that successful!
# android_df2['download_thread_count_a'].hist(bins=[-2, -1, 0, 1, 2])

# client_longitude and client_longitude_start are not anything like as well correlated as expected.
# produce a scatter plot.
sns.set(rc={'figure.figsize': (8, 8)})
ax = sns.scatterplot(x='client_longitude', y='client_longitude_start', data=android_df2)
# there are some outliers in the data but in UK longitude should range from about -8 to +2
ax.set_xlim(-8, 2)
ax.set_ylim(-8, 2)

# Further list of 21 columns to remove after the analysis
remove_cols = ["client_latitude", "client_latitude_start", "client_longitude", "download_kbps",
               "miles_between", "ploss_recv_a", "ploss_sent_a", "post_connection_type", "pre_connection_type",
               "rsrp_a", "server_latitude", "server_longitude", "upload_kbps", "altitude_a", "client_longitude_start",
               "download_stop_reason_a", "download_test_duration_a", "subscription_code_a", "upload_kb_a"]

# bearing in mind the memory crash issue, make another copy using the original df name
android_df = android_df2.drop(remove_cols, axis=1)

# make a second copy of the dataframes ...
android_df.to_pickle(workdir + 'android_2.pickle')


"""
  _____       _______ ______ _____  ____  _____  _____ _____          _      
 / ____|   /\|__   __|  ____/ ____|/ __ \|  __ \|_   _/ ____|   /\   | |     
| |       /  \  | |  | |__ | |  __| |  | | |__) | | || |       /  \  | |     
| |      / /\ \ | |  |  __|| | |_ | |  | |  _  /  | || |      / /\ \ | |     
| |____ / ____ \| |  | |___| |__| | |__| | | \ \ _| || |____ / ____ \| |____ 
 \_____/_/    \_\_|  |______\_____|\____/|_|  \_\_____\_____/_/    \_\______|

Reload data if necessary 
android_df = pd.read_pickle(workdir + 'android_2.pickle')
"""

# Following a manual inspection of these data, the following should be removed.
remove_cols = ["alt_sim_network_operator_name_a", "android_fingerprint", "app_store_a", "chipset_manufacturer_a",
               "chipset_name_a", "client_country", "client_country_code", "client_ip_address", "client_region_code",
               "client_region_name", "gmaps_country", "gmaps_country_code", "gmaps_formatted_address", "gmaps_name",
               "gmaps_postal_code", "gmaps_region", "gmaps_subregion", "gmaps_subsubregion", "gmaps_type",
               "is_nr_telephony_sourced_a", "isp_common_name_a", "loc_timezone_name_a", "location_accuracy_a",
               "location_type", "ookla_device_name_a", "post_device_ip_address_s", "pre_device_ip_address_s",
               "radio_a", "server_country", "server_country_code", "server_sponsor_name", "signal_string_a",
               "sim_network_operator_code_a", "sim_network_operator_name_a", "test_date", "timezone_name_a",
               "tr_ip_0_a", "tr_ip_1_a", "valid_imei_a", "vertical_accuracy_a", "wifi_bssid_a"]

# remove these columns both from the 'full' dataframe
android_df.drop(columns=remove_cols, axis=0, inplace=True)

"""
 _____       _______       _____  _____  ______ _____ ___  
|  __ \   /\|__   __|/\   |  __ \|  __ \|  ____|  __ \__ \ 
| |  | | /  \  | |  /  \  | |__) | |__) | |__  | |__) | ) |
| |  | |/ /\ \ | | / /\ \ |  ___/|  _  /|  __| |  ___/ / / 
| |__| / ____ \| |/ ____ \| |    | | \ \| |____| |    / /_ 
|_____/_/    \_\_/_/    \_\_|    |_|  \_\______|_|   |____|
                                                                                                                 
# RETURN TO STEP 3 DATAPREP ...
# The analysis stage threw up further data prep needed to three fields: 
# 1. 'start_cell_id_a' should be compared to cdma_cell_id or gsm_cell_id to determine if the cell id changed
# during testing. Add a 'network change' boolean
# 2. wifi_rssi_a - should be an integer but contains invalid values
# 3. tr_hops_a - should be an integer but contains invalid values
"""

# start with 2 & 3 as they're easiest!
android_df.wifi_rssi_a = pd.to_numeric(android_df.wifi_rssi_a, errors='coerce').fillna(0).astype(np.int32)
android_df.tr_hops_a = pd.to_numeric(android_df.tr_hops_a, errors='coerce').fillna(0).astype(np.int32)
# and the one I missed
android_df.tr_latency_a = pd.to_numeric(android_df.tr_latency_a, errors='coerce').fillna(0).astype(np.int32)

# The logic required here is if start_cell_id_a doesn't match either gsm_cell_id OR cdma_cell_id
# there has been a cellular network change which may impact on performance.
# create a new column. Assume network has changed unless we can establish otherwise (splits the Boolean logic
# into two separate tests and neater code.)
android_df['network interruption'] = np.where(android_df['start_cell_id_a'] == android_df['gsm_cell_id'],
                                              'False', 'True')
# android_df['network interruption'].value_counts()  # <<< check using
# finally drop the two unwanted fields.
android_df.drop(columns=['start_cell_id_a', 'gsm_cell_id', 'cdma_cell_id'], axis=0, inplace=True)
# OK confession time. I didn't manage to get the above to check both values after 2-3 hours trying. The
# cdma_cell_id value only matches start_cell_id_a ni a few tens of cases so the effort is not worth it!

"""
 _______ _____  _____ __  __ _____   ______          _______ 
|__   __|  __ \|_   _|  \/  |  __ \ / __ \ \        / / ____|
   | |  | |__) | | | | \  / | |__) | |  | \ \  /\  / / (___  
   | |  |  _  /  | | | |\/| |  _  /| |  | |\ \/  \/ / \___ \ 
   | |  | | \ \ _| |_| |  | | | \ \| |__| | \  /\  /  ____) |
   |_|  |_|  \_\_____|_|  |_|_|  \_\\____/   \/  \/  |_____/ 
                                                             
Next need to look at removing unwanted rows. This code hasn't been fully checked out and tidied up due to 
time constraints so I prefer to leave it commented out. 

# Make a copy of the dataframe containing just categorical values for further analysis
and_cat = android_df.select_dtypes(include=['object'])
and_cat.to_csv(workdir + 'and_cat.csv')

and_cat.groupby('isp_name').count().T.to_csv(workdir + 'cat_group.csv')
and_cat_counts = and_cat.groupby('isp_name').count()

series_plot = and_cat_counts['network_operator_name'].sort_values(ascending=False)
# series_plot.reset_index(inplace=True)
tmp = series_plot.reset_index()
# fig, ax = sns.lineplot(data=series_plot['test_date'])
fig, ax = sns.lineplot(data=tmp['network_operator_name'])

Decision was made to remove any ISP accounting for < 2% of the tests to avoid the 'long tail' in the distribution 
"""

print(android_df['isp_name'].value_counts().sort_values())
print('there are', android_df['isp_name'].unique().__len__(), 'different ISP names in the data')

"""
This took a LOT of effort to get right so deserves detailed comments. 
Firstly, when the datasets are created by concatenation, it doesn't reset the index
Way back (line 44) now includes this command to drop the existing index and create a new one: 
android_df.reset_index(drop=True, inplace=True)

OUTLINE of how this works: 
A series is created with the (931) different ISPs and the number of tests against each sorted by popularity. 
This is sliced to remove the most popular (because the objective is to find rows to drop) 
A boolean 'mask' of row numbers is then created for all rows in the main dataframe which match the (reduced) counts df
Then need the *index* values matching tru to apply as argument to the .drop method 
"""

# create a series with the sorted counts of tests per ISP
counts_s = android_df['isp_name'].value_counts().sort_values()
# Remove the <n> most popular so we're left with the ones to be removed
counts_s = counts_s.iloc[:-10]
# Create a Series of Booleans matching rows of main dataframe which ".isin" the list of ISPs we want to drop
drop_index = android_df['isp_name'].isin(counts_s.index)
# The argument given to .drop() is the row numbers from drop_index
android_df = android_df.drop(drop_index[drop_index].index)
# inspection of the final dataframe shows 'gaps' which it can be confirmed align to the rows we needed to drop.
# this could be re-indexed but not as essential as when the dataframe was first created which resulted in dupes.
# finally, check the output
print('there are', android_df['isp_name'].unique().__len__(), 'different ISP names in the data now!')

# make a copy of just the categorical variables
and_cat = android_df.select_dtypes(include=['object'])
print('number of different categorical values for each categorical field')
for c in and_cat.columns:
    print(android_df[c].unique().__len__(), '\t', c, 'different values')
    # print('column', c, 'has', android_df[c].unique().__len__(), 'different values')

# Time for another manual examination of the data. 56 columns is still a challenge!
android_df.to_csv(workdir + 'android.csv')
# bool(1), float64(28), int32(2), int64(5), object(19)
# Following analysis of the above, remove these columns
remove_cols = ["server_name", "client_city", "isp_name", "network_operator_name", "brand", "device", "hardware",
               "build_id", "manufacturer", "model", "product", "device_software_version_a", "app_version_a",
               "android_api_a", "is_rooted_a"]

android_df = android_df.drop(remove_cols, axis=1)
android_df.to_csv(workdir + 'android.csv')
# Examine the data to determine which may be categorical data posing as numerical
# These columns identified as posing as numerical and not providing any value
remove_cols = ["alt_sim_network_operator_code_a", "android_device_id", "asu_level_a", "cid_a", "dbm_a",
               "earfcn_a", "gsm_lac_a", "is_isp", "mcc", "mnc", "net_speed_id_a", "pci_a", "tac_a",
               "test_id", "timezone_offset_seconds_a", "timing_advance_a"]
android_df = android_df.drop(remove_cols, axis=1)

# going back again to fix a problem with "is_airplane_mode_a". This should only be 1 (airplane mode on) or 0 (off)
# get_dummies found 20 different values (which look like valid latitude values for uk [50 - 56 degrees north])
android_df['is_airplane_mode_a'] = android_df['is_airplane_mode_a'].apply(lambda x: x if (x == 1) | (x == 0) else '')

print('value counts for connection type')
print(android_df["data_connection_type_a"].value_counts())
# 84% of connections are over WiFi. Only 14% cellular.

# These columns identified as posing as numerical but are really categorical so need converting for OLS method
need_dummies = ["data_connection_type_a", "architecture_a", "is_airplane_mode_a", "location_type_start",
                "phone_type_a", "server_selection_a", "signal_cell_type_a", "test_method_a"]
# these categoricals don't 100% need to be converted to dummies for OLS type analysis but maybe as well
need_dummies += ['architecture_a', 'server_selection_a', 'network interruption']
android_df = pd.get_dummies(android_df, columns=need_dummies)

# Make a third pickle copy of the dataframe.
android_df.to_pickle(workdir + 'android_3.pickle')

"""
 __  __  ____  _____  ______ _      _      _____ _   _  _____ 
|  \/  |/ __ \|  __ \|  ____| |    | |    |_   _| \ | |/ ____|
| \  / | |  | | |  | | |__  | |    | |      | | |  \| | |  __ 
| |\/| | |  | | |  | |  __| | |    | |      | | | . ` | | |_ |
| |  | | |__| | |__| | |____| |____| |____ _| |_| |\  | |__| |
|_|  |_|\____/|_____/|______|______|______|_____|_| \_|\_____|                                                  
... at last!

Reload data if necessary 
android_df = pd.read_pickle(workdir + 'android_3.pickle')
"""

# Get dummies creates  column names with '.' in them but the multiple linear regression library complains
# take this opportunity to rewrite all the column names

ren_cols = {"download_kb_a": "dl_kb", "phone_type_a_0.0": "pta0", "phone_type_a_1.0": "pta1",
            "phone_type_a_2.0": "pta2", "wifi_rssi_a": "wra", "test_method_a_1.0": "tma1",
            "test_method_a_2.0": "tma2", "test_method_a_5.0": "tma5", "test_method_a_6.0": "tma6",
            "architecture_a_arm": "arc_arm", "architecture_a_arm64-v8a": "arc_arm64",
            "architecture_a_armeabi": "arc_armeabi", "architecture_a_armeabi-v7a": "arc_armeabiv7",
            "architecture_a_universal": "arc_uni", "architecture_a_x86": "arc_x86",
            "architecture_a_x86_64": "arc_x86_64", "signal_cell_type_a_1.0": "sct1", "signal_cell_type_a_2.0": "sct2",
            "signal_cell_type_a_3.0": "sct3", "signal_cell_type_a_4.0": "sct4", "level_a": "level",
            "jitter_a": "jitter", "tr_latency_a": "latency_a", "tr_latency_1_a": "latency_1a",
            "wifi_speed_mbps_a": "wifi_mbps", "wifi_frequency_mhz_a": "wifi_mhz",
            "server_selection_a_Auto": "server_auto", "server_selection_a_USER": "server_user", "rsrq_a": "rsrq",
            "is_airplane_mode_a_0.0": "airpl_0", "is_airplane_mode_a_1.0": "airpl_1", "is_airplane_mode_a_": "airpl_x",
            "location_type_start_0.0": "loctype_0", "location_type_start_1.0": "loctype_1",
            "location_type_start_2.0": "loctype_2", "location_type_start_4.0": "loctype_4",
            "download_thread_count_a": "threads", "device_ram_a": "ram", "device_storage_a": "storage",
            "km_between": "km", "tr_hops_a": "hops", "cellbandwidth_a": "cellbw", "5G_detected": "det5G",
            "network interruption_False": "net_int_false", "network interruption_True": "net_int_true"}

android_df = android_df.rename(columns=ren_cols)
# android_df = android_df.rename(columns={'5G_detect': 'det5G'})


mls = 'dl_kb ~ pta0 + pta1 + pta2 + wra + tma1 + tma2 + tma5 + tma6 + arc_arm + arc_arm64 + arc_armeabi + ' \
      'arc_armeabiv7 + arc_uni + arc_x86 + arc_x86_64 + sct1 + sct2 + sct3 + sct4 + level + jitter + latency_a + ' \
      'latency_1a + wifi_mbps + wifi_mhz + server_auto + server_user + rsrq + airpl_0 + airpl_1 + airpl_x + ' \
      'loctype_0 + loctype_1 + loctype_2 + loctype_4 + threads + ram + storage + km + hops + cellbw + det5G + ' \
      'net_int_false + net_int_true'

lm = smf.ols(formula=mls, data=android_df).fit()
print(lm.summary())
print(lm.pvalues)


