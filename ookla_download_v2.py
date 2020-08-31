"""
Extract speed test results from Ookla
=====================================
Version 1 (21/04/20) obtain zip files and extract those where the IP addresses matches Three's network
Version 2 (13/08/20) "filter3" function updated to count the total daily records and those
          which are run on Three's cellular network

"""

from bs4 import BeautifulSoup
# documentation, including some examples, is here https://www.crummy.com/software/BeautifulSoup/bs4/doc/
import requests
import os
import re
import zipfile
import pandas as pd
# not sure if needed.
import numpy as np

# Define some constants
ookladir = "p:/ookla/"
ooklaweb = 'https://extracts.ookla.com/files/v2'
ooklaname = '3_uk_ext'
ooklapass = 'kT5CqD8l'
# Ookla accept the name and password as part of the URL string in this format
ooklaURL = 'https://3_uk_ext:kT5CqD8l@extracts.ookla.com/files/v2'

"""
  _____ _____       __          ___      
 / ____|  __ \     /\ \        / / |     
| |    | |__) |   /  \ \  /\  / /| |     
| |    |  _  /   / /\ \ \/  \/ / | |     
| |____| | \ \  / ____ \  /\  /  | |____ 
 \_____|_|  \_\/_/    \_\/  \/   |______|
(Online figlet at https://www.askapache.com/online-tools/figlet-ascii/) 
The objective is to visit the URL ooklaweb and download any zip files which 
don't match the *csv* files in ookladir
"""

# submit a request using the 'authenticating' URL
page = requests.get(ooklaURL)
# create a soup object
soup = BeautifulSoup(page.content, features='html.parser')
# extract just the body (this is probably not necessary)
body = soup.find(name='body')

# write a reusable function to download binary files
# validation is assumed to happen somewhere else!
def dlbin(source, target):
    try:
        # print ("current directory is ",os.getcwd())
        # print ("fname is ", fname, "jpg is ",jpg)
        print("Downloading ", source, "to", target)
        req = requests.get(source)
        # print(req.status_code)
        # print(pic.encoding)
        # if True:
        if (req.status_code == 200):
            req = requests.get(source, stream=True)
            req.raise_for_status()
            with open(target, 'wb') as fd:
                for chunk in req.iter_content(chunk_size=50000):
                    print('.', end="")
                    fd.write(chunk)
        print("\n")
    except:
        print("That didn't work!")


# define a function to extract just Three IP addresses from
def filter3(targ):
    # create empty dataframe to contain wanted rows.
    print('scanning', targ)
    matching = 0
    df2 = pd.DataFrame
    # read the input file
    df = pd.read_csv(targ, low_memory=False)
    # print(df.shape)
    total_recs = df.__len__() - 1
    # There are TWO inconsistencies in just the one field we're interested in.
    # IP Addresses are in the fourth column for iOS and WP, fifth for android
    # This field is called 'client_ip_address' on Android and iOS files but 'client_ip_address_s' on WP
    # Feels the best way to move beyond this mess is to see if the IP column is fourth, if not
    # (iOS or WP) insert a dummy column ... and rename this column whether it needs it nor not.
    col5 = df.columns.values[4]
    if not re.search('^client_ip_add', col5):
        df.insert(2, 'fingerprint', '')
        col5 = df.columns.values[4]
        df.rename(columns={col5: 'client_ip_address'}, inplace=True)

    # Create an array of all the 1st/2nd octet REs for Three IP addresses
    ipmatch = ['92.40.', '92.41.',
               '94.196.', '94.197.',
               '188.28.', '188.29.',
               '188.30.', '188.31.']

    # Create a new dataframe of rows matching first element in ipmatch
    for m in ipmatch[:1]:
        df2 = df[df['client_ip_address'].str.startswith(m)]

    # concatenate rows matching the other elements in ipmatch
    for m in ipmatch[1:]:
        df2 = pd.concat([df2, df.loc[df['client_ip_address'].str.startswith(m)]], ignore_index=True)
        matching += df2.__len__()
        print(df2.__len__(), 'records found')

    # write the resulting filtered CSV
        df2.to_csv(targ, index=False)
        # update the meta data - matching records

    # print totals
    print('found', matching, 'ThreeUK records out of', total_recs, 'total')
    # This adds the totals to a simple  CSV file.
    with open("metadata.csv", "a") as metafile:
        outputline = targ + ',' + str(matching) + ',' + str(total_recs) + '\n'
        metafile.write(outputline)


# IMPORTANT need to change to the working directory, otherwise this script will fill your
# scripting directory with 100s of massive csv files!
os.chdir(ookladir)

for a_tag in body.findAll('a'):
    href = a_tag.attrs.get('href')
    # print(href)
    # href is in format eg: href = '/files/v2/wp_2020-04-14.zip'
    #                       href = '/files/v2/android_2020-04-03.zip'

    # Split href on "/" and ".". We only care about the file extension and file's basename
    # the rest is junk. ;-)
    # There are other links on the page so the
    try:
        junk, junk, junk, fname, ext = re.split('/|\.', href)
        print("processing", fname, ext)
        if ext == 'zip':
            # Check to see if we have a csv file matching p:/ookla/wp_2020-04-14.csv
            if os.path.isfile(ookladir + fname + '.csv'):
                print(fname, 'already processed')
            else:
                # if we don't have csv then download the zip
                # print('processing', fname)
                # as downloading a binary file could be really useful, create a function to do this
                zipURL = 'https://3_uk_ext:kT5CqD8l@extracts.ookla.com/files/v2/' + fname + '.zip'
                target = 'p:/ookla/' + fname + '.zip'
                # print('Calling the "dlbin" function with parameters', zipURL, target)
                dlbin(zipURL, target)
                # Extract CSV file and delete the zip
                my_zipfile = zipfile.ZipFile(target, mode='r', compression=zipfile.ZIP_DEFLATED)
                my_zipfile.extractall()
                my_zipfile.close()
                # os.remove(target)   # note this is the zip file.
                target = 'p:/ookla/' + fname + '.csv'
                filter3(target)
    except:
        print('skipping link', href)

