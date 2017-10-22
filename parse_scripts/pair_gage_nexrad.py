#Created on Thu Mar 20 16:12:17 2014
#@author: rspies
# Python 2.7
# This script reads in USGS gage data and pairs the timeseries to the
# corresponding nexrad cell(s)
# Output multiple text files - 1 for each USGS gage with nexrad data

import os
import datetime
from dateutil import parser

maindir = os.getcwd()[:-28]

####### find station description info from info file #########  
finfo = open(maindir + 'data\\USGS 2002_2012_updated\\station_box_info.txt','r')
gage_names = {}
for info in finfo:
    if info[:2] == 'US': #ignores header
        idata = info.split('\t')
        site_num = idata[1]
        gage_names[site_num]=str(idata[2])
finfo.close()
################ read input card (.txt) file with gage id's and nexrad cell id's ##############
finput = open(maindir + 'data\\INPUT_gages_cells.txt', 'r')
usgs_gages = []
cor_nexcell = {}
for ids in finput:
    if ids[:4] != 'Loca': #ignores header
        idinfo = ids.split('\t')
        site_num = idinfo[1].rstrip()
        usgs_gages.append(str(site_num))
        cor_nexcell[site_num]=[str(idinfo[2].rstrip())] # create a dictionary with corresponding nexrad cell for each gage station
        if site_num not in gage_names:
            gage_names[site_num]=str(idinfo[0])
finput.close()
################# create a list of days to use in the analysis ########################
ystart = 2002 # begin data grouping
yend = 2012 # end data grouping
start = datetime.datetime(ystart, 1, 1, 0, 0)
ticker = start
finish = datetime.datetime(yend, 9, 30, 23, 0)
date_list = []
while ticker <= finish:
    date_list.append(str(ticker)[:-9])
    ticker += datetime.timedelta(days=1)

################## Parse each ground-gage file ################################    
status = open(maindir + '\\data\\usgs_nexrad_paired\\status.txt','w') # output helpful info on the status of the processing
for gage in usgs_gages:
    fopen = open(maindir + 'data\\USGS 2002_2012_updated\\' + gage + '.txt','r')
    print 'Processing data for ' + gage + ' -> ' + gage_names[gage]    
    gage_lib = {}
    usmiss = 0
    for line in fopen:
        if line[:1] == '0' or line[:1] == '4':
            status.write(line)
        if line[:2] == 'US': #ignores header
            udata = line.split('\t')
            date_check = parser.parse(udata[2])
            if date_check >= start and date_check <= finish:
                prec_us = udata[3].rstrip()
                if prec_us == '' or prec_us[-3:] == 'Eqp' or prec_us[-3:] == '***' or prec_us == 'na':
                    prec_us = 'na'
                    usmiss += 1
                elif float(prec_us) < 0 or float(prec_us) > 15: # replace erroneous values with 'na'
                    prec_us = 'na'
                    usmiss += 1
                gage_lib[str(date_check)[:-9]]=prec_us                  
    fopen.close()
    status.write('usgs gage missing (na) days: ' + str(usmiss) + '\n')

############## parse corresponding nexrad data ###############################    
    howmany = len(cor_nexcell[gage])
    nfiles = []
    nex_lib = {}
    for ncell in cor_nexcell[gage]: #pulls the corresponding nexrad cells from dictionary above
        nfiles.append(maindir + '\\data\\Nexrad2002_2008\\' + 'cell' + str(ncell) + '-2-1-2002-9-30-2008.txt')        
        nfiles.append(maindir + '\\data\\Nexrad2009_2012\\' + 'cell' + str(ncell) + '-10-1-2008-9-30-2012.txt')        
        status.write('NEXRAD Cell ID: ' + str(ncell) +'\n')

    for nexfile in nfiles:      
        infile = open(nexfile,'r')
        nxmiss = 0
        for nline in infile:
            if nline[:3] == '  2' or nline[:3] == '  1': #ignores header
                ndata = nline.split()
                yr = int(ndata[0])
                mn = int(ndata[1])
                dy = int(ndata[2])
                # nexrad data from Julien is in hours (1-24) for each day
                hr = int(ndata[3])
                # datetime module needs hours to be 0-23 
                nex_date = datetime.datetime(yr,mn,dy)
                if nex_date >= start and nex_date <= finish:
                    prec_nx = float(ndata[4])
                    key = str(nex_date)[:-9]
                    if float(prec_nx) < 0 or float(prec_nx) > 15: # replace erroneous values with 'na'
                        prec_nx = 'na'
                        nxmiss += 1
                    if key in nex_lib:
                        nex_lib[key].append(prec_nx)
                    else:
                        nex_lib[key]=[prec_nx]
                        
        status.write('NEXRAD cell' + nexfile[70:] + ' missing (na) hours: ' + str(nxmiss) + '\n')
        infile.close()
###################### write paired data to gage specific file ################    
    pair_file = open(maindir + '\\data\\usgs_nexrad_paired\\' + gage + '.txt','w')    
    pair_file.write('Date\t' + 'USGS Gage\t' + 'Mean Nexrad\n')    
    for each_date in date_list:
        pair_file.write(each_date + '\t')
        if each_date in gage_lib:
            pair_file.write(str(gage_lib[each_date]) + '\t')
        else:
            pair_file.write('na\t')
            
        if each_date in nex_lib:
            if 'na' in nex_lib[each_date]:
                pair_file.write(str('na') + '\n')
            elif len(nex_lib[each_date]) != (howmany*24):
                print 'Nexrad missing data for at least one hr: ' + each_date
                pair_file.write(str('na') + '\n')
            else:
                mean_nex = sum(nex_lib[each_date])/howmany # divide by the number of nexrad cells used in calc
                pair_file.write(str("%.2f" % mean_nex) + '\n')
        else:
            pair_file.write('na\n')
    pair_file.close()

status.close()
print 'Complete!'

''' # this code was used to add the old data from Julien when the new data was not available (3 sites missing online)
# obtained the new data from nwis server 4/2/2014
if gage == '414655088102300': # new data not available online
        fopen = open(maindir + 'data\\USGS 1997_2009_julien\\' + '41465509' + '.txt','r')
        gage_names[gage]='NAPERVILLE N OPERATIONS CENTER AT NAPERVILLE, IL'
    elif gage == '414158088095600':
        fopen = open(maindir + 'data\\USGS 1997_2009_julien\\' + '41415809' + '.txt','r')
        gage_names[gage]='SPRING BROOK WWTF NR NAPERVILE, IL'
    elif gage == '415751087591000':
        fopen = open(maindir + 'data\\USGS 1997_2009_julien\\' + '41575109_2002_2009' + '.txt','r')
        gage_names[gage]='WOOD DALE WWTF AT WOOD DALE, IL'
    else:    
'''