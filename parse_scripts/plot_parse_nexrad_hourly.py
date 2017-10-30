#Created on Wed May 7 10:37:17 2014
#@author: rspies
# Python 2.7
# This script reads in USGS and CoCoRaHS gage data and pairs the timeseries to the
# corresponding nexrad cell(s)
# Output one text file - with Argonne Temperature and all NEXRAD cell data (CSV file)

import os
import datetime
import numpy
from dateutil import parser
import matplotlib.pyplot as plt
os.chdir("..")
maindir = os.getcwd() + os.sep

######### User Input -> Options ############
csv_out = 'no'
mean_hist = 'yes'  # choice to creat plot 'yes' or 'no'
type_plot = 'Mean Cell' # choices: 'Mean', 'Mean Intensity', 'Mean Cell', 'Total', 'Temperature Frequency', 'Hours Precip'
type_plot2 = 'Temperature Frequency' # choices: 'Temperature Frequency', ''

### calculate helpful summary statistics input ###
# temp range
tmin = 32.0; tmax = 74.0

################# create a list of days to use in the analysis ########################
ystart = 2002 # begin data grouping
yend = 2012 # end data grouping
start = datetime.datetime(ystart, 2, 1, 0, 0)
ticker = start
finish = datetime.datetime(yend, 9, 30, 23, 0)
date_list = {}
while ticker <= finish:
    date_list[(str(ticker))] = []
    ticker += datetime.timedelta(hours=1)

################## Pull all NEXRAD cell id #'s used in study ################################
######## read USGS gage input card (.txt) file with gage id's and nexrad cell id's ##############
finput = open(maindir + 'data\\INPUT_gages_cells.txt', 'r')
usgs_gages = []
cor_nexcell = []
for ids in finput:
    if ids[:4] != 'Loca': #ignores header
        idinfo = ids.split('\t')
        site_num = idinfo[1].rstrip()
        usgs_gages.append(str(site_num))
        if str(idinfo[2].rstrip()) not in cor_nexcell:
            cor_nexcell.append(str(idinfo[2].rstrip())) # create a dictionary with corresponding nexrad cell for each gage station
finput.close()
########## read CoCoRaHS input card (.txt) file with gage id's and nexrad cell id's ##############
finput = open(maindir + 'data\\INPUT_coco_cells_distance.txt', 'r')
coco_gages = []
for ids in finput:
    idinfo = ids.split('\t')
    if ids[:4] == 'COCO': #ignores header
        name = idinfo.index('Name')
        num = idinfo.index('Site_ID')
        rad_cell = idinfo.index('CELL_NO')
    else:
        site_num = idinfo[num].rstrip()
        coco_gages.append(str(site_num))
        if str(idinfo[rad_cell].rstrip()) not in cor_nexcell:
            cor_nexcell.append(str(idinfo[rad_cell].rstrip())) # create a dictionary with corresponding nexrad cell for each gage station
finput.close()

################## Parse Argonne temperature file ################################    
print 'Processing data for ' + 'Argonne hourly temperature...'
fopen = open(maindir + 'data\\temperature\\argonne.txt','r')
temp_lib = {}
bad = 0
for line in fopen:
    if line[:2] == '20': #ignores header
        udata = line.split('\t')
        date_check = parser.parse(udata[0])
        if date_check >= start and date_check <= finish:        
            temp = udata[1].rstrip()
            if temp == '':
                temp = 'na'
            elif float(temp) < -30 or float(temp) > 120: # replace erroneous values with 'na'
                temp = 'na'
            else:
                temp = float(temp)
            key = str(date_check)
            date_list[key].append(temp)               
fopen.close()

############# Create a dictionary of all NEXRAD cells hourly data ####################
print 'Processing NEXRAD cell files...'
nfiles = []
for ncell in cor_nexcell: #pulls the corresponding nexrad cells from dictionary above
    nfiles.append(maindir + '\\data\\Nexrad2002_2008\\' + 'cell' + str(ncell) + '-2-1-2002-9-30-2008.txt')        
    nfiles.append(maindir + '\\data\\Nexrad2009_2012\\' + 'cell' + str(ncell) + '-10-1-2008-9-30-2012.txt')        

for nexfile in nfiles:
    print str(nexfile)      
    infile = open(nexfile,'r')
    nxmiss = 0
    for nline in infile:
        if nline[:3] == '  2' or nline[:3] == '  1': #ignores header
            ndata = nline.split()
            yr = int(ndata[0])
            mn = int(ndata[1])
            dy = int(ndata[2])
            # nexrad data from Julien is in hours (1-24) for each day
            hr = int(ndata[3]) - 1
            # datetime module needs hours to be 0-23 
            nex_date = datetime.datetime(yr,mn,dy,hr)
            if nex_date >= start and nex_date <= finish:
                prec_nx = float(ndata[4])
                if float(prec_nx) < 0 or float(prec_nx) > 15: # replace erroneous values with 'na'
                    prec_nx = 'na'
                    nxmiss += 1
                else:
                    date_list[str(nex_date)].append(prec_nx)
    infile.close()

############# OPTION: write temperature and NEXRAD precip to .csv file #####################    
if csv_out == 'yes':
    print 'Writing data to .csv file...'
    fnew = open(maindir + '\\data\\all_nexrad_cells\\temp_nexrad_' + str(ystart) + '_' + str(yend) + '.csv','w')
    fnew.write('Date,' + 'ANL_Temperature(F),')
    cnt = 0
    for cell in cor_nexcell:
        cnt += 1
        if cnt != len(cor_nexcell):
            fnew.write(cell + ',')
        else:
            fnew.write(cell + '\n')
    for timestep in sorted(date_list):
        cnt_len = 0
        fnew.write(str(timestep) + ',')
        for each in date_list[timestep]:
            cnt_len += 1
            if cnt_len != len(date_list[timestep]):
                fnew.write(str(each) + ',')
            else:
                fnew.write(str(each) + '\n')
    fnew.close()

############## OPTION: PLOT histogram of mean NEXRAD in temperature ranges ################
if mean_hist == 'yes':
    print 'Creating Plot: MPE vs Temperature histogram...'
    min_temp = start_temp = 10.0
    max_temp = 90.0 
    temp_interval = 2.0 
    cat_num = (max_temp - min_temp)/temp_interval
    ############ Create temperature range categories ##############
    categories = {}; statcat = []
    cat_cnt = 1
    while min_temp < max_temp:
        categories['cat'+str(cat_cnt)] = [min_temp,(min_temp + temp_interval)-0.1]
        ###### create list of categories for statistics info #######
        if min_temp >= tmin and min_temp < tmax:
            statcat.append('cat'+str(cat_cnt))
        cat_cnt +=1
        min_temp += temp_interval

    # create dictionary with categorized precip and temp data     
    all_prec = {}; all_temp = {}
    for timestep in sorted(date_list):
        if len(date_list[timestep]) >= len(cor_nexcell):
            ############## analyze temperature data into bins
            temp = date_list[timestep][0]
            for key in categories:
                if temp >= categories[key][0] and temp <= categories[key][1]:
                    key_in = key
                    if key_in in all_prec:
                        all_temp[key_in].append(temp)
                    else:
                        all_temp[key_in] = [temp]
                    break
            ############## analyze precip data into bins
            for every in date_list[timestep][1:]: # only look at the precip data -> starts at index 1
                #mean_precip = numpy.mean(date_list[timestep][1:])
                if every != 'na':
                    if type_plot == 'Mean Intensity' or type_plot == 'Hours Precip':
                        if every > 0.0: # only examine precip values of 0.01 or greater
                            for key in categories:
                                if temp >= categories[key][0] and temp <= categories[key][1]:
                                    key_in = key
                                    if key_in in all_prec:
                                        all_prec[key_in].append(every)
                                    else:
                                        all_prec[key_in] = [every]
                                    break
                    else:
                         if every >= 0.0:
                            for key in categories:
                                if temp >= categories[key][0] and temp <= categories[key][1]:
                                    key_in = key
                                    if key_in in all_prec:
                                        all_prec[key_in].append(every)
                                    else:
                                        all_prec[key_in] = [every]
                                    break   
                    
    fig = plt.figure(figsize=(9, 4))
    ax1 = fig.add_subplot(111)
    width = 0.5
    if type_plot2 == 'Temperature Frequency':
        ax2 = ax1.twinx()
        ax2.set_ylim([0, 4000])
    for cats in categories:
        if cats in all_prec:
            if len(cats) == 4:
                loc = int(cats[-1:])-1
            elif len(cats) == 5:
                loc = int(cats[-2:])-1
            if type_plot == 'Mean Intensity': # only precip hours
                ax1.bar(loc+(width/2.0), numpy.mean(all_prec[cats]), width, color = 'green')
                if loc < 1:
                    ax1.bar(loc+(width/2.0), numpy.mean(all_prec[cats]), width, color = 'green', label = 'NEXRAD-MPE Spatial Average (50 cells)')
            if type_plot == 'Mean': # all hours included (0's)
                ax1.bar(loc+(width/2.0), numpy.mean(all_prec[cats]), width, color = 'green')
                if loc< 1:
                    ax1.bar(loc+(width/2.0), numpy.mean(all_prec[cats]), width, color = 'green', label = 'NEXRAD-MPE Spatial Average (50 cells)')
            if type_plot == 'Hours Precip': # only precip hours
                ax1.bar(loc+(width/2.0), len(all_prec[cats]), width, color = 'green')
                if loc< 1:
                    ax1.bar(loc+(width/2.0), len(all_prec[cats]), width, color = 'green', label = 'NEXRAD-MPE Spatial Average (50 cells)')
            if type_plot == 'Mean Cell':
                ax1.bar(loc+(width/2.0), sum(all_prec[cats])/len(cor_nexcell), width, color = 'green')
                if loc < 1: # only add 1 feature to legend
                    ax1.bar(loc+(width/2.0), sum(all_prec[cats])/len(cor_nexcell), width, color = 'green', label = 'NEXRAD-MPE')
            if type_plot == 'Total':
                ax1.bar(loc+(width/2.0), sum(all_prec[cats]), width, color = 'green')
            if type_plot == 'Temperature Frequency':
                ax1.bar(loc+(width/2.0), len(all_temp[cats]), width, color = 'red')
            if type_plot2 == 'Temperature Frequency':
                ax2.plot(loc+(width), len(all_temp[cats]), ls='', mfc='red', mec = 'k', marker = 'o')
                if loc < 1: # only add 1 feature to legend
                    ax2.plot(loc+(width), len(all_temp[cats]), ls='', mfc='red', mec = 'k', marker = 'o', label = 'Temperature')
       
    ax1.set_xlim([0+(width/2),len(categories)-(width/2)]) # remove white space at end of bar plot
    if type_plot == 'Temperature Frequency':
        ax1.set_ylabel('Number of Hourly Observations')
        ax1.set_title('Temperature Frequency\n'  + str(start.month) + '/' + str(start.day) + '/' + str(start.year) + ' - ' + str(finish.month) + '/' + str(finish.day) + '/' + str(finish.year))
    elif type_plot == 'Mean Cell':
        ax1.set_ylabel('Accumulated Precipitation Depth (inches)')
        ax1.set_title('Mean NEXRAD-MPE\n'  + str(start.month) + '/' + str(start.day) + '/' + str(start.year) + ' - ' + str(finish.month) + '/' + str(finish.day) + '/' + str(finish.year))
    elif type_plot == 'Mean Intensity':
        ax1.set_ylabel('Precipitation Intensity (in/hr)')
        ax1.set_title('Spatial Mean Hourly NEXRAD-MPE Average Intensity\n'  + 'During Hours with Precipitation: ' + str(start.month) + '/' + str(start.day) + '/' + str(start.year) + ' - ' + str(finish.month) + '/' + str(finish.day) + '/' + str(finish.year))
    elif type_plot == 'Mean':
        ax1.set_ylabel('Precipitation Intensity (in/hr)')
        ax1.set_title('Spatial Mean Hourly NEXRAD-MPE Average Intensity\n'  + 'During All Hours: ' + str(start.month) + '/' + str(start.day) + '/' + str(start.year) + ' - ' + str(finish.month) + '/' + str(finish.day) + '/' + str(finish.year))
    elif type_plot == 'Hours Precip':
        ax1.set_ylabel('Hours with Precipitation (50 NEXRAD-MPE cells)')
        ax1.set_title('Hours with Precipitation within Temperature Bins\n'  + 'During All Hours: ' + str(start.month) + '/' + str(start.day) + '/' + str(start.year) + ' - ' + str(finish.month) + '/' + str(finish.day) + '/' + str(finish.year))

    
    if type_plot2 == 'Temperature Frequency':
        ax2.set_ylabel('Number of Hourly Temperature Observations')
        ax1.legend(loc='upper left',numpoints = 1, fontsize = 10)
        ax2.legend(loc='upper right',numpoints = 1, fontsize = 10)
        ax1.set_title('Spatial Mean Accumulated NEXRAD-MPE and Temperature Frequency\n'  + str(start.month) + '/' + str(start.day) + '/' + str(start.year) + ' - ' + str(finish.month) + '/' + str(finish.day) + '/' + str(finish.year))
        type_plot = 'mean_mpe_and_tfreq'
    if type_plot == 'Mean Intensity' or type_plot == 'Mean':
        ax1.legend(loc='upper left',numpoints = 1, fontsize = 10)

        
    ax1.set_xlabel('Argonne National Laboratory Temperature (' + r'$^o$F)')
    tick_num = numpy.arange(len(categories))
    ax1.set_xticks(tick_num+width)
    tick_labels = []
    for key in range(1,len(categories)+1):
        tick_labels.append(str(categories['cat'+str(key)][0]) + ' - ' + str(categories['cat'+str(key)][1]))
    if len(categories) > 10:
        ax1.set_xticklabels(tick_labels,rotation=90,fontsize=9.8)
    else:
        ax1.set_xticklabels(tick_labels,rotation=45,fontsize=9.8)
        
    plt.savefig(maindir + '\\figures\\final\\MPE_vs_temp\\' + type_plot + '_mpe_anl_temp' + '.png', dpi=150, bbox_inches='tight')
    
    ptotal = 0; ttotal = 0
    for all_hours in date_list:
        if len(date_list[all_hours][1:]) >= 1: # fist value in dict is temp (make sure len is greater than 1 to account for 1 temp value)
            ptotal += sum(date_list[all_hours][1:])/len(date_list[all_hours][1:]) # sum all precip (mean cell)
            ttotal += len(date_list[all_hours][1:]) # sum all hourly temperature data
    pcat = 0; tcat = 0
    for cat in statcat:
        pcat += sum(all_prec[cat])/len(cor_nexcell) # sum precip within temp range
        tcat += len(all_prec[cat]) # sum number of hours within temp range
    print 'Statistics for temp range: ' + str(tmin) + ' - ' + str(tmax)
    pstat = round((float(pcat)/ptotal) * 100,1)
    tstat = round((float(tcat)/ttotal) * 100,1)
    print 'Percent of Precip in range: ' + str(pstat)
    print 'Percent of Temperature in range: ' + str(tstat)

print 'Complete!'