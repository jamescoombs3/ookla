
"""
  ____   ____  _  ___               __  __ ______ _______
 / __ \ / __ \| |/ / |        /\   |  \/  |  ____|__   __|/\
| |  | | |  | | ' /| |       /  \  | \  / | |__     | |  /  \
| |  | | |  | |  < | |      / /\ \ | |\/| |  __|    | | / /\ \
| |__| | |__| | . \| |____ / ____ \| |  | | |____   | |/ ____ \
 \____/ \____/|_|\_\______/_/    \_\_|  |_|______|  |_/_/    \_\

Some initial analysis of the Ookla data

"""

import xlrd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
from scipy import stats

ooklameta = pd.read_csv(r'P:\ookla\metadata.csv')
workdir = 'C:/1drive/OneDrive - Three/_avado_Masters/2020/Data-Mining+Machine-Learning/assignment/'
# Filename is in the form eg: 'p:/ookla/android_2019-12-16.zip'
# take slices of this filename to find the phone operating system and date
ooklameta['Operating System'] = ooklameta.filename.str[9:10]
ooklameta['date'] = ooklameta.filename.str[-14:-4]

print('shape of data is', ooklameta.shape)
# drop the Windows Phone records which contain literally just a handful of records.
ooklameta = ooklameta[ooklameta['Operating System'] != 'w']
print('shape of data after dropping windows phone records is', ooklameta.shape)

# rename the Operating System values 'a' and 'i' to 'Android' and 'iOS'
ooklameta['Operating System'] = ooklameta['Operating System'].apply(lambda x: 'Android' if x == 'a' else 'iOS')

# Check the correlation between each OS for whole UK. Needs a 'wide' view so pipe the output of .pivot to .corr.
print('Pearson product-moment correlation')
print(ooklameta.pivot(index='date', columns='Operating System', values='all_UK').corr())

# currently the data consists of number of tests on Three and tests on all of UK *including* Three
# so we should really do a quick bit of subtraction.
ooklameta['non_Three'] = ooklameta['all_UK'] - ooklameta['Three']

# Print a heatmap with KDE 'sidebars' to get an overview of the distributions
sns.set(style='darkgrid')
g = sns.jointplot(x='non_Three', y='Three', data=ooklameta, kind='kde', color='m',)
#                  xlim=(25000, 150000), ylim=(25000, 45000))
g.fig.suptitle('Speed tests on non-Three and Three networks')

# convert 'long' to 'wide' -
o_wide = ooklameta.pivot(index='Operating System', columns='date', values='Three')
o_wide = o_wide.append(ooklameta.pivot(index='Operating System', columns='date', values='non_Three')).T
columns = ['Android_Three', 'iOS_Three', 'Android_non_Three', 'iOS_non_Three']
o_wide.columns = columns
o_desc = o_wide.describe()
o_desc = o_desc.append(o_wide.skew().rename('skew'))
o_desc = o_desc.append(o_wide.kurt().rename('kurt'))
print('summary stats')
print(o_desc)


def cliffs_delta(d1, d2):
    """Return Cliff's delta for two distributions.
    delta =  (# samples(d1 > d2) - # samples(d2 > d1)) / (n1 * n2),
    where n1 and n2 are sample sizes

    delta = 2 * U / (n1 * n2) - 1,
    where U is the Mann-Whitney U statistic
    Args:
        d1, d2 (np.array)

    Returns:
        delta (float): Cliff's delta
        interpretation (str): interpretation of Cliff's delta
    """
    U, p = stats.mannwhitneyu(d1, d2)
    # print(f'Mann-Whitney U={U}, p={p:.2e}')
    delta = abs(2 * U / (len(d1) * len(d2)) - 1)

    # Interpret cliff's delta
    if 0 <= delta < 0.2:
        effect = 'small effect'
    elif 0.2 <= delta < 0.4:
        effect = 'medium effect'
    elif delta >= 0.4:
        effect = 'large effect'

    interpretation = f'Cliff\'s Delta between group means corresponds to {effect} size.'

    return delta, interpretation


cliffs_delta(o_wide['Android_Three'], o_wide['iOS_Three'])

# Create a 'long' version of the data to allow boxplot by individual category
o_long = pd.melt(ooklameta, id_vars=['Operating System'], value_vars=['non_Three', 'Three'])
# move the actual plotting of this data down a few lines so it appears next to the standardised version and
# can get both plots looking consistent (or even have both in a single figure maybe)
# g = sns.boxplot(x='Operating System', y='value', data=o_long, hue='variable')

# find weighting of Three/non-Three
totals = o_wide.sum().sum()
total3 = o_wide.sum()[:2].sum()
print('proportion of tests run on Three network is', total3 / totals)
print('proportion of tests run on non Three network is', (totals - total3) / totals)

# about twice as many tests run on non-Three network so normalise the data by network (whilst preserving the
# differences between the operating systems.
# Creating these variables isn't essential but might make the code a bit more readable!
std_3 = ooklameta.std()['Three']
std_non3 = ooklameta.std()['non_Three']
mean_3 = ooklameta.mean()['Three']
mean_non3 = ooklameta.mean()['non_Three']

print('key values')
for v in ['std_3', 'mean_3', 'std_non3', 'mean_non3']:
    print(v, '\t', eval(v))

# create a standardised version of o_long ...
# Start with a lambda function to create new columns in the ooklameta dataframe
ooklameta['non_Three_std'] = ooklameta.apply(lambda row: (row.non_Three - mean_non3) / std_non3, axis=1)
ooklameta['Three_std'] = ooklameta.apply(lambda row: (row.Three - mean_non3) / std_non3, axis=1)
o_long_std = pd.melt(ooklameta, id_vars=['Operating System'], value_vars=['non_Three_std', 'Three_std'])


# plot both the unweighted and standardised values in a single figure.
sns.set(rc={'figure.figsize': (18, 5)})
fig, axs = plt.subplots(ncols=2)
sns.boxplot(x='Operating System', y='value', data=o_long, hue='variable', ax=axs[0])
sns.boxplot(x='Operating System', y='value', data=o_long_std, hue='variable', ax=axs[1])
fig.suptitle('Absolute and standardised distributions of tests/day', fontsize=20, fontweight="bold", color="black")
# axs[0].axhline(0.5, ls='--', color='r')
# axs[1].axhline(0.5, ls='--', color='r')


prop3 = o_wide['iOS_non_Three'].sum()

( x - ooklameta.std()['Three']

# And again for just Three network
print('Pearson product-moment correlation')
print(ooklameta.pivot(index='date', columns='Operating System', values='Three').corr())

print('Total tests by Operating System')
print(ooklameta.pivot(index='date', columns='Operating System', values='all_UK').sum())

# Calculate the proportions of records and print
sums = ooklameta.pivot(index='date', columns='Operating System', values='all_UK').sum()
# Android percentage of records is 100 * sums[0] / (sums[0] + sums[1])

a_pct = 'Android: %1.2f' % (100 * sums[0] / (sums[0] + sums[1])) + '%'
i_pct = 'iOS:     %1.2f' % (100 * sums[1] / (sums[0] + sums[1])) + '%'
print('percentages of records by operating system')
print(a_pct)
print(i_pct)



sns.set(rc={'figure.figsize': (18, 5)})
ax = sns.scatterplot(data=ooklameta, x='all_UK', y='Three', hue='Operating System')
plt.legend(loc='lower right')
plt.title('Number of handset based speed tests on Three\'s UK network compared to all by Operating System', fontsize=16)
ax.set_xlim(50000, 180000)
path = workdir + 'num_tests_daily.png'
plt.savefig(path, format='png', dpi=300)

ooklameta['date'] = pd.to_datetime(ooklameta['date'])
ax2 = sns.lineplot(data=ooklameta, x='date', y='all_UK', hue='Operating System')
plt.title('Daily number of Ookla tests run on handsets in the UK by Operating System', fontsize=16)


