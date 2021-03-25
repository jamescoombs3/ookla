import pandas as pd
import numpy as np
import seaborn as sns
from sklearn.model_selection import train_test_split

"""
  _____ _                _____ _____ _____ ________     __
 / ____| |        /\    / ____/ ____|_   _|  ____\ \   / /
| |    | |       /  \  | (___| (___   | | | |__   \ \_/ / 
| |    | |      / /\ \  \___ \\___ \  | | |  __|   \   /  
| |____| |____ / ____ \ ____) |___) |_| |_| |       | |   
 \_____|______/_/    \_\_____/_____/|_____|_|       |_|   
                                                          
This script creates a contingency table and plots the results.         
Entire project is uploaded to https://github.com/jamescoombs3/ookla                                              
"""

# Load previous results
workdir = 'p:/ookla/pickle'
ook_df = pd.read_pickle(workdir + '/ook_df_interps.pickle')

# create a dataframe for the contingency
df_bayes = pd.DataFrame(np.zeros((2, 2)))

# set a cutoff level
cutoff = -100
pred = ['RSRP', 'bilinear', 'distance', 'bicubic']

# iterate over the predictors and their 2x2 truth values (NB Python treats zero as false)
for p in pred:
    df = p + '_bayes'
    for x in [0, 1]:
        for y in [0, 1]:
            # For the contingency table we want to have:
            # 'distance' on the x axis. This is the calibrated/interpolated version
            # 'RSRP' on y axis. This is the current measure
            # True condition is > therefore False is <=
            print('x and y are', x, y)
            if x:
                if y:
                    counts = len(ook_df[(ook_df['rsrp_a'] > cutoff) & (ook_df[p] > cutoff)])
                    print('both x,y true, TruePositive, count is', counts)
                    df_bayes.iloc[x, y] = counts
                else:
                    counts = len(ook_df[(ook_df['rsrp_a'] <= cutoff) & (ook_df[p] > cutoff)])
                    print('only x is true, FalseNegative, count is', counts)
                    df_bayes.iloc[x, y] = counts
            else:
                if y:
                    counts = len(ook_df[(ook_df['rsrp_a'] > cutoff) & (ook_df[p] <= cutoff)])
                    print('only y is true, FalsePositive count is', counts)
                    df_bayes.iloc[x, y] = counts
                else:
                    counts = len(ook_df[(ook_df['rsrp_a'] <= cutoff) & (ook_df[p] <= cutoff)])
                    print('both x,y false, TrueNegative count is', counts)
                    df_bayes.iloc[x, y] = counts
    print('contingency table for', p, df_bayes)


# Take a random sample and plot it
ook_plot_df, ook_rem_df = train_test_split(ook_df, test_size=0.998, random_state=0)
sns.set(rc={'figure.figsize': (8, 8)})
ax = sns.scatterplot(x='RSRP', y=p, data=ook_plot_df, hue='WiFi')
