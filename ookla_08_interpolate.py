import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from scipy import interpolate

"""
import statsmodels.formula.api as smf
import xlrd
import matplotlib.pyplot as plt
import glob
import numpy as np
"""

"""
 ____ _____ _      _____ _   _ ______          _____  
|  _ \_   _| |    |_   _| \ | |  ____|   /\   |  __ \ 
| |_) || | | |      | | |  \| | |__     /  \  | |__) |
|  _ < | | | |      | | | . ` |  __|   / /\ \ |  _  / 
| |_) || |_| |____ _| |_| |\  | |____ / ____ \| | \ \ 
|____/_____|______|_____|_| \_|______/_/    \_\_|  \_\
                                                      
This script follows on from a series of cleansing and shaping scripts the output of which is 
Ookla test data with the 16 nearest normal lookup points.   

"""

workdir = 'p:/ookla/pickle'
ook_df = pd.read_pickle(workdir + '/ook_df_final.pickle')


def bilinear(sw, se, nw, ne, e, n):
    x = e % 50
    y = n % 50
    r1 = sw - ((sw - se) * x / 50)
    r2 = nw - ((nw - ne) * x / 50)
    ret = r1 - ((r1 - r2) * y / 50)
    # print('Debug: I was given sw, se, nw, ne, e, n', sw, se, nw, ne, e, n, 'returning:', ret)
    return ret


# Call the function with dataframe.apply. Note variable names used in the function are points of compass
# so there has to be a mapping
ook_df['bilinear'] = ook_df.apply(lambda row: bilinear(row.x2y2, row.x3y2, row.x2y3, row.x3y3, row.E, row.N), axis=1)

formula = 'rsrp_a ~ bilinear'
print('Testing', formula)
lm = smf.ols(formula=formula, data=ook_df).fit()
print(lm.rsquared)

"""
 _____ _____  _____ _______       _   _  _____ ______ 
|  __ \_   _|/ ____|__   __|/\   | \ | |/ ____|  ____|
| |  | || | | (___    | |  /  \  |  \| | |    | |__   
| |  | || |  \___ \   | | / /\ \ | . ` | |    |  __|  
| |__| || |_ ____) |  | |/ ____ \| |\  | |____| |____ 
|_____/_____|_____/   |_/_/    \_\_| \_|\_____|______|
                                                      

"""

def distance(sw, se, nw, ne, e, n):
    x = e % 50
    y = n % 50
    """
    # These square roots are all squared immediately they are so the actual code below is a bit more efficient. 
    # This code is retained but commented out as it accurately reflects the sigma notation formula it was based on. 
    v1 = (x ** 2        + y        ** 2) ** 0.5
    v2 = (x ** 2        + (50 - y) ** 2) ** 0.5
    v3 = ((50 - x) ** 2 + (50 - y) ** 2) ** 0.5
    v4 = ((50 - x) ** 2 + y        ** 2) ** 0.5

    dbv1 = sw / (v1 ** 2)
    dbv2 = nw / (v2 ** 2)
    dbv3 = ne / (v3 ** 2)
    dbv4 = se / (v4 ** 2)

    onev1 = 1 / (v1 ** 2)
    onev2 = 1 / (v2 ** 2)
    onev3 = 1 / (v3 ** 2)
    onev4 = 1 / (v4 ** 2)
    """

    # Does the same as above but without squaring the square root!
    v1 = (x ** 2        + y        ** 2)
    v2 = (x ** 2        + (50 - y) ** 2)
    v3 = ((50 - x) ** 2 + (50 - y) ** 2)
    v4 = ((50 - x) ** 2 + y        ** 2)

    dbv1 = sw / v1
    dbv2 = nw / v2
    dbv3 = ne / v3
    dbv4 = se / v4

    onev1 = 1 / v1
    onev2 = 1 / v2
    onev3 = 1 / v3
    onev4 = 1 / v4


    sigma1 = dbv1 + dbv2 + dbv3 + dbv4
    sigma2 = onev1 + onev2 + onev3 + onev4
    return sigma1 / sigma2


# Call the function with dataframe.apply. Note variable names used in the function are points of compass
# so there has to be a mapping
ook_df['distance'] = ook_df.apply(lambda row: distance(row.x2y2, row.x3y2, row.x2y3, row.x3y3, row.E, row.N), axis=1)

formula = 'rsrp_a ~ distance'
print('Testing', formula)
lm = smf.ols(formula=formula, data=ook_df).fit()
print(lm.rsquared)


"""
 ____ _____ _____ _    _ ____ _____ _____ 
|  _ \_   _/ ____| |  | |  _ \_   _/ ____|
| |_) || || |    | |  | | |_) || || |     
|  _ < | || |    | |  | |  _ < | || |     
| |_) || || |____| |__| | |_) || || |____ 
|____/_____\_____|\____/|____/_____\_____|
                                          

"""


def bicubic(x1y4, x2y4, x3y4, x4y4, x1y3, x2y3, x3y3, x4y3, x1y2, x2y2, x3y2, x4y2, x1y1, x2y1, x3y1, x4y1, e, n):
    """
    The main purpose of this function is to rearrange those ungainly command line arguments into a 4x4
    array of the sort Numpy interp2d expects to find.
    """

    z = [[x1y4, x2y4, x3y4, x4y4],
         [x1y3, x2y3, x3y3, x4y3],
         [x1y2, x2y2, x3y2, x4y2],
         [x1y1, x2y1, x3y1, x4y1]]

    x = np.arange(0, 4, 1)
    y = np.arange(0, 4, 1)

    # create the local model
    f = interpolate.interp2d(x, y, z, kind='cubic')

    # reuse x, y
    x = (e % 50 + 50) / 50
    y = (n % 50 + 50) / 50

    # find the value
    rsrp_int = f(x, y)[0]
    print("Eastings", e, 'Northings', n, 'Interpolated value:', rsrp_int)
    return rsrp_int


# Call the function. Not ideal to use these positional parameters. Potential for errors!
ook_df['bicubic'] = ook_df.apply(lambda row: bicubic(row.x1y4, row.x2y4, row.x3y4, row.x4y4,
                                                       row.x1y3, row.x2y3, row.x3y3, row.x4y3,
                                                       row.x1y2, row.x2y2, row.x3y2, row.x4y2,
                                                       row.x1y1, row.x2y1, row.x3y1, row.x4y1,
                                                       row.E, row.N), axis=1)

# I think there is a better way to do this. Use a slice from  ook_df and automatically manipulate into
# an array then pass the array to the function. Run out of time before investigating!

formula = 'rsrp_a ~ bicubic'
print('Testing', formula)
lm = smf.ols(formula=formula, data=ook_df).fit()
print(lm.rsquared)

ook_df.to_csv(workdir + '/ook_df_interps.csv')
ook_df.head(2000).to_csv(workdir + '/ook_df_interps2k.csv')
ook_df.to_pickle(workdir + '/ook_df_interps.pickle')

