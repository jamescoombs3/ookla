# import matplotlib.pyplot as plt
import seaborn as sns
# import numpy as np
import pandas as pd
import os
# import re

"""
This was just used to produce a plot of where in the UK the Ookla tests were being run
Entire project is uploaded to https://github.com/jamescoombs3/ookla 
"""


# Import some data
csv = 'p:/ookla/2020-may2aug.csv'
csv = 'p:/ookla/2020-05.csv'
cols = ['E', 'N']
ook = pd.read_csv(csv, usecols=cols, index_col=False, low_memory=False)

sns.set_style("white")
h = sns.jointplot(x='E', y='N', data=ook, # kind='hist',
                  marker='+', color='red', s=1, # aspect=1,
                  xlim=(0, 660000), ylim=(0, 1100000))


h.fig.set_figwidth(6.6)
h.fig.set_figheight(11)

# h.fig.suptitle('Think of a title')

h.savefig('p:/ookla/uk-plot-600red.png', dpi=600)


# path to my ACS files
acsdir = 'c:/1drive/OneDrive - Three/jumpserver/UKB/ACS_Reports'
acsdir = 'p:/UKB/sample'


# create empty dataframe
cols = ["Identity", "imsi", "Date", "PCI",
        "RSRP0", "SINR", "CellID", "PeakDL",
        "Band_ID", "RSRP_5G", "SINR_5G"]
acs = pd.DataFrame(columns=cols)


for root, dirnames, filenames in os.walk(acsdir):
    print('test root contains', root)
    for filename in filenames:
        if (filename.startswith('3UK_CPE') and filename.endswith('.csv')):
            fpath = root + '/' + filename
            print('loading', fpath)
            df = pd.read_csv(fpath, usecols=cols, index_col=False, low_memory=False)
            acs = acs.append(df)
        if (filename.startswith('3UK_CPE') and filename.endswith('.zip')):
            fpath = root + '/' + filename
            print('loading', fpath)
            df = pd.read_csv(fpath, usecols=cols, index_col=False, low_memory=False, compression='zip')
            acs = acs.append(df)


# drop rows with nothing in RSRP_5G
acs5g = acs[acs['RSRP_5G'].notna()]
acs5g.__len__()

sns.set(style='darkgrid')
# sns.scatterplot(x='RSRP0', y='RSRP_5G', data=acs5g)

"""
k = sns.jointplot(x='RSRP0', y='RSRP_5G', data=acs5g, kind='kde',
                  xlim=(-110, -70), ylim=(-120, -65))
k.fig.suptitle('4G and 5G RSRP compared (n=26k)')
"""

h = sns.jointplot(x='RSRP0', y='RSRP_5G', data=acs5g, kind='hex',
                  xlim=(-110, -70), ylim=(-120, -65))
h.fig.suptitle('4G and 5G RSRP compared')

"""
grid = sns.lmplot('num', 'stringent', data, size=7, truncate=True, scatter_kws={"s": 100})

g = sns.jointplot(x='RSRP0', y='RSRP_5G', data=df, kind='kde', color='m')
g.plot_joint(plt.scatter, c='w', s=30, linewidth=1, marker='+')
g.ax_joint.collections[0].set_alpha(0)
g.set_axis_labels("$X$", "$Y$")
"""

# compare PeakDL speed to RSRP_5G but only where speed is > 80Mbs otherwise
# 'measuring speed of car in garage'!
acs_speed = acs5g[acs5g['PeakDL'] > 80]
samples = acs_speed.__len__()

g = sns.jointplot(x='PeakDL', y='RSRP_5G', data=acs_speed, kind='kde', color='m',
                  xlim=(0, 350), ylim=(-65, -120))
g.fig.suptitle('Peak DL greater than 80Mbs × 5G RSRP')

